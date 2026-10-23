# -*- coding: utf-8 -*-
"""Application integration for native Codex and Qoder agents."""

import asyncio
import hashlib
import json
from typing import Any

from fastapi import HTTPException

from ._external_runtime import create_runtime, resolve_command
from ._external_runtime._base import finish_cleanup
from .._bus_ops import publish_session_event
from ..message_bus import MessageBus, MessageBusKeys
from ..storage import AgentRecord, SessionRecord, StorageBase
from ..storage._model._agent import ExternalAgentConfig
from ...event import (
    CustomEvent,
    ReplyEndEvent,
    ReplyStartEvent,
    TextBlockDeltaEvent,
    TextBlockEndEvent,
    TextBlockStartEvent,
    ThinkingBlockDeltaEvent,
    ThinkingBlockEndEvent,
    ThinkingBlockStartEvent,
)
from ...message import AssistantMsg, Msg
from ...types import ErrorInfo, ReplyFinishedReason
from ..._utils._common import _generate_id


def runtime_command(
    provider: str,
    config: ExternalAgentConfig,
    cwd: str = ".",
) -> tuple[str, str]:
    """Resolve the chosen native runtime and its working directory."""
    return resolve_command(provider, config.executable, config.cwd or cwd)


def _error_message(error: Exception) -> str:
    """Keep the remote diagnostic accompanying a generic JSON-RPC error."""
    message = str(error) or type(error).__name__
    data = getattr(error, "data", None)
    if isinstance(data, dict) and isinstance(data.get("details"), str):
        return f"{message}: {data['details']}"
    return message


async def check_runtime(provider: str, config: ExternalAgentConfig) -> dict:
    """Initialize the native protocol without submitting a model request."""

    async def ignore(_update: dict) -> None:
        return None

    try:
        command, cwd = runtime_command(provider, config)
        client = create_runtime(
            provider,
            command=command,
            cwd=cwd,
            session_id=None,
            on_update=ignore,
            on_permission=ignore,
        )
        original: BaseException | None = None
        try:
            async with asyncio.timeout(30):
                await client.connect(probe=True)
            return {
                "ready": True,
                "executable": command,
                "cwd": cwd,
                "error": None,
            }
        except BaseException as exc:
            original = exc
            raise
        finally:
            await finish_cleanup(
                asyncio.create_task(client.aclose()),
                original,
            )
    except TimeoutError:
        return {
            "ready": False,
            "error": f"{provider} initialization timed out. Check the CLI "
            f"login, network connection, and runtime configuration.",
        }
    except Exception as exc:
        return {"ready": False, "error": _error_message(exc)}


def _permission_key(session_id: str, request_id: str) -> tuple[str, str]:
    return (
        MessageBusKeys.projection_namespace(session_id),
        MessageBusKeys.projection_field("external_permission", request_id),
    )


async def pending_permissions(bus: MessageBus, session_id: str) -> list[dict]:
    """Return live approvals, including after a browser refresh."""
    if not await bus.is_locked(MessageBusKeys.session_lock(session_id)):
        return []
    entries = await bus.registry_getall(
        MessageBusKeys.projection_namespace(session_id),
    )
    pending = []
    for key, value in entries.items():
        if key.startswith("external_permission:"):
            entry = json.loads(value)
            if "choice" not in entry:
                pending.append(entry)
    return pending


async def resolve_permission(
    bus: MessageBus,
    session_id: str,
    request_id: str,
    option_id: str | None,
) -> None:
    """Validate an exact remote option and deliver it across HTTP workers."""
    namespace, field = _permission_key(session_id, request_id)
    async with bus.acquire_lock(f"{namespace}:{field}:lock", ttl_secs=30):
        raw = await bus.registry_get(namespace, field)
        if raw is None or not await bus.is_locked(
            MessageBusKeys.session_lock(session_id),
        ):
            raise HTTPException(409, "This permission request has expired")
        request = json.loads(raw)
        if "choice" in request:
            raise HTTPException(409, "This permission was already answered")
        if option_id is not None and option_id not in {
            item["option_id"] for item in request["options"]
        }:
            raise HTTPException(422, "Unknown permission option")
        request["choice"] = option_id
        await bus.registry_set(namespace, field, json.dumps(request))


