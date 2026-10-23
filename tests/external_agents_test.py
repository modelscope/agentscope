# -*- coding: utf-8 -*-
"""Third-party web chat through real HTTP routes and native stdio processes."""

import os
import sys
import tempfile
import time
from pathlib import Path
from functools import partial
from typing import Any, Callable
from unittest import TestCase, IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis

from fastapi.testclient import TestClient

from agentscope.app import create_app
from agentscope.app.deps import get_workspace_manager
from agentscope.app.message_bus import RedisMessageBus
from agentscope.app.storage import (
    AsyncSQLAlchemyStorage,
    RedisStorage,
    SessionConfig,
)
from agentscope.app.storage._model._agent import ExternalAgentConfig
from agentscope.app.workspace_manager import LocalWorkspaceManager
from agentscope.app._service._external import runtime_command
from agentscope.message import UserMsg
from agentscope.app._service._external_runtime._codex import CodexRuntime

HEADERS = {"X-User-ID": "alice"}


# pylint: disable-next=too-many-public-methods
class ExternalWebAgentsTest(TestCase):
    """Exercise the production chat branch without vendor accounts/models."""

    def setUp(self) -> None:
        # unittest owns all contexts until the app has stopped its tasks.
        # pylint: disable=consider-using-with
        self.directory = self.enterContext(tempfile.TemporaryDirectory())
        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

        class Storage(RedisStorage):
            """Use an isolated in-memory Redis backend."""

            async def __aenter__(self) -> Any:
                self._client = redis
                return self

            async def aclose(self) -> None:
                self._client = None

        class Bus(RedisMessageBus):
            """Share the Redis instance across app services."""

            async def __aenter__(self) -> Any:
                self._client = redis
                return self

            async def aclose(self) -> None:
                self._client = None

        self.enterContext(
            patch.dict(
                os.environ,
                {
                    "NATIVE_TEST_MODE": "resume",
                    "NATIVE_TEST_STATE": str(Path(self.directory) / "history"),
                },
            ),
        )
        self.command = self.enterContext(
            patch(
                "agentscope.app._service._external.runtime_command",
                return_value=(
                    sys.executable,
                    self.directory,
                ),
            ),
        )

        def command(
            _provider: str,
            _config: Any,
            cwd: str | None = None,
        ) -> tuple:
            executable, _ = self.command.return_value
            _, directory = runtime_command(
                "codex",
                ExternalAgentConfig(
                    executable=sys.executable,
                    cwd=_config.cwd,
                ),
                cwd=cwd or self.directory,
            )
            return executable, directory

        self.command.side_effect = command
        self.runtimes: list[CodexRuntime] = []

        def runtime(_provider: str, **kwargs: Any) -> CodexRuntime:
            client = CodexRuntime(**kwargs)
            self.runtimes.append(client)
            client.arguments = [
                str(Path(__file__).with_name("native_runtime_test.py")),
                "--serve",
            ]
            return client

        self.enterContext(
            patch(
                "agentscope.app._service._external.create_runtime",
                side_effect=runtime,
            ),
        )
        self.client = self.enterContext(
            TestClient(
                create_app(
                    storage=Storage(),
                    message_bus=Bus(),
                    workspace_manager=LocalWorkspaceManager(self.directory),
                    enable_index_worker=False,
                ),
            ),
        )
        self.agent_id = self.create_agent("codex")
        response = self.client.post(
            "/sessions/",
            headers=HEADERS,
            json={"agent_id": self.agent_id, "name": "native chat"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        self.session_id = response.json()["session_id"]
        self.permissions_url = (
            f"/agent/{self.agent_id}/sessions/"
            f"{self.session_id}/external/permissions"
        )

    def create_agent(self, backend: str) -> str:
        """Create an agent without an AgentScope model configuration."""
        body = {"name": backend, "backend": backend}
        if backend != "agentscope":
            body["external_config"] = {"executable": ""}
        response = self.client.post("/agent/", headers=HEADERS, json=body)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["agent_id"]

    def trigger(self, text: str) -> None:
        """Start a background turn using the ordinary chat endpoint."""
        response = self.client.post(
            "/chat/",
            headers=HEADERS,
            json={
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "input": UserMsg(name="alice", content=text).model_dump(
                    mode="json",
                ),
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

    def wait_for(
        self,
        read: Callable[[], Any],
        predicate: Callable[[Any], bool],
    ) -> Any:
        """Bound polling so a failed background run fails the test."""
        deadline = time.monotonic() + 12
        value = None
        while time.monotonic() < deadline:
            value = read()
            if predicate(value):
                return value
            time.sleep(0.03)
        raise AssertionError(f"Timed out waiting for native: {value}")

    def replies(self) -> list[dict]:
        """Read persisted replies, including metadata after refresh."""
        response = self.client.get(
            f"/sessions/{self.session_id}/messages",
            params={"agent_id": self.agent_id},
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 200, response.text)
        return [
            m for m in response.json()["messages"] if m["role"] == "assistant"
        ]

    def finished(self, count: int = 1) -> list[dict]:
        """Wait until replies are checkpointed and the run lock is free."""
        result = self.wait_for(self.replies, lambda items: len(items) == count)
        self.wait_for(
            lambda: self.client.get(
                "/sessions/",
                params={"agent_id": self.agent_id},
                headers=HEADERS,
            ).json(),
            lambda data: data["sessions"][0]["status"] == "idle",
        )
        return sorted(result, key=lambda msg: msg["created_at"])

    def test_qoder_login_route_and_failure_reporting(self) -> None:
        """Login actions and account polling share the app-owned service."""
        login = self.client.app.state.qoder_login
        with patch.object(
            login,
            "start",
            return_value={"started": True},
        ) as start:
            response = self.client.post(
                "/agent/external/qoder/login",
                headers=HEADERS,
                json={"executable": "selected-cli"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"started": True})
            start.assert_called_once_with("selected-cli")
        for error, status in (
            (ValueError("missing"), 400),
            (RuntimeError("busy"), 409),
        ):
            with self.subTest(status=status), patch.object(
                login,
                "start",
                side_effect=error,
            ):
                response = self.client.post(
                    "/agent/external/qoder/login",
                    headers=HEADERS,
                    json={},
                )
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json(), {"detail": str(error)})
        with patch(
            "agentscope.app._router._external.check_account",
            new=AsyncMock(
                return_value={
                    "status": "not_authenticated",
                    "account": None,
                    "error": None,
                },
            ),
        ), patch.object(login, "error_for", return_value="login failed"):
            response = self.client.post(
                "/agent/external/account",
                headers=HEADERS,
                json={"backend": "qoder", "executable": "selected-cli"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                {"status": "error", "account": None, "error": "login failed"},
            )

    def test_default_directory_uses_backend_configuration(self) -> None:
        """Describe the real default without creating an agent workspace."""
        response = self.client.get(
            "/agent/external/defaults",
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"workspace_path": os.path.join(self.directory, "<agent_id>")},
        )
        root = Path(self.directory) / "another workspace root"
        for manager, expected in (
            (
                LocalWorkspaceManager(basedir=str(root)),
                {"workspace_path": str(root / "<agent_id>")},
            ),
            (object(), {"workspace_path": None}),
        ):
            with self.subTest(manager=type(manager).__name__):
                self.client.app.dependency_overrides[
                    get_workspace_manager
                ] = partial(lambda value: value, manager)
                try:
                    response = self.client.get(
                        "/agent/external/defaults",
                        headers=HEADERS,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json(), expected)
                    self.assertFalse(root.exists())
                finally:
                    del self.client.app.dependency_overrides[
                        get_workspace_manager
                    ]

    def test_create_edit_and_native_compatibility(self) -> None:
        """Providers round-trip; old requests still create native agents."""
        native = self.create_agent("agentscope")
        qoder = self.create_agent("qoder")
        changed = self.client.patch(
            f"/agent/{qoder}",
            headers=HEADERS,
            json={
                "name": "Qoder work",
                "external_config": {
                    "cwd": self.directory,
                    "executable": "qodercli",
                },
            },
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(
            changed.json()["data"]["external_config"],
            {
                "executable": "qodercli",
                "cwd": str(Path(self.directory).resolve()),
            },
        )
        agents = self.client.get("/agent/", headers=HEADERS).json()["agents"]
        self.assertEqual(
            {a["id"]: a["data"]["backend"] for a in agents},
            {native: "agentscope", qoder: "qoder", self.agent_id: "codex"},
        )
        invalid = self.client.post(
            "/agent/",
            headers=HEADERS,
            json={
                "name": "missing config",
                "backend": "codex",
            },
        )
        self.assertEqual(invalid.status_code, 422)

    def test_legacy_config_is_read_and_serialized_with_new_name(self) -> None:
        """Previously created ACP provider settings remain editable."""
        response = self.client.post(
            "/agent/",
            headers=HEADERS,
            json={
                "name": "old",
                "backend": "codex",
                "acp_config": {"executable": "", "cwd": self.directory},
            },
        )
        self.assertEqual(response.status_code, 201)
        agent_id = response.json()["agent_id"]
        response = self.client.patch(
            f"/agent/{agent_id}",
            headers=HEADERS,
            json={
                "acp_config": {"executable": "codex", "cwd": self.directory},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"]["external_config"],
            {
                "executable": "codex",
                "cwd": str(Path(self.directory).resolve()),
            },
        )
        self.assertNotIn("acp_config", response.json()["data"])

    def test_multi_turn_restores_history_and_metadata(self) -> None:
        """Separate processes resume history; load replay is not duplicated."""
        self.trigger("updates")
        first = self.finished()[0]
        self.assertEqual(first["finished_reason"], "completed")
        self.assertEqual(
            first["metadata"],
            {
                "external_tools": {
                    "call-1": {
                        "tool_call_id": "call-1",
                        "title": "Build",
                        "status": "completed",
                        "raw_output": "done",
                        "raw_input": {
                            "id": "call-1",
                            "type": "commandExecution",
                            "command": "Build",
                            "status": "completed",
                            "aggregatedOutput": "done",
                        },
                    },
                },
                "external_plan": [],
            },
        )
        self.trigger("second")
        second = self.finished(2)[1]
        self.assertEqual([b["text"] for b in second["content"]], ["2:second"])
        self.assertEqual(second["finished_reason"], "completed")

    def test_default_workspace_is_stable_across_turns(self) -> None:
        """An omitted path uses the same managed directory every turn."""
        expected = str((Path(self.directory) / self.agent_id).resolve())
        for count in (1, 2):
            self.trigger("cwd")
            reply = self.finished(count)[-1]
            self.assertEqual(reply["finished_reason"], "completed", reply)
            self.assertEqual(
                [block["text"] for block in reply["content"]],
                [expected],
            )
        self.assertEqual(
            [runtime.cwd for runtime in self.runtimes],
            [expected, expected],
        )
        self.assertEqual(
            self.runtimes[0].session_id,
            self.runtimes[1].session_id,
        )

    def test_custom_workspace_is_used_and_can_be_reset(self) -> None:
        """Persist the selected directory and launch the process inside it."""
        custom = Path(self.directory) / "custom workspace"
        custom.mkdir()
        response = self.client.patch(
            f"/agent/{self.agent_id}",
            headers=HEADERS,
            json={"external_config": {"cwd": f"  {custom}  "}},
        )
        expected = str(custom.resolve())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"]["external_config"],
            {"executable": "", "cwd": expected},
        )
        for count in (1, 2):
            self.trigger("cwd")
            reply = self.finished(count)[-1]
            self.assertEqual(reply["finished_reason"], "completed", reply)
            self.assertEqual(
                [block["text"] for block in reply["content"]],
                [expected],
            )
        response = self.client.patch(
            f"/agent/{self.agent_id}",
            headers=HEADERS,
            json={"external_config": {"cwd": "  "}},
        )
        self.assertEqual(
            response.json()["data"]["external_config"],
            {"executable": "", "cwd": ""},
        )
        self.trigger("cwd")
        reply = self.finished(3)[-1]
        self.assertEqual(reply["finished_reason"], "error")
        self.assertIn("Start a new conversation", reply["error"]["message"])
        self.assertEqual(len(self.runtimes), 2)
        created = self.client.post(
            "/sessions/",
            headers=HEADERS,
            json={"agent_id": self.agent_id, "name": "default workspace"},
        )
        self.assertEqual(created.status_code, 201)
        self.session_id = created.json()["session_id"]
        self.trigger("cwd")
        reply = self.finished()[0]
        self.assertEqual(reply["finished_reason"], "completed", reply)
        self.assertEqual(
            [block["text"] for block in reply["content"]],
            [str((Path(self.directory) / self.agent_id).resolve())],
        )

    def test_changed_directory_cannot_silently_resume_history(self) -> None:
        """A different managed root invalidates the remote history binding."""
        self.trigger("first")
        self.finished()
        self.command.side_effect = None
        self.trigger("second")
        reply = self.finished(2)[-1]
        self.assertEqual(reply["finished_reason"], "error")
        self.assertIn("Start a new conversation", reply["error"]["message"])
        self.assertEqual(len(self.runtimes), 1)

    def test_agents_use_their_own_managed_directories(self) -> None:
        """The workspace manager supplies a distinct directory per agent."""
        first_agent = self.agent_id
        self.trigger("cwd")
        first = self.finished()[0]
        self.agent_id = self.create_agent("codex")
        created = self.client.post(
            "/sessions/",
            headers=HEADERS,
            json={"agent_id": self.agent_id, "name": "second workspace"},
        )
        self.assertEqual(created.status_code, 201)
        self.session_id = created.json()["session_id"]
        self.trigger("cwd")
        second = self.finished()[0]
        self.assertEqual(
            [
                [block["text"] for block in reply["content"]]
                for reply in (first, second)
            ],
            [
                [str((Path(self.directory) / agent).resolve())]
                for agent in (first_agent, self.agent_id)
            ],
        )

    def test_tool_snapshots_replace_previous_content(self) -> None:
        """Snapshots are persisted once, including updates without START."""
        self.trigger("snapshots")
        reply = self.finished()[0]
        self.assertEqual(
            reply["metadata"],
            {
                "external_tools": {
                    "snapshot": {
                        "tool_call_id": "snapshot",
                        "status": "completed",
                        "title": "commandExecution",
                        "raw_input": {
                            "id": "snapshot",
                            "type": "commandExecution",
                            "status": "completed",
                        },
                        "raw_output": "first plus last",
                    },
                },
            },
        )

    def test_permission_options_and_access_control(self) -> None:
        """Actual remote IDs are required and cross-user choices fail."""
        self.trigger("permission")
        pending = self.wait_for(
            lambda: self.client.get(
                self.permissions_url,
                headers=HEADERS,
            ).json()["requests"],
            bool,
        )[0]
        url = f"{self.permissions_url}/{pending['request_id']}"
        self.assertEqual(
            pending["options"],
            [
                {
                    "option_id": "allow",
                    "name": "Allow once",
                    "kind": "allow_once",
                },
                {
                    "option_id": "deny",
                    "name": "Reject",
                    "kind": "reject_once",
                },
            ],
        )
        self.assertEqual(
            self.client.post(
                url,
                headers={"X-User-ID": "bob"},
                json={"option_id": "allow"},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                url,
                headers=HEADERS,
                json={"option_id": "invented"},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                url,
                headers=HEADERS,
                json={"option_id": "allow"},
            ).json(),
            {"accepted": True},
        )
        self.assertEqual(
            self.client.post(
                url,
                headers=HEADERS,
                json={"option_id": "allow"},
            ).status_code,
            409,
        )
        reply = self.finished()[0]
        self.assertEqual(reply["finished_reason"], "completed")
        self.assertEqual(reply["content"][0]["text"], '{"decision": "accept"}')
        self.assertEqual(
            self.client.get(
                self.permissions_url,
                headers=HEADERS,
            ).json(),
            {"requests": []},
        )

    def test_cancel_permission_and_continue(self) -> None:
        """Interrupt releases approvals and preserves resumable history."""
        self.trigger("permission")
        self.wait_for(
            lambda: self.client.get(
                self.permissions_url,
                headers=HEADERS,
            ).json()["requests"],
            bool,
        )
        interrupted = self.client.post(
            f"/sessions/{self.session_id}/interrupt",
            headers=HEADERS,
            params={"agent_id": self.agent_id},
        )
        self.assertEqual(interrupted.status_code, 202, interrupted.text)
        cancelled = self.finished()[0]
        self.assertEqual(cancelled["finished_reason"], "interrupted")
        self.assertEqual(
            cancelled["metadata"]["external_tools"]["call-1"],
            {
                "tool_call_id": "call-1",
                "title": "Run command",
                "status": "failed",
                "raw_input": {
                    "id": "call-1",
                    "type": "commandExecution",
                    "command": "Run command",
                },
                "raw_output": "",
            },
        )
        self.assertEqual(
            self.client.get(
                self.permissions_url,
                headers=HEADERS,
            ).json(),
            {"requests": []},
        )
        self.trigger("after cancel")
        reply = self.finished(2)[1]
        self.assertEqual(reply["finished_reason"], "completed", reply)
        self.assertEqual(reply["content"][0]["text"], "2:after cancel")

    def test_delete_during_approval_cleans_up_the_active_run(self) -> None:
        """Normal session deletion also stops its third-party process."""
        self.trigger("permission")
        self.wait_for(
            lambda: self.client.get(
                self.permissions_url,
                headers=HEADERS,
            ).json()["requests"],
            bool,
        )
        response = self.client.delete(
            f"/sessions/{self.session_id}",
            headers=HEADERS,
            params={"agent_id": self.agent_id},
        )
        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual(
            self.client.get(
                self.permissions_url,
                headers=HEADERS,
            ).status_code,
            404,
        )

    def test_crash_blocks_unsafe_history_replay(self) -> None:
        """A lost prompt response prevents silently retrying tool actions."""
        self.trigger("crash")
        self.assertEqual(self.finished()[0]["finished_reason"], "error")
        self.trigger("retry")
        reply = self.finished(2)[1]
        self.assertEqual(reply["finished_reason"], "error")
        self.assertIn("Start a new conversation", reply["error"]["message"])

    def test_changed_runtime_requires_a_new_conversation(self) -> None:
        """A different executable must not inherit another runtime's ID."""
        self.trigger("first")
        self.finished()
        command, cwd = self.command.return_value
        self.command.return_value = (f"{command}-changed", cwd)
        self.trigger("second")
        reply = self.finished(2)[1]
        self.assertEqual(reply["finished_reason"], "error")
        self.assertIn("Start a new conversation", reply["error"]["message"])
        self.assertEqual(
            Path(os.environ["NATIVE_TEST_STATE"]).read_text(encoding="utf-8"),
            "1",
        )

    def test_permission_reject_and_dismiss(self) -> None:
        """Reject and dismiss both deny the operation."""
        for count, choice in enumerate(("deny", None), start=1):
            with self.subTest(choice=choice):
                self.trigger("permission")
                pending = self.wait_for(
                    lambda: self.client.get(
                        self.permissions_url,
                        headers=HEADERS,
                    ).json()["requests"],
                    bool,
                )[0]
                self.assertEqual(
                    self.client.post(
                        f"{self.permissions_url}/{pending['request_id']}",
                        headers=HEADERS,
                        json={"option_id": choice},
                    ).json(),
                    {"accepted": True},
                )
                reply = self.finished(count)[-1]
                self.assertEqual(
                    reply["finished_reason"],
                    "completed",
                )

    def test_connection_failure_is_actionable(self) -> None:
        """Missing dependencies and protocol support reach the UI."""
        for mode, hint in (
            ("login", "not authenticated"),
            ("protocol_error", "Unsupported protocol"),
        ):
            with self.subTest(mode=mode), patch.dict(
                os.environ,
                {"NATIVE_TEST_MODE": mode},
            ):
                response = self.client.post(
                    "/agent/external/check",
                    headers=HEADERS,
                    json={
                        "backend": "codex",
                        "external_config": {
                            "cwd": self.directory,
                        },
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.json()["ready"])
                self.assertIn(hint, response.json()["error"])

    def test_realtime_is_explicitly_unsupported(self) -> None:
        """Third-party agents cannot enter native realtime assembly."""
        response = self.client.post(
            f"/realtime/sessions/{self.session_id}/offer",
            headers=HEADERS,
            json={"agent_id": self.agent_id, "sdp": "test offer"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "detail": "Third-party agents support text chat only",
            },
        )

    def test_executable_and_account_checks_are_separate(self) -> None:
        """Inspection needs neither a chat directory nor a session."""
        response = self.client.post(
            "/agent/external/detect",
            headers=HEADERS,
            json={"backend": "codex", "executable": sys.executable},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "installed": True,
                "executable": str(Path(sys.executable).resolve()),
                "error": None,
            },
        )
        with patch(
            "agentscope.app._service._external_runtime._status."
            "CodexRuntime.read_account",
            new_callable=AsyncMock,
            return_value={"account": None, "requiresOpenaiAuth": True},
        ):
            response = self.client.post(
                "/agent/external/account",
                headers=HEADERS,
                json={"backend": "codex", "executable": sys.executable},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "not_authenticated",
                "account": None,
                "error": None,
            },
        )

    def test_connection_check_uses_preinstalled_runtime(self) -> None:
        """Probe the native handshake without calling a model."""
        response = self.client.post(
            "/agent/external/check",
            headers=HEADERS,
            json={
                "backend": "qoder",
                "external_config": {"cwd": self.directory},
            },
        )
        self.assertEqual(
            response.json(),
            {
                "ready": True,
                "executable": sys.executable,
                "cwd": str(Path(self.directory).resolve()),
                "error": None,
            },
        )


class ExternalStorageTest(IsolatedAsyncioTestCase):
    """Keep native state separate from native state and editable config."""

    async def test_both_backends_preserve_session_fields(self) -> None:
        """Selective state writes round-trip through Redis and SQL."""
        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        self.addAsyncCleanup(redis.aclose)
        redis_storage = RedisStorage()
        # pylint: disable-next=protected-access
        redis_storage._client = redis
        sql = await self.enterAsyncContext(
            AsyncSQLAlchemyStorage(
                "sqlite+aiosqlite:///:memory:",
                create_tables=True,
            ),
        )
        for storage in (redis_storage, sql):
            with self.subTest(backend=type(storage).__name__):
                original = await storage.upsert_session(
                    "alice",
                    "agent",
                    SessionConfig(
                        workspace_id="workspace",
                        name="conversation",
                    ),
                )
                remote = {
                    "session_id": "remote",
                    "binding": "hash",
                    "in_flight": False,
                }
                await storage.update_session_external_state(
                    "alice",
                    "agent",
                    original.id,
                    remote,
                )
                current = await storage.get_session(
                    "alice",
                    "agent",
                    original.id,
                )
                expected = original.model_dump(exclude={"updated_at"})
                expected["external_state"] = remote
                self.assertEqual(
                    current.model_dump(exclude={"updated_at"}),
                    expected,
                )
                with self.assertRaises(LookupError):
                    await storage.update_session_external_state(
                        "bob",
                        "agent",
                        original.id,
                        remote,
                    )

    async def test_workspace_paths_are_normalized_and_validated(self) -> None:
        """Resolve home/relative paths and reject unavailable directories."""
        for value, expected in (
            ("  ", ""),
            ("~", str(Path.home().resolve())),
            (".", str(Path.cwd().resolve())),
        ):
            with self.subTest(value=value):
                self.assertEqual(
                    ExternalAgentConfig(cwd=value).model_dump(),
                    {"executable": "", "cwd": expected},
                )
        with tempfile.TemporaryDirectory() as root:
            for path in (Path(root) / "missing", Path(root) / "file"):
                if path.name == "file":
                    path.touch()
                with self.subTest(path=path):
                    with self.assertRaisesRegex(
                        ValueError,
                        "Working directory does not exist",
                    ):
                        runtime_command(
                            "codex",
                            ExternalAgentConfig(
                                executable=sys.executable,
                                cwd=str(path),
                            ),
                            cwd=root,
                        )

    async def test_shell_launchers_require_native_executables(self) -> None:
        """Do not implicitly run Windows batch launchers through a shell."""
        with patch("shutil.which", return_value="codex-acp.cmd"):
            with self.assertRaisesRegex(ValueError, "native executable"):
                runtime_command(
                    "codex",
                    ExternalAgentConfig(executable="test.cmd"),
                )
