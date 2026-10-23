# -*- coding: utf-8 -*-
"""Shared turn lifecycle and application callbacks for native runtimes."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

from ...._logging import logger
from ....types import ReplyFinishedReason

Update = Callable[[dict], Awaitable[None]]
Permission = Callable[[dict], Awaitable[str | None]]


async def finish_task(task: asyncio.Task) -> Any:
    """Drain an owned task, preserving cancellation and retrieving failures."""
    cancelled = None
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError as exc:
            cancelled = cancelled or exc
        except Exception:
            break
    try:
        result = task.result()
    except (Exception, asyncio.CancelledError) as exc:
        if cancelled is None:
            raise
        if not isinstance(exc, asyncio.CancelledError):
            message = f"Owned task failed during cancellation: {exc}"
            logger.warning(message)
    if cancelled is not None:
        raise cancelled
    return result


async def finish_cleanup(
    task: asyncio.Task,
    original: BaseException | None,
) -> None:
    """Preserve a primary failure while reporting secondary cleanup errors."""
    try:
        await finish_task(task)
    except asyncio.CancelledError:
        caller = asyncio.current_task()
        if original is None or (caller is not None and caller.cancelling()):
            raise
        message = f"Cleanup cancelled while handling {type(original).__name__}"
        logger.warning(message)
    except Exception as exc:
        if original is None:
            raise
        message = (
            f"Cleanup failed while handling {type(original).__name__}: {exc}"
        )
        logger.warning(message)


class NativeRuntime(ABC):
    """One process and one remote conversation per application turn."""

    def __init__(
        self,
        command: str,
        cwd: str,
        session_id: str | None,
        on_update: Update,
        on_permission: Permission,
    ) -> None:
        self.command = command
        self.cwd = cwd
        self.session_id: str | None = session_id
        self.on_update = on_update
        self.on_permission = on_permission
        self.completed = False
        self.cancelled = asyncio.Event()

    async def choose(self, request: dict, signal: Any = None) -> str | None:
        """Release a pending UI approval when the turn or tool is cancelled."""
        choice = asyncio.ensure_future(self.on_permission(request))
        stopped = asyncio.create_task(self.cancelled.wait())
        tasks = [choice, stopped]
        if signal is not None:
            tasks.append(asyncio.create_task(signal.wait()))
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            if stopped.done() or (len(tasks) == 3 and tasks[2].done()):
                return None
            return choice.result()
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def prompt(self, text: str) -> ReplyFinishedReason:
        """Cancel through the provider and wait for a definitive turn end."""
        turn = asyncio.create_task(self._prompt(text))
        try:
            return await asyncio.shield(turn)
        except asyncio.CancelledError as exc:
            self.cancelled.set()
            await finish_cleanup(
                asyncio.create_task(self._stop_turn(turn)),
                exc,
            )
            raise

    async def _stop_turn(self, turn: asyncio.Task) -> None:
        try:
            async with asyncio.timeout(10):
                await self.interrupt()
                await asyncio.shield(turn)
        except (Exception, asyncio.CancelledError):
            turn.cancel()
        finally:
            await asyncio.gather(turn, return_exceptions=True)

    async def __aenter__(self) -> "NativeRuntime":
        try:
            async with asyncio.timeout(30):
                await self.connect()
        except TimeoutError as exc:
            await finish_cleanup(asyncio.create_task(self.aclose()), exc)
            raise TimeoutError(
                "Runtime initialization timed out. Check CLI login, "
                "network connection, and runtime configuration.",
            ) from exc
        except BaseException as exc:
            await finish_cleanup(asyncio.create_task(self.aclose()), exc)
            raise
        return self

    async def __aexit__(
        self,
        _exc_type: Any,
        exc: BaseException | None,
        _traceback: Any,
    ) -> None:
        self.cancelled.set()
        await finish_cleanup(asyncio.create_task(self.aclose()), exc)

    @abstractmethod
    async def connect(self, probe: bool = False) -> None:
        """Initialize and restore a session, or only check the runtime."""

    @abstractmethod
    async def _prompt(self, text: str) -> ReplyFinishedReason:
        """Send one prompt and consume updates through its terminal result."""

    @abstractmethod
    async def interrupt(self) -> None:
        """Request provider-side cancellation."""

    @abstractmethod
    async def aclose(self) -> None:
        """Release processes and tasks without removing remote history."""


def approval(tool_id: str, title: str, inputs: Any) -> dict:
    """Offer per-operation approval without creating persistent grants."""
    return {
        "tool_call": {
            "tool_call_id": tool_id,
            "title": title,
            "raw_input": inputs,
        },
        "options": [
            {"option_id": "allow", "name": "Allow once", "kind": "allow_once"},
            {"option_id": "deny", "name": "Reject", "kind": "reject_once"},
        ],
    }