class ExternalChatRun:
    """One turn under ChatService's distributed session lock.

    Each turn starts a process and restores persistent remote history. No
    worker owns a resident process between turns; approval responses are
    carried through the shared bus while the turn is active.
    """

    def __init__(
        self,
        storage: StorageBase,
        bus: MessageBus,
        agent: AgentRecord,
        session: SessionRecord,
    ) -> None:
        self.storage = storage
        self.bus = bus
        self.agent = agent
        self.session = session
        self.reply = AssistantMsg(name=agent.data.name, content=[])
        self.cursor: str | None = None
        self.blocks: dict[str, str] = {}
        self.accept_updates = False
        self.client: Any = None
        self.remote_state: dict | None = None

    async def emit(self, event: Any) -> None:
        """Apply before publishing so cancellation cannot lose the event."""
        if not isinstance(event, CustomEvent):
            self.reply.append_event(event)
        self.cursor = await publish_session_event(
            self.bus,
            self.session.id,
            event.model_dump(mode="json"),
        )

    async def update(self, update: dict) -> None:
        """Map text deltas and preserve tool replacement snapshots."""
        if not self.accept_updates:
            return  # session/load may replay the previous conversation.
        kind = update["kind"]
        if kind in ("text", "thought"):
            thinking = kind == "thought"
            if kind not in self.blocks:
                self.blocks[kind] = _generate_id()
                start = (
                    ThinkingBlockStartEvent
                    if thinking
                    else TextBlockStartEvent
                )
                await self.emit(
                    start(
                        reply_id=self.reply.id,
                        block_id=self.blocks[kind],
                    ),
                )
            delta = (
                ThinkingBlockDeltaEvent if thinking else TextBlockDeltaEvent
            )
            await self.emit(
                delta(
                    reply_id=self.reply.id,
                    block_id=self.blocks[kind],
                    delta=update["text"],
                ),
            )
        elif kind == "tool":
            snapshot = update["tool"]
            tool_id = snapshot["tool_call_id"]
            tools = self.reply.metadata.setdefault("external_tools", {})
            previous = tools.get(tool_id, {})
            tools[tool_id] = {**previous, **snapshot}
            await self.emit(
                CustomEvent(
                    name="external_tool",
                    value={
                        "reply_id": self.reply.id,
                        "tool": tools[tool_id],
                    },
                ),
            )
        elif kind == "plan":
            plan = update["plan"]
            self.reply.metadata["external_plan"] = plan
            await self.emit(
                CustomEvent(
                    name="external_plan",
                    value={
                        "reply_id": self.reply.id,
                        "plan": plan,
                    },
                ),
            )

    async def permission(self, request: dict) -> str | None:
        """Wait for a user choice while the native turn remains active."""
        request_id = _generate_id()
        namespace, field = _permission_key(self.session.id, request_id)
        payload = {
            "request_id": request_id,
            "reply_id": self.reply.id,
            **request,
        }
        await self.bus.registry_set(namespace, field, json.dumps(payload))
        try:
            while True:
                raw = await self.bus.registry_get(namespace, field)
                if raw is None:
                    return None
                entry = json.loads(raw)
                if "choice" in entry:
                    return entry["choice"]
                await asyncio.sleep(0.1)
        finally:
            await self.bus.registry_del(namespace, field)

    async def prepare(self, inputs: Any, workdir: str) -> tuple[str, str]:
        """Validate user input and bind a resumable remote conversation."""
        messages = inputs if isinstance(inputs, list) else [inputs]
        if not messages or any(
            not isinstance(msg, Msg)
            or msg.role != "user"
            or any(block.type != "text" for block in msg.content)
            for msg in messages
        ):
            raise ValueError(
                "Third-party chat currently accepts user text only",
            )
        for msg in messages:
            await self.storage.upsert_message(
                self.session.user_id,
                self.session.id,
                msg,
            )
        assert self.agent.data.external_config is not None
        command, cwd = runtime_command(
            self.agent.data.backend,
            self.agent.data.external_config,
            cwd=workdir,
        )
        binding = hashlib.sha256(
            json.dumps(
                [
                    self.agent.data.backend,
                    command,
                    "native-v1",
                    cwd,
                ],
            ).encode(),
        ).hexdigest()
        remote = self.session.external_state
        if remote and (remote.binding != binding or remote.in_flight):
            raise ValueError(
                "The runtime changed or the previous turn did not finish. "
                "Start a new conversation to avoid replaying tool actions.",
            )
        self.client = create_runtime(
            self.agent.data.backend,
            command=command,
            cwd=cwd,
            session_id=remote.session_id if remote else None,
            on_update=self.update,
            on_permission=self.permission,
        )
        return binding, "\n".join(
            block.text for msg in messages for block in msg.content
        )

    async def run(
        self,
        inputs: Any,
        *,
        workdir: str | None,
    ) -> None:
        """Submit one turn and persist both setup and execution failures."""
        reason = ReplyFinishedReason.COMPLETED
        error = None
        try:
            await self.emit(
                ReplyStartEvent(
                    session_id=self.session.id,
                    reply_id=self.reply.id,
                    name=self.agent.data.name,
                ),
            )
            if workdir is None:
                raise ValueError(
                    "Third-party agents require a local workspace",
                )
            if self.session.team_id or self.session.origin.type != "user":
                raise ValueError("Third-party agents support direct chat only")
            binding, text = await self.prepare(inputs, workdir)
            async with self.client:
                self.remote_state = {
                    "session_id": self.client.session_id,
                    "binding": binding,
                    "in_flight": True,
                }
                await self.save_remote_state()
                self.accept_updates = True
                reason = await self.client.prompt(text)
        except asyncio.CancelledError:
            reason = ReplyFinishedReason.INTERRUPTED
        except Exception as exc:
            reason = ReplyFinishedReason.ERROR
            error = ErrorInfo(message=_error_message(exc))
        finally:
            cleanup = asyncio.create_task(self.finish(reason, error))
            while not cleanup.done():
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    pass
            cleanup.result()

    async def save_remote_state(self) -> None:
        """Record identity independently of user-editable settings."""
        assert self.remote_state is not None
        await self.storage.update_session_external_state(
            self.session.user_id,
            self.agent.id,
            self.session.id,
            self.remote_state,
        )

    async def finish(
        self,
        reason: ReplyFinishedReason,
        error: ErrorInfo | None,
    ) -> None:
        """Close blocks and checkpoint the reply under the run lock."""
        for kind, block_id in self.blocks.items():
            end = (
                ThinkingBlockEndEvent
                if kind == "thought"
                else TextBlockEndEvent
            )
            await self.emit(end(reply_id=self.reply.id, block_id=block_id))
        for tool in self.reply.metadata.get("external_tools", {}).values():
            if tool.get("status") in (None, "pending", "in_progress"):
                tool["status"] = "failed"
                await self.emit(
                    CustomEvent(
                        name="external_tool",
                        value={"reply_id": self.reply.id, "tool": tool},
                    ),
                )
        if self.remote_state is not None:
            self.remote_state["in_flight"] = not self.client.completed
            await self.save_remote_state()
        await self.emit(
            ReplyEndEvent(
                session_id=self.session.id,
                reply_id=self.reply.id,
                finished_reason=reason,
                error=error,
            ),
        )
        async with self.bus.acquire_lock(
            MessageBusKeys.session_event_checkpoint_lock(self.session.id),
            ttl_secs=MessageBusKeys.SESSION_EVENT_CHECKPOINT_LOCK_TTL_SECS,
        ):
            await self.storage.upsert_message(
                self.session.user_id,
                self.session.id,
                self.reply,
            )
            if self.cursor:
                await self.bus.registry_set(
                    MessageBusKeys.session_event_checkpoint(self.session.id),
                    MessageBusKeys.SESSION_EVENT_CURSOR_FIELD,
                    self.cursor,
                )
