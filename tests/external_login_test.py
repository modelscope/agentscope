# -*- coding: utf-8 -*-
"""Qoder login ownership using real, harmless child processes."""

import asyncio
import sys
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from agentscope.app._service._external_runtime._login import QoderLogin

LOGIN = "agentscope.app._service._external_runtime._login"


class QoderLoginTest(IsolatedAsyncioTestCase):
    """Exercise deduplication, deadlines, failures, and shutdown races."""

    async def asyncSetUp(self) -> None:
        self.login = QoderLogin()
        self.addAsyncCleanup(self.login.aclose)
        self.enterContext(
            patch(
                f"{LOGIN}.resolve_command",
                side_effect=lambda _provider, command, _cwd: (
                    command or sys.executable,
                    ".",
                ),
            ),
        )
        self.processes = []
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.release.set()
        self.code = "import sys; assert sys.stdin.read() == ''"
        create = asyncio.create_subprocess_exec

        async def spawn(
            *_args: Any,
            **kwargs: Any,
        ) -> asyncio.subprocess.Process:
            process = await create(sys.executable, "-c", self.code, **kwargs)
            self.processes.append(process)
            self.started.set()
            await self.release.wait()
            return process

        self.spawn = self.enterContext(
            patch(
                f"{LOGIN}.asyncio.create_subprocess_exec",
                side_effect=spawn,
            ),
        )

    async def test_repeated_start_reuses_process_and_allows_retry(
        self,
    ) -> None:
        """One pending process consumes EOF; finished logins can restart."""
        self.assertEqual(
            [self.login.start(""), self.login.start("")],
            [{"started": True}, {"started": True}],
        )
        await self.login.task
        self.spawn.assert_awaited_once_with(
            sys.executable,
            "login",
            cwd=".",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self.assertEqual(self.login.error_for(""), None)
        self.assertEqual(self.login.start(""), {"started": True})
        await self.login.task
        self.assertEqual([p.returncode for p in self.processes], [0, 0])

    async def test_failure_is_safe_and_scoped_to_command(self) -> None:
        """Report exit status without exposing command output."""
        self.code = "print('credential-secret'); raise SystemExit(7)"
        self.login.start("")
        await self.login.task
        self.assertEqual(
            [self.login.error_for(""), self.login.error_for("different")],
            ["Qoder login failed (exit 7). Try again.", None],
        )
        self.assertEqual(self.processes[0].returncode, 7)

    async def test_deadline_reaps_process_and_retry_clears_failure(
        self,
    ) -> None:
        """A stalled login is killed, reaped, and can be retried."""
        self.code = "import time; time.sleep(60)"
        with patch(f"{LOGIN}.LOGIN_TIMEOUT", 0.1):
            self.login.start("")
            await self.login.task
        self.assertEqual(
            self.login.error_for(""),
            "Qoder login timed out. Try again.",
        )
        self.assertIsNotNone(self.processes[0].returncode)
        self.code = "pass"
        self.login.start("")
        self.assertEqual(self.login.error_for(""), None)
        await self.login.task
        self.assertEqual(self.processes[1].returncode, 0)

    async def test_shutdown_during_spawn_reaps_child(self) -> None:
        """Cancelling before spawn returns still retrieves the child."""
        self.code = "import time; time.sleep(60)"
        self.release.clear()
        self.login.start("")
        await self.started.wait()
        with self.assertRaisesRegex(RuntimeError, "Another Qoder login"):
            self.login.start("another")
        closing = asyncio.create_task(self.login.aclose())
        await asyncio.sleep(0)
        self.release.set()
        await closing
        self.assertIsNotNone(self.processes[0].returncode)
        self.assertTrue(self.login.task.done())
        with self.assertRaisesRegex(RuntimeError, "shutting down"):
            self.login.start("")

    async def test_cancelling_shutdown_still_reaps_spawned_child(self) -> None:
        """The spawn result stays owned when shutdown itself is cancelled."""
        self.code = "import time; time.sleep(60)"
        self.release.clear()
        self.login.start("")
        await self.started.wait()
        closing = asyncio.create_task(self.login.aclose())
        await asyncio.sleep(0)
        closing.cancel()
        await asyncio.sleep(0)
        closing.cancel()
        self.release.set()
        with self.assertRaises(asyncio.CancelledError):
            await closing
        self.assertIsNotNone(self.processes[0].returncode)
        self.assertTrue(self.login.task.done())

    async def test_shutdown_logs_unexpected_owner_failure(self) -> None:
        """Unexpected owner errors are retrieved and reported on shutdown."""

        async def fail() -> None:
            raise RuntimeError("cleanup failed")

        self.login.task = asyncio.create_task(fail())
        await asyncio.sleep(0)
        with patch(f"{LOGIN}.logger.warning") as warning:
            await self.login.aclose()
            warning.assert_called_once_with(
                "Qoder login cleanup failed: cleanup failed",
            )

    async def test_spawn_failure_is_retrieved(self) -> None:
        """A missing executable cannot leave an unobserved task exception."""
        self.spawn.side_effect = FileNotFoundError("missing executable")
        self.login.start("")
        await self.login.task
        self.assertEqual(
            self.login.error_for(""),
            "Could not start Qoder login: missing executable",
        )
