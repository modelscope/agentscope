# -*- coding: utf-8 -*-
"""ACP client tests, with a deterministic subprocess agent in this module."""

import asyncio
import json
import os
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

from acp import run_agent
from acp.schema import (
    AgentCapabilities,
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    CloseSessionResponse,
    HttpMcpServer,
    InitializeResponse,
    LoadSessionResponse,
    McpCapabilities,
    McpServerStdio,
    NewSessionResponse,
    PermissionOption,
    PromptResponse,
    ResourceContentBlock,
    SessionCapabilities,
    SseMcpServer,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    ToolCallUpdate,
)

from agentscope.acp import ACPClient

# Lifecycle assertions need the owned process, which is deliberately private.
# pylint: disable=protected-access,too-many-public-methods


class _StdioAgent:
    """Exercise the wire protocol without models or external services."""

    def __init__(self) -> None:
        self.connection = None
        self.cancelled = asyncio.Event()
        self.turn = 0
        self.mode = os.environ.get("ACP_TEST_MODE", "")

    def on_connect(self, connection: Any) -> None:
        """Record the SDK's reverse RPC connection."""
        self.connection = connection

    async def initialize(self, **kwargs: Any) -> InitializeResponse:
        """Negotiate capabilities or simulate a failed initialization."""
        if self.mode == "startup_hang":
            await asyncio.Event().wait()
        if self.mode == "stderr":
            sys.stderr.write("diagnostic\n" * 20000)
            sys.stderr.flush()
        capabilities = kwargs["client_capabilities"]
        assert not capabilities.terminal
        assert not capabilities.fs.read_text_file
        assert not capabilities.fs.write_text_file
        return InitializeResponse(
            protocol_version=99 if self.mode == "version" else 1,
            agent_capabilities=AgentCapabilities(
                load_session=self.mode == "resume",
                mcp_capabilities=McpCapabilities(
                    http=self.mode == "mcp",
                    sse=self.mode == "mcp",
                ),
                session_capabilities=SessionCapabilities.model_validate(
                    {"close": {}} if self.mode == "close" else {},
                ),
            ),
        )

    async def new_session(self, cwd: str, **kwargs: Any) -> NewSessionResponse:
        """Send an update before the session/new response."""
        assert cwd == str(Path.cwd())
        if self.mode == "new_error":
            raise ValueError("Login required for test agent")
        await self._text("ready")
        if self.mode == "mcp":
            await self._text(
                json.dumps(
                    [
                        item.model_dump(mode="json", exclude_none=True)
                        for item in kwargs["mcp_servers"]
                    ],
                ),
            )
        if self.mode == "idle":
            asyncio.create_task(self._idle_update())
        return NewSessionResponse(session_id="test-session")

    async def load_session(
        self,
        session_id: str,
        cwd: str,
        **_kwargs: Any,
    ) -> LoadSessionResponse:
        """Restore the turn counter and replay a historical notification."""
        assert session_id == "test-session"
        assert cwd == str(Path.cwd())
        self.turn = int(
            Path(os.environ["ACP_TEST_STATE"]).read_text(encoding="utf-8"),
        )
        await self._text("historical replay")
        return LoadSessionResponse()

    async def _idle_update(self) -> None:
        await asyncio.sleep(0.1)
        await self._text("idle")

    async def _text(self, text: str) -> None:
        await self.connection.session_update(
            session_id="test-session",
            update=AgentMessageChunk(
                session_update="agent_message_chunk",
                content=TextContentBlock(type="text", text=text),
            ),
        )

    async def prompt(
        self,
        prompt: list[Any],
        session_id: str,
        **_kwargs: Any,
    ) -> PromptResponse:
        """Produce updates, request permission, wait, or crash on demand."""
        assert session_id == "test-session"
        self.turn += 1
        if self.mode == "resume":
            Path(os.environ["ACP_TEST_STATE"]).write_text(
                str(self.turn),
                encoding="utf-8",
            )
        self.cancelled.clear()
        text = getattr(prompt[0], "text", "resource")
        if text == "long":
            text = "x" * 100000
        if text == "crash":
            os._exit(23)
        if text in ("wait", "ignore_cancel"):
            await self._text("running")
            if text == "ignore_cancel":
                await asyncio.Event().wait()
            await self.cancelled.wait()
            await self._text("cancelled")
            return PromptResponse(stop_reason="cancelled")
        if text == "permission":
            await self.connection.session_update(
                session_id=session_id,
                update=ToolCallStart(
                    session_update="tool_call",
                    tool_call_id="call-1",
                    title="Run command",
                    status="pending",
                ),
            )
            response = await self.connection.request_permission(
                session_id=session_id,
                tool_call=ToolCallUpdate(
                    tool_call_id="call-1",
                    title="Run command",
                ),
                options=[
                    PermissionOption(
                        option_id="yes-42",
                        name="Allow",
                        kind="allow_once",
                    ),
                    PermissionOption(
                        option_id="no-42",
                        name="Reject",
                        kind="reject_once",
                    ),
                ],
            )
            await self._text(response.model_dump_json(exclude_none=True))
            return PromptResponse(
                stop_reason=(
                    "cancelled"
                    if response.outcome.outcome == "cancelled"
                    else "end_turn"
                ),
            )
        if text == "snapshots":
            for output in ("first", "first plus last"):
                await self.connection.session_update(
                    session_id=session_id,
                    update=ToolCallProgress.model_validate(
                        {
                            "session_update": "tool_call_update",
                            "tool_call_id": "snapshot",
                            "status": "completed",
                            "content": [
                                {
                                    "type": "content",
                                    "content": {
                                        "type": "text",
                                        "text": output,
                                    },
                                },
                            ],
                        },
                    ),
                )
        if text == "updates":
            for update in [
                AgentThoughtChunk(
                    session_update="agent_thought_chunk",
                    content=TextContentBlock(type="text", text="thinking"),
                ),
                ToolCallStart(
                    session_update="tool_call",
                    tool_call_id="call-1",
                    title="Build",
                    status="in_progress",
                ),
                ToolCallProgress(
                    session_update="tool_call_update",
                    tool_call_id="call-1",
                    status="completed",
                    raw_output={"exit": 0},
                ),
                AgentPlanUpdate(session_update="plan", entries=[]),
            ]:
                await self.connection.session_update(
                    session_id=session_id,
                    update=update,
                )
        if text == "environment":
            text = json.dumps(
                {
                    "cwd": str(Path.cwd()),
                    "args": sys.argv[2:],
                    "inherited": os.environ.get("ACP_TEST_INHERITED"),
                    "override": os.environ.get("ACP_TEST_OVERRIDE"),
                },
            )
        elif text == "resource":
            text = prompt[0].model_dump_json(exclude_none=True)
        elif text == "unsupported":
            try:
                await self.connection.read_text_file(
                    session_id=session_id,
                    path="unavailable.txt",
                )
            except Exception as exc:
                text = str(exc.code)
        await self._text(f"{self.turn}:{text}")
        return PromptResponse(stop_reason="end_turn")

    async def cancel(self, **_kwargs: Any) -> None:
        """Finish waiting prompts, without cancelling their handler tasks."""
        self.cancelled.set()

    async def close_session(self, **_kwargs: Any) -> CloseSessionResponse:
        """Record capability-gated close calls for parent assertions."""
        if os.environ.get("ACP_TEST_CLOSE_HANG"):
            await asyncio.Event().wait()
        Path(os.environ["ACP_TEST_CLOSE_FILE"]).write_text(
            "closed",
            encoding="utf-8",
        )
        return CloseSessionResponse()


