# -*- coding: utf-8 -*-
"""Native protocol probes without vendor credentials or model requests."""

import asyncio
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator
from unittest import IsolatedAsyncioTestCase, skipUnless
from unittest.mock import AsyncMock, patch

from agentscope.app._service._external_runtime import resolve_command
from agentscope.app._service._external_runtime._codex import CodexRuntime
from agentscope.app._service._external_runtime._qoder import QoderRuntime
from agentscope.types import ReplyFinishedReason


class CodexProtocolTest(IsolatedAsyncioTestCase):
    """Exercise actual pipes, concurrent requests, and process cleanup."""

    async def asyncSetUp(self) -> None:
        # unittest owns the directory until all asynchronous tasks finish.
        # pylint: disable-next=consider-using-with
        self.directory = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(
            patch.dict(
                os.environ,
                {
                    "NATIVE_TEST_STATE": str(Path(self.directory) / "history"),
                    "NATIVE_TEST_MODE": "",
                },
            ),
        )
        self.updates = AsyncMock()
        self.permissions = AsyncMock(return_value="allow")

    def runtime(self, session_id: str | None = None) -> CodexRuntime:
        """Run this module's protocol peer in a real child process."""
        runtime = CodexRuntime(
            command=sys.executable,
            cwd=self.directory,
            session_id=session_id,
            on_update=self.updates,
            on_permission=self.permissions,
        )
        runtime.arguments = [str(Path(__file__).resolve()), "--serve"]
        return runtime

    async def test_turn_resume_and_process_cleanup(self) -> None:
        """Persist provider history across independently owned processes."""
        async with self.runtime() as first:
            self.assertEqual(
                await first.prompt("hello"),
                ReplyFinishedReason.COMPLETED,
            )
        self.assertEqual(first.process.returncode, 0)
        async with self.runtime(first.session_id) as second:
            await second.prompt("again")
        self.assertEqual(
            [call.args[0] for call in self.updates.await_args_list],
            [
                {"kind": "text", "text": "1:hello"},
                {"kind": "text", "text": "2:again"},
            ],
        )
        self.assertEqual(second.process.returncode, 0)
        self.assertTrue(first.reader.done() and second.reader.done())

    async def test_approval_does_not_block_cancel_or_rpc(self) -> None:
        """Cancel twice while a UI approval is waiting, then resume."""
        waiting = asyncio.Event()

        async def permission(_request: dict) -> None:
            waiting.set()
            await asyncio.Event().wait()

        self.permissions.side_effect = permission
        async with self.runtime() as runtime:
            turn = asyncio.create_task(runtime.prompt("permission"))
            await asyncio.wait_for(waiting.wait(), 5)
            self.assertEqual(await runtime.rpc("ping", {}), {})
            turn.cancel()
            await asyncio.sleep(0)
            turn.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(turn, 5)
            self.assertTrue(runtime.completed)
        self.assertEqual(runtime.requests, {})
        self.assertEqual(runtime.process.returncode, 0)

    async def test_failed_and_disconnected_turns_differ(self) -> None:
        """A definitive failure is resumable; a transport loss is uncertain."""
        for text, completed in (("failure", True), ("crash", False)):
            with self.subTest(text=text):
                async with self.runtime() as runtime:
                    with self.assertRaises(RuntimeError):
                        await runtime.prompt(text)
                    self.assertEqual(runtime.completed, completed)

    async def test_unsupported_request_is_rejected(self) -> None:
        """Unknown interactive requests never receive synthetic approval."""
        async with self.runtime() as runtime:
            await runtime.prompt("unsupported")
        self.permissions.assert_not_awaited()
        self.assertEqual(
            self.updates.await_args.args[0],
            {
                "kind": "text",
                "text": "-32601",
            },
        )

    async def test_missing_dependency_and_explicit_executable(self) -> None:
        """Explicit Codex works without SDK; absent bundles explain extras."""
        self.assertEqual(
            resolve_command(
                "codex",
                sys.executable,
                self.directory,
            ),
            (
                str(Path(sys.executable).resolve()),
                str(Path(self.directory).resolve()),
            ),
        )
        with patch(
            "agentscope.app._service._external_runtime.optional_sdk",
            side_effect=ValueError("missing"),
        ), patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(ValueError, r"agentscope\[codex\]"):
                resolve_command("codex", "", self.directory)
            with self.assertRaisesRegex(ValueError, r"agentscope\[qoder\]"):
                resolve_command("qoder", "", self.directory)

    async def test_qoder_cli_discovery_does_not_require_sdk(self) -> None:
        """Explicit/PATH CLIs work for inspection; chat still needs the SDK."""
        expected = (
            str(Path(sys.executable).resolve()),
            str(Path(self.directory).resolve()),
        )
        with patch(
            "agentscope.app._service._external_runtime.optional_sdk",
            side_effect=ValueError("SDK missing"),
        ) as sdk:
            self.assertEqual(
                resolve_command("qoder", sys.executable, self.directory),
                expected,
            )
            sdk.assert_not_called()
            with patch("shutil.which", return_value=sys.executable):
                self.assertEqual(
                    resolve_command("qoder", "", self.directory),
                    expected,
                )
        with patch(
            "agentscope.app._service._external_runtime._qoder.optional_sdk",
            side_effect=ValueError("SDK missing"),
        ):
            with self.assertRaisesRegex(ValueError, "SDK missing"):
                QoderRuntime(
                    command=sys.executable,
                    cwd=self.directory,
                    session_id=None,
                    on_update=self.updates,
                    on_permission=self.permissions,
                )

    async def test_approval_scope_and_offered_decisions(self) -> None:
        """Foreign turns are rejected; unavailable allow is never offered."""
        # pylint: disable=protected-access
        runtime = self.runtime("thread")
        runtime.turn_id = "turn"
        runtime._send = AsyncMock()  # pylint: disable=protected-access
        request: dict = {
            "id": "approval",
            "method": "item/commandExecution/requestApproval",
            "params": {
                "threadId": "thread",
                "turnId": "foreign",
                "itemId": "tool",
                "availableDecisions": ["decline"],
            },
        }
        await runtime._respond(request)  # pylint: disable=protected-access
        self.permissions.assert_not_awaited()
        self.assertEqual(
            runtime._send.await_args.args[0],
            {  # pylint: disable=protected-access
                "id": "approval",
                "error": {
                    "code": -32601,
                    "message": "Unsupported client request",
                },
            },
        )
        request["params"]["turnId"] = "turn"
        self.permissions.return_value = "deny"
        await runtime._respond(request)  # pylint: disable=protected-access
        self.assertEqual(
            self.permissions.await_args.args[0]["options"],
            [
                {"option_id": "deny", "name": "Reject", "kind": "reject_once"},
            ],
        )
        self.assertEqual(
            runtime._send.await_args.args[0],
            {  # pylint: disable=protected-access
                "id": "approval",
                "result": {"decision": "decline"},
            },
        )

    async def test_login_failure_closes_process(self) -> None:
        """A failed context entry still releases its reader and child."""
        with patch.dict(os.environ, {"NATIVE_TEST_MODE": "login"}):
            runtime = self.runtime()
            with self.assertRaisesRegex(ValueError, "not authenticated"):
                async with runtime:
                    self.fail("Unauthenticated runtime should not connect")
        self.assertEqual(runtime.process.returncode, 0)
        self.assertTrue(runtime.reader.done())


