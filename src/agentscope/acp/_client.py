# -*- coding: utf-8 -*-
"""A single-session stdio client for the Agent Client Protocol."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable, Mapping, Sequence
from contextlib import AsyncExitStack, suppress
from pathlib import Path
from typing import Any, TypeAlias, TypeVar

from acp import PROTOCOL_VERSION, spawn_agent_process
from acp.client.connection import ClientSideConnection
from acp.connection import StreamDirection, StreamEvent
from acp.core import DEFAULT_STDIO_BUFFER_LIMIT_BYTES
from acp.schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AllowedOutcome,
    AvailableCommandsUpdate,
    ClientCapabilities,
    ConfigOptionUpdate,
    CurrentModeUpdate,
    DeniedOutcome,
    HttpMcpServer,
    Implementation,
    InitializeResponse,
    McpServerStdio,
    NewSessionResponse,
    PermissionOption,
    PromptResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    ResourceContentBlock,
    SessionInfoUpdate,
    SessionNotification,
    SseMcpServer,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    ToolCallUpdate,
    UsageUpdate,
    UserMessageChunk,
)

from .._version import __version__
from .._logging import logger

_Update: TypeAlias = (
    AgentMessageChunk
    | AgentPlanUpdate
    | AgentThoughtChunk
    | AvailableCommandsUpdate
    | ConfigOptionUpdate
    | CurrentModeUpdate
    | SessionInfoUpdate
    | ToolCallProgress
    | ToolCallStart
    | UsageUpdate
    | UserMessageChunk
)
UpdateCallback = Callable[[str, _Update], Awaitable[None]]
PermissionCallback = Callable[
    [RequestPermissionRequest],
    Awaitable[str | None],
]
_T = TypeVar("_T")


async def _finish(task: asyncio.Task[_T]) -> _T:
    """Finish owned cleanup even if the caller is cancelled repeatedly."""
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled = True
    if cancelled:
        # Retrieve failures even when cancellation takes precedence.
        with suppress(BaseException):
            task.result()
        raise asyncio.CancelledError
    return task.result()


class ACPClient:
    """Own one external ACP process and one conversation.

    Args:
        command: Executable to launch without a shell.
        args: Arguments passed verbatim to the executable.
        cwd: Existing working directory, also used for the ACP session.
        env: Environment overrides, added to the current environment.
        on_update: Async callback receiving the session ID and an SDK update.
            Updates are delivered in wire order, including outside prompts.
            Tool content updates are replacement snapshots, not text deltas.
        on_permission: Async callback receiving an SDK permission request.
            Return one offered option ID, or None to cancel. Without a
            callback, all permission requests are cancelled.
        mcp_servers: MCP configurations forwarded to the external agent.
        startup_timeout: Seconds allowed for startup and session creation.
        cancel_timeout: Seconds to wait for a cancelled turn to finish.
        shutdown_timeout: Seconds for session close and each process shutdown
            stage (EOF, terminate, kill).
        session_id: Existing remote session to load instead of creating one.
        preserve_session: Skip session/close so persistent history can be
            loaded by a later client. The stdio process is still closed.

    Callbacks must cooperate with asyncio cancellation and must not await
    this client's lifecycle methods. No client filesystem or terminal RPCs
    are advertised. Authentication must be configured externally. This is
    a Python protocol client, not an AgentScope Agent or console adapter.
    Closed or failed instances are single-use; create a new client to retry.
    """

    def __init__(
        self,
        command: str,
        args: Sequence[str] = (),
        *,
        cwd: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        on_update: UpdateCallback | None = None,
        on_permission: PermissionCallback | None = None,
        mcp_servers: Sequence[
            HttpMcpServer | SseMcpServer | McpServerStdio
        ] = (),
        startup_timeout: float = 30.0,
        cancel_timeout: float = 10.0,
        shutdown_timeout: float = 5.0,
        session_id: str | None = None,
        preserve_session: bool = False,
    ) -> None:
        if not command or isinstance(args, str):
            raise ValueError("Provide an executable and an argument sequence")
        directory = Path(cwd or Path.cwd()).expanduser().resolve()
        if not directory.is_dir():
            raise ValueError(f"ACP cwd is not a directory: {directory}")
        if min(startup_timeout, cancel_timeout, shutdown_timeout) <= 0:
            raise ValueError("ACP timeouts must be positive")
        self._resume_session_id = session_id
        self._preserve_session = preserve_session
        self._command = command
        self._args = tuple(args)
        self._cwd = directory
        self._env = dict(env or {})
        self._on_update = on_update
        self._on_permission = on_permission
        self._mcp_servers = list(mcp_servers)
        self._startup_timeout = startup_timeout
        self._cancel_timeout = cancel_timeout
        self._shutdown_timeout = shutdown_timeout
        self._stack = AsyncExitStack()
        self._connection: ClientSideConnection | None = None
        self._process: asyncio.subprocess.Process | None = None
        self._initialize_response: InitializeResponse | None = None
        self._session: NewSessionResponse | None = None
        self.last_response: PromptResponse | None = None
        self._connect_task: asyncio.Task[None] | None = None
        self._started = False
        self._closing = False
        self._failure: asyncio.Future[Exception] | None = None
        self._updates: asyncio.Queue[SessionNotification] = asyncio.Queue()
        self._update_task: asyncio.Task[None] | None = None
        self._prompt_task: asyncio.Task[PromptResponse] | None = None
        self._cancel_task: asyncio.Task[None] | None = None
        self._close_task: asyncio.Task[None] | None = None
        self._cancel_requested = asyncio.Event()

    @property
    def is_connected(self) -> bool:
        """Whether the session is usable and its transport is still open."""
        return bool(
            self._session is not None
            and self._connect_task is not None
            and self._connect_task.done()
            and not self._closing
            and self._failure is not None
            and not self._failure.done()
            and self._process is not None
            and self._process.returncode is None
            and self._process.stdout is not None
            and not self._process.stdout.at_eof(),
        )

    @property
    def session_id(self) -> str | None:
        """The session ID returned by the external agent."""
        return self._session.session_id if self._session else None

    @property
    def initialize_response(self) -> InitializeResponse | None:
        """Remote capabilities, implementation and authentication methods."""
        return self._initialize_response

    async def connect(self) -> ACPClient:
        """Start the agent, negotiate ACP v1 and create a session once."""
        if self._started or self._closing:
            raise RuntimeError("Create a new ACPClient to connect again")
        self._started = True
        self._failure = asyncio.get_running_loop().create_future()
        self._update_task = asyncio.create_task(self._deliver_updates())
        self._connect_task = asyncio.create_task(self._start())
        try:
            async with asyncio.timeout(self._startup_timeout):
                pending: list[asyncio.Future[Any]] = [
                    self._connect_task,
                    self._failure,
                ]
                await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                self._raise_callback_error()
                self._connect_task.result()
        except BaseException:
            await self.aclose()
            raise
        return self

    async def _start(self) -> None:
        """Keep resource acquisition separate from callers and cleanup."""
        (
            self._connection,
            self._process,
        ) = await self._stack.enter_async_context(
            spawn_agent_process(
                self,
                self._command,
                *self._args,
                cwd=self._cwd,
                env={**os.environ, **self._env},
                transport_kwargs={
                    "stderr": None,
                    "limit": DEFAULT_STDIO_BUFFER_LIMIT_BYTES,
                    "shutdown_timeout": self._shutdown_timeout,
                },
                observers=[self._observe],
                use_unstable_protocol=True,
            ),
        )
        self._initialize_response = await self._connection.initialize(
            protocol_version=PROTOCOL_VERSION,
            client_capabilities=ClientCapabilities(),
            client_info=Implementation(
                name="agentscope",
                version=__version__,
            ),
        )
        if self._initialize_response.protocol_version != PROTOCOL_VERSION:
            raise RuntimeError("Agent negotiated an unsupported ACP version")
        self._validate_mcp_capabilities()
        if self._resume_session_id is None:
            self._session = await self._connection.new_session(
                cwd=str(self._cwd),
                mcp_servers=self._mcp_servers,
            )
        else:
            if not self._initialize_response.agent_capabilities.load_session:
                raise RuntimeError(
                    "Agent cannot restore this conversation; start a new one",
                )
            await self._connection.load_session(
                session_id=self._resume_session_id,
                cwd=str(self._cwd),
                mcp_servers=self._mcp_servers,
            )
            self._session = NewSessionResponse(
                session_id=self._resume_session_id,
            )
        await self._updates.join()
        self._raise_callback_error()

    def _validate_mcp_capabilities(self) -> None:
        """Check optional transports before forwarding MCP configurations."""
        capabilities = self._initialize_response.agent_capabilities
        mcp = capabilities.mcp_capabilities if capabilities else None
        for server in self._mcp_servers:
            if isinstance(server, HttpMcpServer) and not (mcp and mcp.http):
                raise ValueError("Agent does not support HTTP MCP servers")
            if isinstance(server, SseMcpServer) and not (mcp and mcp.sse):
                raise ValueError("Agent does not support SSE MCP servers")

    def _observe(self, event: StreamEvent) -> None:
        """Queue updates before the SDK resolves a following RPC response."""
        if (
            event.direction == StreamDirection.INCOMING
            and event.message.get("method") == "session/update"
        ):
            try:
                notification = SessionNotification.model_validate(
                    event.message.get("params"),
                )
                self._updates.put_nowait(notification)
            except Exception as exc:
                self._fail(exc)

    def _fail(self, error: Exception) -> None:
        """Remember callback errors without unobserved Future exceptions."""
        if self._failure is not None and not self._failure.done():
            self._failure.set_result(error)

    def _raise_callback_error(self) -> None:
        if self._failure is not None and self._failure.done():
            raise self._failure.result()

    async def _deliver_updates(self) -> None:
        """Serialize user callbacks independently of SDK dispatch tasks."""
        while True:
            notification = await self._updates.get()
            try:
                self._raise_callback_error()
                if self._on_update is not None:
                    await self._on_update(
                        notification.session_id,
                        notification.update,
                    )
            except asyncio.CancelledError:
                if self._closing:
                    raise
                self._fail(RuntimeError("ACP update callback was cancelled"))
            except Exception as exc:
                self._fail(exc)
            finally:
                self._updates.task_done()

    async def session_update(
        self,
        session_id: str,
        update: _Update,
        **kwargs: Any,
    ) -> None:
        """SDK hook; ordered delivery is handled by the stream observer."""

    async def request_permission(
        self,
        options: list[PermissionOption],
        session_id: str,
        tool_call: ToolCallUpdate,
        **kwargs: Any,
    ) -> RequestPermissionResponse:
        """Resolve a remote request with an offered ID or cancellation."""
        denied = RequestPermissionResponse(
            outcome=DeniedOutcome(outcome="cancelled"),
        )
        handler = self._on_permission
        if (
            handler is None
            or self._closing
            or self._cancel_requested.is_set()
            or session_id != self.session_id
        ):
            return denied

        async def choose() -> str | None:
            return await handler(
                RequestPermissionRequest(
                    options=options,
                    session_id=session_id,
                    tool_call=tool_call,
                    field_meta=kwargs or None,
                ),
            )

        callback = asyncio.create_task(choose())
        cancelled = asyncio.create_task(self._cancel_requested.wait())
        try:
            await asyncio.wait(
                [callback, cancelled],
                return_when=asyncio.FIRST_COMPLETED,
            )
            if self._cancel_requested.is_set():
                return denied
            selected = callback.result()
            if selected is None:
                return denied
            if selected not in {option.option_id for option in options}:
                raise ValueError(f"Unknown ACP permission option: {selected}")
            return RequestPermissionResponse(
                outcome=AllowedOutcome(
                    outcome="selected",
                    option_id=selected,
                ),
            )
        except asyncio.CancelledError:
            if not self._closing and not self._cancel_requested.is_set():
                self._fail(
                    RuntimeError("ACP permission callback was cancelled"),
                )
            return denied
        except Exception as exc:
            self._fail(exc)
            return denied
        finally:
            callback.cancel()
            cancelled.cancel()
            await asyncio.gather(callback, cancelled, return_exceptions=True)

    async def prompt(
        self,
        prompt: str | Sequence[TextContentBlock | ResourceContentBlock],
        *,
        timeout: float | None = None,
    ) -> PromptResponse:
        """Run one turn, delivering updates before returning its stop reason.

        Caller cancellation and timeout first send session/cancel. If the
        agent does not finish within cancel_timeout, the client is closed.
        Concurrent prompts on the same instance are rejected.
        """
        self._raise_callback_error()
        if not self.is_connected:
            raise RuntimeError("ACP client is not connected")
        if self._prompt_task is not None:
            raise RuntimeError("An ACP prompt is already running")
        if timeout is not None and timeout <= 0:
            raise ValueError("Prompt timeout must be positive")
        blocks = (
            [TextContentBlock(type="text", text=prompt)]
            if isinstance(prompt, str)
            else list(prompt)
        )
        if any(
            not isinstance(block, (TextContentBlock, ResourceContentBlock))
            for block in blocks
        ):
            raise TypeError("Only text and resource_link input is supported")
        assert self._failure is not None
        self.last_response = None
        self._cancel_requested.clear()
        self._cancel_task = None
        self._prompt_task = asyncio.create_task(self._run_prompt(blocks))
        try:
            async with asyncio.timeout(timeout):
                await asyncio.wait(
                    [self._prompt_task, self._failure],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                self._raise_callback_error()
                return self._prompt_task.result()
        except (asyncio.CancelledError, TimeoutError):
            with suppress(Exception):
                await _finish(asyncio.create_task(self.cancel()))
            raise
        except Exception:
            await self.aclose()
            raise
        finally:
            self._prompt_task = None

    async def _run_prompt(
        self,
        blocks: list[TextContentBlock | ResourceContentBlock],
    ) -> PromptResponse:
        response = await self._connection.prompt(
            prompt=blocks,
            session_id=self.session_id,
        )
        self.last_response = response
        await self._updates.join()
        self._raise_callback_error()
        return response

    async def _cancel_turn(
        self,
        task: asyncio.Task[PromptResponse],
    ) -> None:
        if task.done():
            return
        self._cancel_requested.set()
        async with asyncio.timeout(self._cancel_timeout):
            await self._connection.cancel(session_id=self.session_id)
            await asyncio.shield(task)

    async def cancel(self) -> None:
        """Cancel the active turn, closing an unresponsive connection."""
        if self._prompt_task is None or self._prompt_task.done():
            return
        if self._cancel_task is None:
            self._cancel_task = asyncio.create_task(
                self._cancel_turn(self._prompt_task),
            )
        try:
            await _finish(self._cancel_task)
        except Exception:
            await self.aclose()
            raise

    async def aclose(self) -> None:
        """Release the session and process, including during cancellation."""
        if self._close_task is None:
            self._closing = True
            self._close_task = asyncio.create_task(self._close())
        await _finish(self._close_task)

    async def _close(self) -> None:
        if self._connect_task is not None:
            self._connect_task.cancel()
            await asyncio.gather(self._connect_task, return_exceptions=True)
        task = self._prompt_task
        self._cancel_requested.set()
        try:
            if self._prompt_task is not None and not self._prompt_task.done():
                if self._cancel_task is None:
                    self._cancel_task = asyncio.create_task(
                        self._cancel_turn(self._prompt_task),
                    )
                with suppress(Exception, asyncio.CancelledError):
                    await self._cancel_task
            capabilities = (
                self._initialize_response.agent_capabilities
                if self._initialize_response
                else None
            )
            sessions = (
                capabilities.session_capabilities if capabilities else None
            )
            if (
                self._session
                and sessions
                and sessions.close is not None
                and not self._preserve_session
            ):
                try:
                    async with asyncio.timeout(self._shutdown_timeout):
                        await self._connection.close_session(
                            session_id=self.session_id,
                        )
                except Exception as exc:
                    message = (
                        f"ACP session close failed "
                        f"({type(exc).__name__}): {exc}"
                    )
                    logger.warning(message)
        finally:
            if self._update_task is not None:
                self._update_task.cancel()
                await asyncio.gather(self._update_task, return_exceptions=True)
            try:
                await self._stack.aclose()
            finally:
                if task is not None:
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)

    async def __aenter__(self) -> ACPClient:
        return await self.connect()

    async def __aexit__(self, *_exc: Any) -> None:
        await self.aclose()
