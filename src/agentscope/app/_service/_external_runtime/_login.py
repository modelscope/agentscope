# -*- coding: utf-8 -*-
"""Own the bounded, provider-managed Qoder browser login process."""

import asyncio

from . import resolve_command
from ._base import finish_cleanup, finish_task
from ...._logging import logger

LOGIN_TIMEOUT = 120


class QoderLogin:
    """Keep at most one local login running for this application process."""

    def __init__(self) -> None:
        self.command: str | None = None
        self.task: asyncio.Task | None = None
        self.error: str | None = None
        self.closed = False

    def start(self, executable: str) -> dict:
        """Reuse an active login instead of opening another browser."""
        if self.closed:
            raise RuntimeError("The application is shutting down")
        command, cwd = resolve_command("qoder", executable.strip(), ".")
        if self.task is not None and not self.task.done():
            if command != self.command:
                raise RuntimeError("Another Qoder login is in progress")
        else:
            self.command = command
            self.error = None
            self.task = asyncio.create_task(self._run(command, cwd))
        return {"started": True}

    def error_for(self, executable: str) -> str | None:
        """Associate login failures only with the selected executable."""
        if self.command is None:
            return None
        command, _ = resolve_command("qoder", executable.strip(), ".")
        return self.error if command == self.command else None

    async def _run(self, command: str, cwd: str) -> None:
        spawn = asyncio.create_task(
            asyncio.create_subprocess_exec(
                command,
                "login",
                cwd=cwd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            ),
        )
        original: BaseException | None = None
        try:
            async with asyncio.timeout(LOGIN_TIMEOUT):
                process = await asyncio.shield(spawn)
                code = await process.wait()
            if code:
                self.error = f"Qoder login failed (exit {code}). Try again."
        except asyncio.CancelledError as exc:
            original = exc
            raise
        except TimeoutError as exc:
            original = exc
            self.error = "Qoder login timed out. Try again."
        except Exception as exc:
            original = exc
            self.error = f"Could not start Qoder login: {exc}"
        finally:
            await finish_cleanup(
                asyncio.create_task(self._close_process(spawn)),
                original,
            )

    @staticmethod
    async def _close_process(spawn: asyncio.Task) -> None:
        """Retrieve the child even when cancellation arrived during spawn."""
        try:
            process = await spawn
        except Exception:
            return
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
        await process.wait()

    async def aclose(self) -> None:
        """Reap the owner, reporting failures without breaking app shutdown."""
        self.closed = True
        task = self.task
        if task is None:
            return
        task.cancel()

        async def drain() -> None:
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                message = f"Qoder login cleanup failed: {exc}"
                logger.warning(message)

        await finish_task(asyncio.create_task(drain()))