class QoderTransport:
    """Exercise the real SDK parser and control protocol through its API."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue = asyncio.Queue()
        self.writes: list[dict] = []
        self.closed = False
        self.session_id = ""
        self.mode = "stream"

    async def connect(self) -> None:
        """No subprocess is needed for SDK contract tests."""

    def is_ready(self) -> bool:
        """Report transport readiness to the SDK."""
        return not self.closed

    async def end_input(self) -> None:
        """The bidirectional client keeps its input open until close."""

    def result(self, **fields: Any) -> dict:
        """Construct a real SDK terminal message."""
        return {
            "type": "result",
            "subtype": "success",
            "duration_ms": 1,
            "duration_api_ms": 1,
            "is_error": False,
            "num_turns": 1,
            "session_id": self.session_id,
            **fields,
        }

    async def write(self, data: str) -> None:
        """Answer initialization, permissions, prompts, and interruptions."""
        message = json.loads(data)
        self.writes.append(message)
        if message["type"] == "control_request":
            await self.queue.put(
                {
                    "type": "control_response",
                    "response": {
                        "subtype": "success",
                        "request_id": message["request_id"],
                        "response": {},
                    },
                },
            )
            if message["request"].get("subtype") == "interrupt":
                await self.queue.put(self.result(stop_reason="interrupted"))
        elif message["type"] == "user":
            self.session_id = message["session_id"]
            if self.mode == "permission":
                await self.queue.put(
                    {
                        "type": "control_request",
                        "request_id": "approval",
                        "request": {
                            "subtype": "can_use_tool",
                            "tool_name": "Bash",
                            "input": {"command": "pwd"},
                            "tool_use_id": "tool-1",
                        },
                    },
                )
            elif self.mode == "error":
                await self.queue.put(
                    self.result(
                        is_error=True,
                        subtype="error_during_execution",
                        errors=["Authentication required"],
                    ),
                )
            else:
                for event in [
                    {"type": "message_start"},
                    {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": "first"},
                    },
                ]:
                    await self.queue.put(
                        {
                            "type": "stream_event",
                            "uuid": "event",
                            "session_id": self.session_id,
                            "event": event,
                        },
                    )
                for text in ["first", "second"]:
                    await self.queue.put(
                        {
                            "type": "assistant",
                            "message": {
                                "model": "test",
                                "content": [
                                    {"type": "text", "text": text},
                                ],
                            },
                        },
                    )
                await self.queue.put(self.result(result="second"))
        elif message["type"] == "control_response":
            await self.queue.put(self.result())

    async def read_messages(self) -> AsyncIterator[dict]:
        """Yield raw protocol messages for SDK parsing."""
        while True:
            message = await self.queue.get()
            if message is None:
                return
            yield message

    async def close(self) -> None:
        """Unblock SDK readers on cleanup."""
        self.closed = True
        await self.queue.put(None)


@skipUnless(importlib.util.find_spec("qoder_agent_sdk"), "Install [qoder]")
class QoderSDKTest(IsolatedAsyncioTestCase):
    """Use actual SDK types, control requests, and message parsing."""

    async def asyncSetUp(self) -> None:
        self.updates = AsyncMock()
        self.permissions = AsyncMock(return_value="allow")
        self.runtime = QoderRuntime(
            command="qodercli",
            cwd=".",
            session_id="remote-session",
            on_update=self.updates,
            on_permission=self.permissions,
        )
        self.transport = QoderTransport()
        client_type = self.runtime.sdk.QoderSDKClient
        self.factory = self.enterContext(
            patch.object(
                self.runtime.sdk,
                "QoderSDKClient",
                side_effect=lambda **kwargs: client_type(
                    **kwargs,
                    transport=self.transport,
                ),
            ),
        )

    async def test_stream_deduplication_resets_per_message(self) -> None:
        """Streamed/full duplicates disappear; later full messages remain."""
        async with self.runtime:
            self.assertEqual(
                await self.runtime.prompt("hi"),
                ReplyFinishedReason.COMPLETED,
            )
        self.assertEqual(
            [call.args[0] for call in self.updates.await_args_list],
            [
                {"kind": "text", "text": "first"},
                {"kind": "text", "text": "second"},
            ],
        )
        options = self.factory.call_args.kwargs["options"]
        self.assertEqual(
            (options.resume, options.session_id, options.permission_mode),
            ("remote-session", None, "default"),
        )
        self.assertTrue(self.transport.closed)

    async def test_permission_result_uses_sdk_contract(self) -> None:
        """Allow and deny reach the real SDK control response encoder."""
        self.transport.mode = "permission"
        async with self.runtime:
            await self.runtime.prompt("permission")
        response = next(
            msg["response"]
            for msg in self.transport.writes
            if msg["type"] == "control_response"
        )
        self.assertEqual(
            response,
            {
                "subtype": "success",
                "request_id": "approval",
                "response": {
                    "behavior": "allow",
                    "updatedInput": {"command": "pwd"},
                    "toolUseID": "tool-1",
                },
            },
        )
        self.assertTrue(self.transport.closed)

    async def test_cancel_pending_permission(self) -> None:
        """Native interrupt cancels a pending browser approval."""
        self.transport.mode = "permission"
        waiting = asyncio.Event()

        async def permission(_request: dict) -> None:
            waiting.set()
            await asyncio.Event().wait()

        self.permissions.side_effect = permission
        async with self.runtime:
            turn = asyncio.create_task(self.runtime.prompt("permission"))
            await asyncio.wait_for(waiting.wait(), 5)
            turn.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(turn, 5)
        self.assertTrue(self.runtime.completed)
        self.assertTrue(self.transport.closed)

    async def test_provider_error_is_visible(self) -> None:
        """Definitive SDK errors retain their diagnostic and end the turn."""
        self.transport.mode = "error"
        async with self.runtime:
            with self.assertRaisesRegex(
                RuntimeError,
                "Authentication required",
            ):
                await self.runtime.prompt("hi")
        self.assertTrue(self.runtime.completed)
        self.assertTrue(self.transport.closed)

    async def test_new_session_and_denied_permission(self) -> None:
        """New UUIDs and per-operation denial follow SDK options/results."""
        self.runtime.session_id = None
        self.transport.mode = "permission"
        self.permissions.return_value = "deny"
        async with self.runtime:
            await self.runtime.prompt("permission")
        options = self.factory.call_args.kwargs["options"]
        self.assertEqual(
            (options.resume, options.session_id),
            (None, self.runtime.session_id),
        )
        response = next(
            msg["response"]
            for msg in self.transport.writes
            if msg["type"] == "control_response"
        )
        self.assertEqual(
            response,
            {
                "subtype": "success",
                "request_id": "approval",
                "response": {
                    "behavior": "deny",
                    "toolUseID": "tool-1",
                    "message": "The user declined or cancelled this operation",
                },
            },
        )

    async def test_tool_result_and_plan_projection(self) -> None:
        """Tools and plans survive as complete application snapshots."""
        # pylint: disable=protected-access
        sdk = self.runtime.sdk
        todos = [{"content": "Build", "status": "in_progress"}]
        await self.runtime._project(
            sdk.AssistantMessage(  # pylint: disable=protected-access
                model="test",
                content=[
                    sdk.ToolUseBlock(
                        id="todo",
                        name="TodoWrite",
                        input={"todos": todos},
                    ),
                ],
            ),
        )
        await self.runtime._project(
            sdk.UserMessage(
                content=[  # pylint: disable=protected-access
                    sdk.ToolResultBlock(tool_use_id="todo", content="done"),
                ],
            ),
        )
        self.assertEqual(
            [call.args[0] for call in self.updates.await_args_list],
            [
                {
                    "kind": "tool",
                    "tool": {
                        "tool_call_id": "todo",
                        "title": "TodoWrite",
                        "raw_input": {"todos": todos},
                        "status": "in_progress",
                    },
                },
                {"kind": "plan", "plan": todos},
                {
                    "kind": "tool",
                    "tool": {
                        "tool_call_id": "todo",
                        "raw_output": "done",
                        "status": "completed",
                    },
                },
            ],
        )


def serve_codex() -> None:
    """Speak app-server JSON lines as a separate test process."""
    history = Path(os.environ["NATIVE_TEST_STATE"])
    mode = os.environ.get("NATIVE_TEST_MODE", "")
    session_id = "thread-1"
    turn_id = "turn-1"
    pending = None

    def send(message: dict) -> None:
        print(json.dumps(message), flush=True)

    def event(method: str, **params: Any) -> None:
        send(
            {
                "method": method,
                "params": {
                    "threadId": session_id,
                    "turnId": turn_id,
                    **params,
                },
            },
        )

    def finish(status: str = "completed") -> None:
        event(
            "turn/completed",
            turn={
                "id": turn_id,
                "status": status,
                "error": {"message": "Provider failed"}
                if status == "failed"
                else None,
            },
        )

    for line in sys.stdin:
        message = json.loads(line)
        method = message.get("method")
        params = message.get("params", {})
        request_id = message.get("id")
        if method is None:
            if pending:
                text = (
                    json.dumps(message.get("result"))
                    if "result" in message
                    else str(message["error"]["code"])
                )
                event("item/agentMessage/delta", delta=text)
                pending = None
                finish()
            continue
        if request_id is None:
            continue
        if method == "initialize" and mode == "protocol_error":
            send(
                {
                    "id": request_id,
                    "error": {"message": "Unsupported protocol"},
                },
            )
            continue
        result: dict = {}
        if method == "account/read":
            result = {"requiresOpenaiAuth": mode == "login", "account": None}
        elif method in {"thread/start", "thread/resume"}:
            result = {"thread": {"id": session_id}}
        elif method == "turn/start":
            result = {"turn": {"id": turn_id}}
        send({"id": request_id, "result": result})
        if method == "turn/interrupt":
            pending = None
            finish("interrupted")
        elif method == "turn/start":
            count = (
                int(history.read_text(encoding="utf-8")) + 1
                if history.exists()
                else 1
            )
            history.write_text(str(count), encoding="utf-8")
            text = params["input"][0]["text"]
            if text == "crash":
                return
            if text in {"permission", "unsupported"}:
                event(
                    "item/started",
                    item={
                        "id": "call-1",
                        "type": "commandExecution",
                        "command": "Run command",
                    },
                )
                pending = True
                send(
                    {
                        "id": "request-1",
                        "method": "item/commandExecution/requestApproval"
                        if text == "permission"
                        else "item/tool/requestUserInput",
                        "params": {
                            "threadId": session_id,
                            "turnId": turn_id,
                            "itemId": "call-1",
                            "command": "Run command",
                        },
                    },
                )
                continue
            if text == "updates":
                event(
                    "item/started",
                    item={
                        "id": "call-1",
                        "type": "commandExecution",
                        "command": "Build",
                    },
                )
                event(
                    "item/completed",
                    item={
                        "id": "call-1",
                        "type": "commandExecution",
                        "command": "Build",
                        "status": "completed",
                        "aggregatedOutput": "done",
                    },
                )
                event("turn/plan/updated", plan=[])
            elif text == "snapshots":
                for delta in ["first", " plus last"]:
                    event(
                        "item/commandExecution/outputDelta",
                        itemId="snapshot",
                        delta=delta,
                    )
                event(
                    "item/completed",
                    item={
                        "id": "snapshot",
                        "type": "commandExecution",
                        "status": "completed",
                    },
                )
            event(
                "item/agentMessage/delta",
                delta=os.getcwd() if text == "cwd" else f"{count}:{text}",
            )
            finish("failed" if text == "failure" else "completed")


if __name__ == "__main__" and "--serve" in sys.argv:
    serve_codex()