class ACPClientTest(unittest.IsolatedAsyncioTestCase):
    """Verify lifecycle and callbacks through real stdio JSON-RPC."""

    async def asyncSetUp(self) -> None:
        self.directory = self.enterContext(
            # unittest owns this context until all async cleanup finishes.
            # pylint: disable-next=consider-using-with
            tempfile.TemporaryDirectory(prefix="acp client 空格 "),
        )
        self.updates = []
        self.running = asyncio.Event()
        self.idle = asyncio.Event()
        self.clients = []

    async def asyncTearDown(self) -> None:
        for client in self.clients:
            await client.aclose()
            if client._process is not None:
                self.assertIsNotNone(client._process.returncode)

    async def collect(self, session_id: str, update: Any) -> None:
        """Record full updates, deliberately yielding to test ordering."""
        await asyncio.sleep(0.001)
        self.assertEqual(session_id, "test-session")
        self.updates.append(update.model_dump(exclude_none=True))
        if getattr(update, "content", None) is not None:
            if getattr(update.content, "text", None) == "running":
                self.running.set()
            if getattr(update.content, "text", None) == "idle":
                self.idle.set()

    def client(self, mode: str = "", **kwargs: Any) -> ACPClient:
        """Build a client pointing to this file's test-only agent entry."""
        env = kwargs.pop("env", {})
        client = ACPClient(
            command=sys.executable,
            args=[
                str(Path(__file__).resolve()),
                "--serve",
                "one two",
                "汉字",
            ],
            cwd=self.directory,
            env={"ACP_TEST_MODE": mode, **env},
            on_update=kwargs.pop("on_update", self.collect),
            startup_timeout=kwargs.pop("startup_timeout", 5),
            cancel_timeout=kwargs.pop("cancel_timeout", 1),
            shutdown_timeout=0.2,
            **kwargs,
        )
        self.clients.append(client)
        return client

    def texts(self) -> list[str]:
        """Read the recorded text chunks."""
        return [
            item["content"]["text"]
            for item in self.updates
            if item["session_update"] == "agent_message_chunk"
        ]

    async def test_round_trip_history_and_ordered_updates(self) -> None:
        """A session retains history and finishes delivering updates."""
        async with self.client() as client:
            self.assertEqual(self.texts(), ["ready"])
            result = await client.prompt("first")
            self.assertEqual(
                result.model_dump(exclude_none=True),
                {"stop_reason": "end_turn"},
            )
            await client.prompt("second")
            self.assertEqual(self.texts(), ["ready", "1:first", "2:second"])
            self.assertTrue(client.is_connected)
        self.assertFalse(client.is_connected)
        await client.aclose()
        with self.assertRaisesRegex(RuntimeError, "new ACPClient"):
            await client.connect()

    async def test_restore_history_in_a_new_process(self) -> None:
        """Loading a retained session continues history without a new ID."""
        env = {"ACP_TEST_STATE": str(Path(self.directory) / "history")}
        async with self.client("resume", env=env) as first:
            await first.prompt("first")
        self.updates.clear()
        async with self.client(
            "resume",
            env=env,
            session_id="test-session",
            preserve_session=True,
        ) as resumed:
            response = await resumed.prompt("second")
            self.assertEqual(resumed.last_response, response)
            self.assertEqual(resumed.session_id, "test-session")
        self.assertEqual(self.texts(), ["historical replay", "2:second"])

    async def test_restore_requires_remote_capability(self) -> None:
        """Unsupported restoration never silently opens a fresh session."""
        with self.assertRaisesRegex(RuntimeError, "cannot restore"):
            await self.client(session_id="test-session").connect()

    async def test_preserve_session_skips_remote_close(self) -> None:
        """Closing the process can retain its remote conversation."""
        marker = Path(self.directory) / "closed"
        async with self.client(
            "close",
            preserve_session=True,
            env={"ACP_TEST_CLOSE_FILE": str(marker)},
        ):
            pass
        self.assertFalse(marker.exists())

    async def test_two_clients_are_independent(self) -> None:
        """Separate instances own separate processes and histories."""
        one, two = self.client(), self.client()
        await asyncio.gather(one.connect(), two.connect())
        await asyncio.gather(one.prompt("one"), two.prompt("two"))
        self.assertEqual(
            sorted(self.texts()),
            ["1:one", "1:two", "ready", "ready"],
        )
        self.assertNotEqual(one._process.pid, two._process.pid)

    async def test_update_shapes_are_preserved(self) -> None:
        """Thought, tool and plan updates retain their complete structure."""
        async with self.client() as client:
            await client.prompt("updates")
        self.assertEqual(
            self.updates[1:],
            [
                {
                    "session_update": "agent_thought_chunk",
                    "content": {"type": "text", "text": "thinking"},
                },
                {
                    "session_update": "tool_call",
                    "tool_call_id": "call-1",
                    "title": "Build",
                    "status": "in_progress",
                },
                {
                    "session_update": "tool_call_update",
                    "tool_call_id": "call-1",
                    "status": "completed",
                    "raw_output": {"exit": 0},
                },
                {"session_update": "plan", "entries": []},
                {
                    "session_update": "agent_message_chunk",
                    "content": {"type": "text", "text": "1:updates"},
                },
            ],
        )

    async def test_permission_options_and_default_cancel(self) -> None:
        """Only exact offered IDs are sent, with cancellation by default."""
        for choice in ("yes-42", "no-42", None):
            with self.subTest(choice=choice):

                async def choose(
                    request: Any,
                    selected: str | None = choice,
                ) -> str | None:
                    self.assertEqual(request.tool_call.tool_call_id, "call-1")
                    self.assertEqual(
                        [item.option_id for item in request.options],
                        ["yes-42", "no-42"],
                    )
                    return selected

                async with self.client(on_permission=choose) as client:
                    result = await client.prompt("permission")
                outcome = (
                    {"outcome": "selected", "option_id": choice}
                    if choice
                    else {"outcome": "cancelled"}
                )
                self.assertEqual(
                    json.loads(self.texts()[-1]),
                    {"outcome": outcome},
                )
                self.assertEqual(
                    result.stop_reason,
                    "end_turn" if choice else "cancelled",
                )
        async with self.client() as client:
            result = await client.prompt("permission")
            self.assertEqual(result.stop_reason, "cancelled")

    async def test_bad_permission_is_reported_to_caller(self) -> None:
        """Invalid approval IDs fail the turn and close the connection."""

        async def choose(_request: Any) -> str:
            return "made-up"

        client = await self.client(on_permission=choose).connect()
        with self.assertRaisesRegex(ValueError, "Unknown ACP permission"):
            await client.prompt("permission")
        self.assertFalse(client.is_connected)

    async def test_cancel_while_permission_pending(self) -> None:
        """Pending approval is cancelled and the session remains usable."""
        waiting, finished = asyncio.Event(), asyncio.Event()

        async def choose(_request: Any) -> None:
            waiting.set()
            try:
                await asyncio.Event().wait()
            finally:
                finished.set()

        async with self.client(on_permission=choose) as client:
            turn = asyncio.create_task(client.prompt("permission"))
            await asyncio.wait_for(waiting.wait(), 3)
            await client.cancel()
            self.assertEqual((await turn).stop_reason, "cancelled")
            self.assertTrue(finished.is_set())
            self.assertEqual(
                json.loads(self.texts()[-1]),
                {"outcome": {"outcome": "cancelled"}},
            )
            self.assertEqual(
                (await client.prompt("again")).stop_reason,
                "end_turn",
            )

    async def test_concurrent_prompt_rejected_and_cancel_reusable(
        self,
    ) -> None:
        """Reject overlapping prompts and finish concurrent cancels."""
        async with self.client() as client:
            turn = asyncio.create_task(client.prompt("wait"))
            await asyncio.wait_for(self.running.wait(), 3)
            with self.assertRaisesRegex(RuntimeError, "already running"):
                await client.prompt("overlap")
            await asyncio.gather(client.cancel(), client.cancel())
            self.assertEqual((await turn).stop_reason, "cancelled")
            await client.prompt("again")
            self.assertEqual(
                self.texts(),
                ["ready", "running", "cancelled", "2:again"],
            )

    async def test_caller_cancellation_and_timeout(self) -> None:
        """Repeated native cancellation still completes remote cleanup."""
        async with self.client() as client:
            turn = asyncio.create_task(client.prompt("wait"))
            await asyncio.wait_for(self.running.wait(), 3)
            turn.cancel()
            await asyncio.sleep(0)
            turn.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await turn
            with self.assertRaises(TimeoutError):
                await client.prompt("wait", timeout=0.05)
            await client.prompt("again")
            self.assertEqual(self.texts()[-1], "3:again")

    async def test_unresponsive_cancel_closes_process(self) -> None:
        """A peer ignoring session/cancel is terminated."""
        client = await self.client(cancel_timeout=0.05).connect()
        with self.assertRaises(TimeoutError):
            await client.prompt("ignore_cancel", timeout=0.05)
        self.assertFalse(client.is_connected)
        self.assertIsNotNone(client._process.returncode)

    async def test_close_during_prompt(self) -> None:
        """Closing first allows the active turn to report cancellation."""
        client = await self.client().connect()
        turn = asyncio.create_task(client.prompt("wait"))
        await asyncio.wait_for(self.running.wait(), 3)
        await client.aclose()
        self.assertEqual((await turn).stop_reason, "cancelled")

    async def test_callback_failure_stops_turn(self) -> None:
        """Callback failures reach prompt callers and terminate the turn."""

        async def fail(_session: str, update: Any) -> None:
            if update.content.text == "running":
                raise ValueError("render failed")

        client = await self.client(on_update=fail).connect()
        with self.assertRaisesRegex(ValueError, "render failed"):
            await client.prompt("wait")
        self.assertFalse(client.is_connected)

    async def test_startup_errors_cleanup(self) -> None:
        """Version, session and startup failures release their process."""
        for mode, error in [
            ("version", RuntimeError),
            ("new_error", Exception),
            ("startup_hang", TimeoutError),
        ]:
            with self.subTest(mode=mode):
                client = self.client(mode, startup_timeout=0.5)
                with self.assertRaises(error):
                    await client.connect()
                self.assertFalse(client.is_connected)
                self.assertIsNotNone(client._process.returncode)

    async def test_close_during_startup(self) -> None:
        """Concurrent close cannot race resource acquisition and leak."""
        client = self.client("startup_hang")
        startup = asyncio.create_task(client.connect())
        while client._process is None:
            await asyncio.sleep(0.01)
        await client.aclose()
        with self.assertRaises(asyncio.CancelledError):
            await startup
        self.assertFalse(client.is_connected)

    async def test_crash_is_not_retried(self) -> None:
        """Transport failure ends the client without replaying a prompt."""
        client = await self.client().connect()
        with self.assertRaises(Exception):
            await client.prompt("crash")
        self.assertFalse(client.is_connected)
        self.assertEqual(client._process.returncode, 23)

    async def test_resource_and_process_arguments(self) -> None:
        """Paths, argv, environment and resource links survive the wire."""
        with patch.dict(os.environ, {"ACP_TEST_INHERITED": "inherited"}):
            async with self.client(
                env={"ACP_TEST_OVERRIDE": "override"},
            ) as client:
                await client.prompt("environment")
                self.assertEqual(
                    json.loads(self.texts()[-1][2:]),
                    {
                        "cwd": str(Path(self.directory).resolve()),
                        "args": ["one two", "汉字"],
                        "inherited": "inherited",
                        "override": "override",
                    },
                )
                block = ResourceContentBlock(
                    type="resource_link",
                    name="notes",
                    uri=Path(self.directory).as_uri(),
                )
                await client.prompt([block])
                self.assertEqual(
                    json.loads(self.texts()[-1][2:]),
                    block.model_dump(exclude_none=True),
                )

    async def test_mcp_configs_are_only_forwarded(self) -> None:
        """MCP configuration is forwarded and capabilities are checked."""
        servers = [
            McpServerStdio(
                name="echo",
                command="not-run-here",
                args=[],
                env=[],
            ),
            HttpMcpServer(
                type="http",
                name="http",
                url="https://example.invalid/mcp",
                headers=[],
            ),
        ]
        async with self.client("mcp", mcp_servers=servers) as client:
            self.assertEqual(
                json.loads(self.texts()[-1]),
                [item.model_dump(exclude_none=True) for item in servers],
            )
        for server, transport in (
            (servers[-1], "HTTP"),
            (
                SseMcpServer(
                    type="sse",
                    name="sse",
                    url="https://example.invalid/sse",
                    headers=[],
                ),
                "SSE",
            ),
        ):
            client = self.client(mcp_servers=[server])
            with self.assertRaisesRegex(ValueError, f"{transport} MCP"):
                await client.connect()

    async def test_capability_gated_close_and_unsupported_rpc(self) -> None:
        """Optional close is used and unsupported client RPCs are rejected."""
        path = Path(self.directory) / "close.txt"
        async with self.client(
            "close",
            env={"ACP_TEST_CLOSE_FILE": str(path)},
        ) as client:
            await client.prompt("unsupported")
            self.assertEqual(self.texts()[-1], "1:-32601")
        self.assertEqual(path.read_text(encoding="utf-8"), "closed")

    async def test_stderr_does_not_block(self) -> None:
        """Large diagnostic output cannot fill an unconsumed stderr pipe."""
        async with self.client("stderr") as client:
            self.assertEqual(
                (await client.prompt("hello")).stop_reason,
                "end_turn",
            )

    async def test_missing_executable_and_invalid_config(self) -> None:
        """Fail predictably for launch errors and invalid configuration."""
        client = ACPClient(str(Path(self.directory) / "missing-agent"))
        self.clients.append(client)
        with self.assertRaises(FileNotFoundError):
            await client.connect()
        for kwargs in (
            {"cwd": "/does/not/exist"},
            {"cancel_timeout": 0},
            {"args": "--acp"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ACPClient("agent", **kwargs)

    async def test_large_notification(self) -> None:
        """Tool snapshots can exceed asyncio's default 64 KiB line limit."""
        async with self.client() as client:
            await client.prompt("long")
            self.assertEqual(self.texts(), ["ready", f"1:{'x' * 100000}"])

    async def test_update_callback_cancellation_is_reported(self) -> None:
        """A callback cancelling itself must not strand queue.join()."""

        async def cancelled(_session: str, _update: Any) -> None:
            raise asyncio.CancelledError

        client = self.client(on_update=cancelled)
        with self.assertRaisesRegex(RuntimeError, "update callback"):
            await client.connect()
        self.assertIsNotNone(client._process.returncode)

    async def test_permission_callback_cancellation_is_reported(self) -> None:
        """Cancelled approval callbacks still return a protocol outcome."""

        async def cancelled(_request: Any) -> None:
            raise asyncio.CancelledError

        client = await self.client(on_permission=cancelled).connect()
        with self.assertRaisesRegex(RuntimeError, "permission callback"):
            await client.prompt("permission")
        self.assertIsNotNone(client._process.returncode)

    async def test_repeated_cancellation_of_close(self) -> None:
        """Native cancellation cannot orphan the owned subprocess."""
        client = await self.client(
            "close",
            env={"ACP_TEST_CLOSE_HANG": "1"},
        ).connect()
        close = asyncio.create_task(client.aclose())
        await asyncio.sleep(0.02)
        close.cancel()
        await asyncio.sleep(0.02)
        close.cancel()
        with self.assertLogs("as", level="WARNING") as logs:
            with self.assertRaises(asyncio.CancelledError):
                await close
        self.assertEqual(len(logs.records), 1)
        self.assertFalse(client.is_connected)
        self.assertIsNotNone(client._process.returncode)
        await client.aclose()

    async def test_cancel_unresponsive_turn_preserves_caller_cancellation(
        self,
    ) -> None:
        """An unresponsive peer preserves caller cancellation semantics."""
        client = await self.client(cancel_timeout=0.05).connect()
        turn = asyncio.create_task(client.prompt("ignore_cancel"))
        await asyncio.wait_for(self.running.wait(), 3)
        turn.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await turn
        self.assertIsNotNone(client._process.returncode)

    async def test_unsupported_input_does_not_break_session(self) -> None:
        """Invalid inputs leave the remote history unchanged."""
        async with self.client() as client:
            with self.assertRaises(TypeError):
                await client.prompt([{"type": "text", "text": "bad"}])
            with self.assertRaises(ValueError):
                await client.prompt("bad", timeout=0)
            await client.prompt("good")
            self.assertEqual(self.texts(), ["ready", "1:good"])

    async def test_optional_dependency_does_not_affect_core_import(
        self,
    ) -> None:
        """Core imports work even when the optional SDK cannot be imported."""
        code = (
            "import sys; sys.modules['acp'] = None; "
            "import agentscope; print(agentscope.__version__)"
        )
        result = await asyncio.to_thread(
            lambda: subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                check=False,
            ),
        )
        self.assertEqual((result.returncode, result.stderr), (0, ""))

    async def test_updates_between_turns(self) -> None:
        """Updates arriving without an active prompt still reach the UI."""
        async with self.client("idle") as client:
            self.assertTrue(client.is_connected)
            await asyncio.wait_for(self.idle.wait(), 3)
            self.assertEqual(self.texts(), ["ready", "idle"])
            await client.prompt("hello")
            self.assertEqual(self.texts(), ["ready", "idle", "1:hello"])

    async def test_agent_ignoring_eof_is_terminated(self) -> None:
        """An agent ignoring EOF cannot keep failed startup alive forever."""
        client = ACPClient(
            sys.executable,
            ["-c", "import time; time.sleep(60)"],
            startup_timeout=0.1,
            shutdown_timeout=0.1,
        )
        self.clients.append(client)
        with self.assertRaises(TimeoutError):
            await asyncio.wait_for(client.connect(), 3)
        self.assertIsNotNone(client._process.returncode)
        self.assertFalse(client.is_connected)


if __name__ == "__main__":
    if "--serve" in sys.argv:
        asyncio.run(run_agent(_StdioAgent(), use_unstable_protocol=True))
    else:
        unittest.main()
