# -*- coding: utf-8 -*-
"""Tests for reconnecting stateful MCP clients."""
import asyncio
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Any, AsyncGenerator
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import patch

import anyio
from mcp import ClientSession

from agentscope.mcp import HttpMCPConfig, MCPClient, StdioMCPConfig


class _OneShotTransport:
    """Minimal transport context manager that cannot be entered twice."""

    def __init__(self) -> None:
        self.enter_count = 0
        self.exit_count = 0

    async def __aenter__(self) -> tuple[object, object]:
        self.enter_count += 1
        if self.enter_count > 1:
            raise AssertionError("transport context manager was reused")
        return object(), object()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.exit_count += 1
        return False


class _FakeSession:
    """Small ClientSession stand-in for lifecycle-only tests."""

    def __init__(self, read_stream: object, write_stream: object) -> None:
        self.read_stream = read_stream
        self.write_stream = write_stream
        self.exit_count = 0

    async def __aenter__(self) -> "_FakeSession":
        """Enter the fake session context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Leave the fake session context."""
        self.exit_count += 1
        return False

    async def initialize(self) -> None:
        """Initialize the fake session."""
        return None


class MCPClientReconnectTest(IsolatedAsyncioTestCase):
    """Stateful MCP transports must be recreated for every connection."""

    async def _check_scoped_cleanup(self, failure: str) -> None:
        """Exercise real session scopes and cancellation checkpoints."""
        # pylint: disable=protected-access
        owner = asyncio.current_task()
        assert owner is not None
        events: list[tuple[str, bool]] = []
        attempts = 0
        original_error = ValueError("initialization failed")

        @asynccontextmanager
        async def transport(
            _parameters: Any,
        ) -> AsyncGenerator[tuple[Any, Any], None]:
            """Keep transport and session scopes nested as in the SDK."""
            incoming, read = anyio.create_memory_object_stream(1)
            write, outgoing = anyio.create_memory_object_stream(1)
            async with anyio.create_task_group():
                async with incoming, read, write, outgoing:
                    events.append(
                        ("transport enter", owner is asyncio.current_task()),
                    )
                    try:
                        yield read, write
                    finally:
                        await anyio.sleep(0)
            events.append(("transport exit", owner is asyncio.current_task()))

        class Session(ClientSession):
            """Keep real session scopes with controlled initialization."""

            async def initialize(self) -> Any:
                """Fail the first attempt and allow a subsequent retry."""
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    if failure == "error":
                        raise original_error
                    if failure == "task":
                        owner.cancel()
                    else:
                        outer.cancel()
                    await anyio.sleep(0)
                return None

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc: BaseException | None,
                traceback: TracebackType | None,
            ) -> bool | None:
                result = await super().__aexit__(exc_type, exc, traceback)
                events.append(
                    ("session exit", owner is asyncio.current_task()),
                )
                return result

        with (
            patch(
                "agentscope.mcp._mcp_client.stdio_client",
                transport,
            ),
            patch("agentscope.mcp._mcp_client.ClientSession", Session),
        ):
            client = MCPClient(
                name="scoped_cleanup",
                is_stateful=True,
                mcp_config=StdioMCPConfig(command="unused"),
            )
            expected = (
                ValueError if failure == "error" else asyncio.CancelledError
            )
            with anyio.CancelScope() as outer:
                with self.assertRaises(expected) as caught:
                    await client.connect()
            if failure == "error":
                self.assertIs(caught.exception, original_error)
            elif failure == "task":
                owner.uncancel()

            self.assertEqual(
                (
                    client.is_connected,
                    client._client,
                    client._session,
                    client._stack,
                ),
                (False, None, None, None),
            )
            self.assertEqual(
                events,
                [
                    ("transport enter", True),
                    ("session exit", True),
                    ("transport exit", True),
                ],
            )
            await client.connect()
            await client.close(ignore_errors=False)
            await anyio.sleep(0)

        self.assertEqual(
            events,
            [
                ("transport enter", True),
                ("session exit", True),
                ("transport exit", True),
            ]
            * 2,
        )

    async def test_failed_connect_closes_real_session_scopes(self) -> None:
        """An initialization error must survive cleanup in the owner task."""
        await self._check_scoped_cleanup("error")

    async def test_task_cancel_closes_real_session_scopes(self) -> None:
        """Native task cancellation must unwind the real session scopes."""
        await self._check_scoped_cleanup("task")

    async def test_anyio_cancel_closes_real_session_scopes(self) -> None:
        """Outer cancellation must not interrupt the transport teardown."""
        await self._check_scoped_cleanup("scope")

    async def test_stdio_client_can_reconnect_after_close(self) -> None:
        """A stdio client must get a new transport after close()."""
        transports: list[_OneShotTransport] = []

        def create_transport(_parameters: Any) -> _OneShotTransport:
            """Create and retain a one-shot transport for assertions."""
            transport = _OneShotTransport()
            transports.append(transport)
            return transport

        with patch(
            "agentscope.mcp._mcp_client.stdio_client",
            side_effect=create_transport,
        ), patch(
            "agentscope.mcp._mcp_client.ClientSession",
            _FakeSession,
        ):
            client = MCPClient(
                name="reconnect_stdio",
                is_stateful=True,
                mcp_config=StdioMCPConfig(command="unused"),
            )

            await client.connect()
            await client.close()
            await client.connect()
            await client.close()

        self.assertEqual(len(transports), 2)
        self.assertTrue(all(_.enter_count == 1 for _ in transports))

    async def test_failed_connect_can_be_retried(self) -> None:
        """A failed connection must discard its one-shot transport."""
        transports: list[_OneShotTransport] = []

        def create_transport(_parameters: Any) -> _OneShotTransport:
            """Create and retain a one-shot transport for assertions."""
            transport = _OneShotTransport()
            transports.append(transport)
            return transport

        class _FailOnceSession(_FakeSession):
            """Fail the first initialization, then allow a retry."""

            attempts = 0

            async def initialize(self) -> None:
                _FailOnceSession.attempts += 1
                if _FailOnceSession.attempts == 1:
                    raise RuntimeError("initialization failed")

        with patch(
            "agentscope.mcp._mcp_client.stdio_client",
            side_effect=create_transport,
        ), patch(
            "agentscope.mcp._mcp_client.ClientSession",
            _FailOnceSession,
        ):
            client = MCPClient(
                name="retry_after_failed_connect",
                is_stateful=True,
                mcp_config=StdioMCPConfig(command="unused"),
            )

            with self.assertRaisesRegex(RuntimeError, "initialization failed"):
                await client.connect()
            await client.connect()
            await client.close()

        self.assertEqual(len(transports), 2)
        self.assertTrue(all(_.enter_count == 1 for _ in transports))

    async def test_cancelled_connect_closes_partial_connection(self) -> None:
        """Cancellation during initialization must clean up and allow retry."""
        initialize_started = asyncio.Event()
        never_finish = asyncio.Event()
        transports: list[_OneShotTransport] = []

        def create_transport(_parameters: Any) -> _OneShotTransport:
            """Create and retain one-shot transports for assertions."""
            transport = _OneShotTransport()
            transports.append(transport)
            return transport

        class _BlockingSession(_FakeSession):
            """Block initialization until the test cancels the connection."""

            instance: "_BlockingSession | None" = None
            attempts = 0

            def __init__(
                self,
                read_stream: object,
                write_stream: object,
            ) -> None:
                super().__init__(read_stream, write_stream)
                _BlockingSession.instance = self

            async def initialize(self) -> None:
                _BlockingSession.attempts += 1
                initialize_started.set()
                if _BlockingSession.attempts == 1:
                    await never_finish.wait()

        with patch(
            "agentscope.mcp._mcp_client.stdio_client",
            side_effect=create_transport,
        ), patch(
            "agentscope.mcp._mcp_client.ClientSession",
            _BlockingSession,
        ):
            client = MCPClient(
                name="cancelled_connect",
                is_stateful=True,
                mcp_config=StdioMCPConfig(command="unused"),
            )

            task = asyncio.create_task(client.connect())
            await initialize_started.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

            session = _BlockingSession.instance
            assert session is not None
            self.assertFalse(client.is_connected)
            self.assertEqual(transports[0].exit_count, 1)
            self.assertEqual(session.exit_count, 1)

            await client.connect()
            await client.close()

        self.assertEqual(len(transports), 2)
        self.assertTrue(all(_.enter_count == 1 for _ in transports))
        self.assertTrue(all(_.exit_count == 1 for _ in transports))

    async def test_cancel_scope_does_not_abandon_the_transport(self) -> None:
        """A cancel scope must not cut the cleanup short."""
        initialize_started = asyncio.Event()
        transport_closed = asyncio.Event()

        class _SlowTransport(_OneShotTransport):
            """Await while closing, the way a real stdio transport does."""

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc: BaseException | None,
                traceback: TracebackType | None,
            ) -> bool:
                await asyncio.sleep(0)
                await super().__aexit__(exc_type, exc, traceback)
                transport_closed.set()
                return False

        class _BlockingSession(_FakeSession):
            """Never finish initializing, so the scope cancels mid-connect."""

            async def initialize(self) -> None:
                initialize_started.set()
                await asyncio.Event().wait()

        transport = _SlowTransport()
        with patch(
            "agentscope.mcp._mcp_client.stdio_client",
            return_value=transport,
        ), patch(
            "agentscope.mcp._mcp_client.ClientSession",
            _BlockingSession,
        ):
            client = MCPClient(
                name="cancel_scope",
                is_stateful=True,
                mcp_config=StdioMCPConfig(command="unused"),
            )

            with anyio.CancelScope() as scope:

                async def _cancel_once_started() -> None:
                    """Cancel the scope once the connect is blocked."""
                    await initialize_started.wait()
                    scope.cancel()

                canceller = asyncio.create_task(_cancel_once_started())
                await client.connect()
            await canceller

        self.assertTrue(scope.cancelled_caught)
        # Cleanup runs to completion even though the scope keeps cancelling.
        await asyncio.wait_for(transport_closed.wait(), 1)
        self.assertEqual(transport.exit_count, 1)
        self.assertFalse(client.is_connected)

    async def test_http_client_can_reconnect_after_close(self) -> None:
        """An HTTP client must get a new transport after close()."""
        transports: list[_OneShotTransport] = []

        def create_transport() -> _OneShotTransport:
            """Create and retain a one-shot transport for assertions."""
            transport = _OneShotTransport()
            transports.append(transport)
            return transport

        with patch.object(
            MCPClient,
            "_create_http_client",
            side_effect=create_transport,
        ), patch(
            "agentscope.mcp._mcp_client.ClientSession",
            _FakeSession,
        ):
            client = MCPClient(
                name="reconnect_http",
                is_stateful=True,
                mcp_config=HttpMCPConfig(url="http://unused"),
            )

            await client.connect()
            await client.close()
            await client.connect()
            await client.close()

        self.assertEqual(len(transports), 2)
        self.assertTrue(all(_.enter_count == 1 for _ in transports))
