# -*- coding: utf-8 -*-
"""Qoder SDK lifecycle, permissions, and streaming message projection."""

import asyncio
import os
from typing import Any
from uuid import uuid4

from . import optional_sdk
from ._base import NativeRuntime, approval
from ....types import ReplyFinishedReason


class QoderRuntime(NativeRuntime):
    """Use Qoder's native SDK without requiring an ACP adapter."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.sdk = optional_sdk("qoder")
        self.client: Any = None
        self.turn_ready = asyncio.Event()
        self.streamed: set[tuple[str | None, int]] = set()
        self.has_text = False

    async def connect(self, probe: bool = False) -> None:
        resume = self.session_id
        self.session_id = resume or str(uuid4())
        auth = (
            self.sdk.access_token_from_env()
            if os.environ.get("QODER_PERSONAL_ACCESS_TOKEN")
            else self.sdk.qodercli_auth()
        )
        # Inherit stderr: SDK stderr callbacks create a task-affine AnyIO
        # scope, incompatible with cleanup in our independently owned task.
        options = self.sdk.QoderAgentOptions(
            auth=auth,
            cli_path=self.command,
            cwd=self.cwd,
            resume=resume,
            session_id=None if resume else self.session_id,
            include_partial_messages=True,
            permission_mode="default",
            can_use_tool=self._permission,
            setting_sources=["user", "project", "local"],
        )
        self.client = self.sdk.QoderSDKClient(options=options)
        await self.client.connect()

    async def _permission(
        self,
        tool_name: str,
        inputs: dict,
        context: Any,
    ) -> Any:
        if tool_name == "AskUserQuestion":
            return self.sdk.PermissionResultDeny(
                message="Interactive questions are not supported in this UI",
            )
        choice = await self.choose(
            approval(context.tool_use_id, tool_name, inputs),
            context.signal,
        )
        if choice == "allow":
            return self.sdk.PermissionResultAllow(updated_input=inputs)
        return self.sdk.PermissionResultDeny(
            message="The user declined or cancelled this operation",
            interrupt=self.cancelled.is_set(),
        )

    async def _text(self, kind: str, text: str) -> None:
        if text:
            if kind == "text":
                self.has_text = True
            await self.on_update({"kind": kind, "text": text})

    async def _tool(self, tool_id: str, **fields: Any) -> None:
        await self.on_update(
            {
                "kind": "tool",
                "tool": {"tool_call_id": tool_id, **fields},
            },
        )

    async def _prompt(self, text: str) -> ReplyFinishedReason:
        await self.client.query(text, session_id=self.session_id)
        self.turn_ready.set()
        async for message in self.client.receive_response():
            if isinstance(message, self.sdk.ResultMessage):
                if message.session_id != self.session_id:
                    raise RuntimeError("Qoder returned a different session")
                self.completed = True
                if self.cancelled.is_set() or message.stop_reason in {
                    "interrupted",
                    "cancelled",
                }:
                    return ReplyFinishedReason.INTERRUPTED
                if message.subtype == "error_max_turns":
                    return ReplyFinishedReason.EXCEED_MAX_ITERS
                if message.is_error:
                    raise RuntimeError(
                        "; ".join(message.errors or [])
                        or message.result
                        or message.subtype,
                    )
                if not self.has_text:
                    await self._text("text", message.result or "")
                return ReplyFinishedReason.COMPLETED
            await self._project(message)
        raise RuntimeError("Qoder disconnected before finishing the turn")

    async def _project(self, message: Any) -> None:
        sdk = self.sdk
        parent = getattr(message, "parent_tool_use_id", None)
        if isinstance(message, sdk.StreamEvent):
            event = message.event
            if event["type"] == "message_start":
                self.streamed = {
                    key for key in self.streamed if key[0] != parent
                }
            elif event["type"] == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") in {"text_delta", "thinking_delta"}:
                    self.streamed.add((parent, event["index"]))
                    thinking = delta["type"] == "thinking_delta"
                    await self._text(
                        "thought" if thinking else "text",
                        delta.get("thinking" if thinking else "text", ""),
                    )
            elif event["type"] == "content_block_start":
                block = event["content_block"]
                if block["type"] in {"text", "thinking"}:
                    thinking = block["type"] == "thinking"
                    text = block.get("thinking" if thinking else "text", "")
                    if text:
                        self.streamed.add((parent, event["index"]))
                        await self._text(
                            "thought" if thinking else "text",
                            text,
                        )
                elif block["type"] == "tool_use":
                    await self._tool(
                        block["id"],
                        title=block["name"],
                        raw_input=block.get("input", {}),
                        status="in_progress",
                    )
        elif isinstance(message, sdk.AssistantMessage):
            if message.error:
                raise RuntimeError(f"Qoder: {message.error}")
            for index, block in enumerate(message.content):
                if isinstance(block, sdk.ToolUseBlock):
                    await self._tool(
                        block.id,
                        title=block.name,
                        raw_input=block.input,
                        status="in_progress",
                    )
                    if block.name == "TodoWrite":
                        await self.on_update(
                            {
                                "kind": "plan",
                                "plan": [
                                    {
                                        "content": todo["content"],
                                        "status": todo["status"],
                                    }
                                    for todo in block.input.get("todos", [])
                                ],
                            },
                        )
                elif (parent, index) not in self.streamed:
                    if isinstance(block, sdk.TextBlock):
                        await self._text("text", block.text)
                    elif isinstance(block, sdk.ThinkingBlock):
                        await self._text("thought", block.thinking)
            self.streamed = {key for key in self.streamed if key[0] != parent}
        elif isinstance(message, sdk.UserMessage):
            if isinstance(message.content, list):
                for block in message.content:
                    if isinstance(block, sdk.ToolResultBlock):
                        await self._tool(
                            block.tool_use_id,
                            raw_output=block.content,
                            status="failed" if block.is_error else "completed",
                        )
        elif isinstance(message, sdk.ToolProgressMessage):
            await self._tool(
                message.tool_use_id,
                title=message.tool_name,
                status="in_progress",
                raw_output=f"Running for {message.elapsed_time_seconds:g}s",
            )
        elif isinstance(message, sdk.SDKPermissionDeniedMessage):
            await self._tool(
                message.tool_use_id,
                title=message.tool_name,
                status="failed",
                raw_output=message.message,
            )
        elif isinstance(message, sdk.SystemMessage):
            if message.subtype == "local_command_output":
                await self._text("text", message.data.get("content", ""))

    async def interrupt(self) -> None:
        await self.turn_ready.wait()
        await self.client.interrupt()

    async def aclose(self) -> None:
        self.cancelled.set()
        if self.client is not None:
            await self.client.disconnect()
