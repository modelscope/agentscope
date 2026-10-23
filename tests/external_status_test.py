# -*- coding: utf-8 -*-
"""Executable and account inspection without model or login requests."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from agentscope.app._service._external_runtime._status import (
    check_account,
    detect_executable,
)

STATUS = "agentscope.app._service._external_runtime._status"


class ExternalStatusTest(IsolatedAsyncioTestCase):
    """Verify public status, process cleanup, and credential filtering."""

    def test_detects_explicit_paths_without_starting_process(self) -> None:
        """Discovery is independent of authentication and session creation."""
        with patch("asyncio.create_subprocess_exec") as spawn:
            self.assertEqual(
                detect_executable("codex", sys.executable),
                {
                    "installed": True,
                    "executable": str(Path(sys.executable).resolve()),
                    "error": None,
                },
            )
        spawn.assert_not_called()

    async def test_codex_public_identity_and_authentication_states(
        self,
    ) -> None:
        """Account checks expose only whitelisted identity fields."""
        for raw, expected in [
            (
                {
                    "account": {
                        "type": "chatgpt",
                        "email": "user@example.com",
                        "planType": "plus",
                        "accessToken": "secret",
                    },
                },
                {
                    "status": "authenticated",
                    "account": {
                        "type": "chatgpt",
                        "email": "user@example.com",
                        "planType": "plus",
                    },
                    "error": None,
                },
            ),
            (
                {"account": None, "requiresOpenaiAuth": True},
                {
                    "status": "not_authenticated",
                    "account": None,
                    "error": None,
                },
            ),
            (
                {"account": None, "requiresOpenaiAuth": False},
                {
                    "status": "configured",
                    "account": {"type": "customProvider"},
                    "error": None,
                },
            ),
        ]:
            with self.subTest(raw=raw), patch(
                f"{STATUS}.CodexRuntime",
            ) as runtime:
                runtime.return_value.read_account = AsyncMock(return_value=raw)
                runtime.return_value.aclose = AsyncMock()
                self.assertEqual(
                    await check_account("codex", sys.executable),
                    expected,
                )
                runtime.return_value.aclose.assert_awaited_once()
                runtime.return_value.connect.assert_not_called()

    async def qoder_command(self, script: str) -> tuple[list, asyncio.Event]:
        """Substitute a real Python child for the CLI across platforms."""
        self.enterContext(
            patch.dict(os.environ, {"QODER_PERSONAL_ACCESS_TOKEN": ""}),
        )
        self.enterContext(
            patch(
                f"{STATUS}.resolve_command",
                return_value=(sys.executable, "."),
            ),
        )
        spawn = asyncio.create_subprocess_exec
        processes = []
        started = asyncio.Event()

        async def create(
            command: str,
            argument: str,
            **kwargs: Any,
        ) -> object:
            self.assertEqual((command, argument), (sys.executable, "status"))
            self.assertEqual(kwargs["stdin"], asyncio.subprocess.DEVNULL)
            process = await spawn(command, "-c", script, **kwargs)
            processes.append(process)
            started.set()
            return process

        self.enterContext(
            patch("asyncio.create_subprocess_exec", side_effect=create),
        )
        return processes, started

    async def test_qoder_status_parses_identity_without_sdk_connect(
        self,
    ) -> None:
        """Inspect colored CLI labels; discard unrelated output and secrets."""
        processes, _ = await self.qoder_command(
            "print('\\x1b[32mAccount: user@example.com\\x1b[0m\\n'"
            "'Username: user\\nToken: secret')",
        )
        self.assertEqual(
            await check_account("qoder", ""),
            {
                "status": "authenticated",
                "account": {
                    "type": "qodercli",
                    "email": "user@example.com",
                    "username": "user",
                },
                "error": None,
            },
        )
        self.assertEqual([process.returncode for process in processes], [0])

    async def test_qoder_not_logged_in(self) -> None:
        """Normal signed-out status is distinct from inspection failure."""
        await self.qoder_command("print('Account: Not logged in')")
        self.assertEqual(
            await check_account("qoder", ""),
            {
                "status": "not_authenticated",
                "account": None,
                "error": None,
            },
        )

    async def test_qoder_cli_failure_does_not_expose_output(self) -> None:
        """Failed commands return a safe diagnostic, not arbitrary output."""
        await self.qoder_command("print('Token: secret'); raise SystemExit(2)")
        self.assertEqual(
            await check_account("qoder", ""),
            {
                "status": "error",
                "account": None,
                "error": "Qoder account detection failed (exit 2)",
            },
        )

    async def test_unrecognized_status_is_not_a_login_verdict(self) -> None:
        """Unexpected CLI output must not be presented as signed out."""
        await self.qoder_command("print('unrecognized output')")
        self.assertEqual(
            await check_account("qoder", ""),
            {
                "status": "error",
                "account": None,
                "error": "Qoder returned no recognizable account status",
            },
        )

    async def test_token_presence_is_not_authenticated(self) -> None:
        """Configuration detection does not promise remote token validity."""
        with patch.dict(
            os.environ,
            {"QODER_PERSONAL_ACCESS_TOKEN": "secret"},
        ), patch(
            f"{STATUS}.resolve_command",
            return_value=(sys.executable, "."),
        ), patch(
            "asyncio.create_subprocess_exec",
        ) as spawn:
            self.assertEqual(
                await check_account("qoder", ""),
                {
                    "status": "configured",
                    "account": {"type": "accessToken"},
                    "error": None,
                },
            )
        spawn.assert_not_called()

    async def test_cancelled_status_reaps_process(self) -> None:
        """Repeated cancellation still releases stdout and the child."""
        processes, started = await self.qoder_command(
            "import time; time.sleep(60)",
        )
        task = asyncio.create_task(check_account("qoder", ""))
        await asyncio.wait_for(started.wait(), 5)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await asyncio.wait_for(task, 5)
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].returncode)

    async def test_timed_out_status_reaps_process(self) -> None:
        """The status deadline yields an actionable result and no orphan."""
        processes, _ = await self.qoder_command("import time; time.sleep(60)")
        timeout = asyncio.timeout
        with patch(
            "asyncio.timeout",
            side_effect=lambda _seconds: timeout(0.05),
        ):
            self.assertEqual(
                await check_account("qoder", ""),
                {
                    "status": "error",
                    "account": None,
                    "error": "Account detection timed out. "
                    "Check the CLI and network.",
                },
            )
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].returncode)
