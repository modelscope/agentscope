# -*- coding: utf-8 -*-
"""Preserve primary failures and cancellation across native cleanup."""

import asyncio
import os
import sys
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from agentscope.app._service._external import check_runtime
from agentscope.app.storage._model._agent import ExternalAgentConfig
from agentscope.app._service._external_runtime._base import finish_task
from agentscope.app._service._external_runtime._codex import CodexRuntime
from agentscope.app._service._external_runtime._status import check_account

BASE = "agentscope.app._service._external_runtime._base"
STATUS = "agentscope.app._service._external_runtime._status"


class NativeCleanupTest(IsolatedAsyncioTestCase):
    """Test error precedence at the actual context and account boundaries."""

    def runtime(self) -> CodexRuntime:
        """Create a runtime whose connection and cleanup are controllable."""
        runtime = CodexRuntime(
            command=sys.executable,
            cwd=".",
            session_id=None,
            on_update=AsyncMock(),
            on_permission=AsyncMock(),
        )
        runtime.connect = AsyncMock()
        runtime.aclose = AsyncMock()
        return runtime

    async def test_finish_task_reports_failure_after_repeated_cancel(
        self,
    ) -> None:
        """Cancellation wins after the child finishes, even if it fails."""
        for failure in (None, RuntimeError("cleanup failed")):
            with self.subTest(failure=failure):
                entered, release = asyncio.Event(), asyncio.Event()

                async def cleanup(
                    start: asyncio.Event = entered,
                    gate: asyncio.Event = release,
                    error: Exception | None = failure,
                ) -> str:
                    start.set()
                    await gate.wait()
                    if error:
                        raise error
                    return "done"

                child = asyncio.create_task(cleanup())
                waiter = asyncio.create_task(finish_task(child))
                with patch(f"{BASE}.logger.warning") as warning:
                    await entered.wait()
                    waiter.cancel()
                    await asyncio.sleep(0)
                    waiter.cancel()
                    await asyncio.sleep(0)
                    self.assertFalse(child.done())
                    release.set()
                    with self.assertRaises(asyncio.CancelledError):
                        await waiter
                    self.assertEqual(
                        warning.call_count,
                        int(failure is not None),
                    )
                self.assertTrue(waiter.cancelled())
                self.assertFalse(child.cancelled())
                self.assertIs(child.exception(), failure)

    async def test_primary_connect_and_body_failures_survive_cleanup(
        self,
    ) -> None:
        """A secondary close failure does not replace a primary failure."""
        for stage in ("connect", "body"):
            for primary in (ValueError("primary"), asyncio.CancelledError()):
                with self.subTest(stage=stage, primary=type(primary).__name__):
                    runtime = self.runtime()
                    runtime.aclose.side_effect = RuntimeError("cleanup failed")
                    if stage == "connect":
                        runtime.connect.side_effect = primary
                    with patch(f"{BASE}.logger.warning") as warning:
                        with self.assertRaises(type(primary)) as caught:
                            async with runtime:
                                raise primary
                        self.assertIs(caught.exception, primary)
                        warning.assert_called_once()
                    runtime.aclose.assert_awaited_once()

    async def test_connect_timeout_is_not_replaced(self) -> None:
        """Initialization retains its actionable timeout diagnostic."""
        runtime = self.runtime()
        original = TimeoutError("connect")
        runtime.connect.side_effect = original
        runtime.aclose.side_effect = RuntimeError("cleanup failed")
        with patch(f"{BASE}.logger.warning"):
            with self.assertRaisesRegex(
                TimeoutError,
                "initialization timed out",
            ) as caught:
                async with runtime:
                    self.fail("Connection should have failed")
        self.assertIs(caught.exception.__cause__, original)

    async def test_cleanup_failure_after_success_is_visible(self) -> None:
        """Successful work does not silently hide failed resource cleanup."""
        runtime = self.runtime()
        failure = RuntimeError("cleanup failed")
        runtime.aclose.side_effect = failure
        with self.assertRaises(RuntimeError) as caught:
            async with runtime:
                pass
        self.assertIs(caught.exception, failure)

    async def test_normal_exit_propagates_cancellation(self) -> None:
        """Cancellation arriving only during __aexit__ is not swallowed."""
        runtime = self.runtime()
        entered, release = asyncio.Event(), asyncio.Event()

        async def cleanup() -> None:
            entered.set()
            await release.wait()

        runtime.aclose.side_effect = cleanup

        async def run() -> None:
            async with runtime:
                pass

        task = asyncio.create_task(run())
        await entered.wait()
        task.cancel()
        await asyncio.sleep(0)
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
        runtime.aclose.assert_awaited_once()
        self.assertTrue(task.cancelled())

    async def test_codex_account_preserves_primary_error(self) -> None:
        """Inspection failures survive, while sole cleanup failures surface."""
        for failure, message in (
            (ValueError("original failure"), "original failure"),
            (
                TimeoutError(),
                "Account detection timed out. Check the CLI and network.",
            ),
            (None, "cleanup failed"),
        ):
            with self.subTest(failure=failure), patch(
                f"{STATUS}.CodexRuntime",
            ) as cls:
                cls.return_value.read_account = AsyncMock(
                    return_value={"account": None},
                    side_effect=failure,
                )
                cls.return_value.aclose = AsyncMock(
                    side_effect=RuntimeError("cleanup failed"),
                )
                with patch(f"{BASE}.logger.warning"):
                    self.assertEqual(
                        await check_account("codex", sys.executable),
                        {"status": "error", "account": None, "error": message},
                    )

    async def test_qoder_account_preserves_error_when_kill_fails(self) -> None:
        """A kill failure cannot replace the failed status request."""
        process = Mock(returncode=None)
        process.communicate = AsyncMock(
            side_effect=ValueError("original failure"),
        )
        process.kill.side_effect = OSError("kill failed")
        with patch.dict(
            os.environ,
            {"QODER_PERSONAL_ACCESS_TOKEN": ""},
        ), patch(
            f"{STATUS}.resolve_command",
            return_value=(sys.executable, "."),
        ), patch(
            f"{STATUS}.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ), patch(
            f"{BASE}.logger.warning",
        ) as warning:
            self.assertEqual(
                await check_account("qoder", ""),
                {
                    "status": "error",
                    "account": None,
                    "error": "original failure",
                },
            )
            warning.assert_called_once()

    async def test_account_cleanup_keeps_late_cancellation(self) -> None:
        """A successfully inspected account cannot swallow cancellation."""
        entered, release = asyncio.Event(), asyncio.Event()

        async def cleanup() -> None:
            entered.set()
            await release.wait()

        with patch(f"{STATUS}.CodexRuntime") as cls:
            cls.return_value.read_account = AsyncMock(
                return_value={"account": None},
            )
            cls.return_value.aclose = AsyncMock(side_effect=cleanup)
            task = asyncio.create_task(check_account("codex", sys.executable))
            await entered.wait()
            task.cancel()
            await asyncio.sleep(0)
            release.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertTrue(task.cancelled())

    async def test_account_cleanup_ignores_callers_handled_exception(
        self,
    ) -> None:
        """Only this operation's failure can take precedence over cleanup."""
        with patch(f"{STATUS}.CodexRuntime") as cls:
            cls.return_value.read_account = AsyncMock(
                return_value={"account": None},
            )
            cls.return_value.aclose = AsyncMock(
                side_effect=RuntimeError("cleanup failed"),
            )
            try:
                raise ValueError("unrelated caller failure")
            except ValueError:
                result = await check_account("codex", sys.executable)
            self.assertEqual(
                result,
                {
                    "status": "error",
                    "account": None,
                    "error": "cleanup failed",
                },
            )

    async def test_connection_probe_preserves_primary_error(self) -> None:
        """The standalone handshake endpoint retains its connection error."""
        runtime = self.runtime()
        runtime.connect.side_effect = ValueError("connection failed")
        runtime.aclose.side_effect = RuntimeError("cleanup failed")
        with patch(
            "agentscope.app._service._external.create_runtime",
            return_value=runtime,
        ), patch(f"{BASE}.logger.warning") as warning:
            self.assertEqual(
                await check_runtime(
                    "codex",
                    ExternalAgentConfig(executable=sys.executable),
                ),
                {"ready": False, "error": "connection failed"},
            )
            warning.assert_called_once()
        runtime.aclose.assert_awaited_once()
