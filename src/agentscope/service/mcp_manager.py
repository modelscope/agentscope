# -*- coding: utf-8 -*-
"""
This module manages MCP (ModelContextProtocal) sessions and tool execution
within an asynchronous context. It includes functionality to create, manage,
and close sessions, as well as execute various tools provided by an MCP server.
"""
import asyncio
import os
import shutil
import sys
import traceback
from contextlib import AsyncExitStack
from functools import wraps
from typing import Any, Optional, Callable, Tuple
import nest_asyncio

from anyio.streams.memory import (
    MemoryObjectReceiveStream,
    MemoryObjectSendStream,
)
from loguru import logger

try:
    import mcp
    from mcp.client.sse import sse_client
    from mcp.client.stdio import stdio_client

except ImportError:
    mcp = None

from .service_response import ServiceResponse, ServiceExecStatus


COROUTINE_TIMEOUT_SECONDS = 60


def sync_exec(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    Execute a function synchronously.

    Args:
        func (Callable): The asynchronous function to execute.
        *args (Any): Positional arguments to pass to the function.
        **kwargs (Any): Keyword arguments to pass to the function.

    Returns:
        Any: The result of the function execution.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as e:
        # If there is no event loop in the current context, create one
        if "no current event loop" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        else:
            raise

    # Apply nest_asyncio in Jupyter environments to allow nested event loops
    if "ipykernel" in sys.modules:
        nest_asyncio.apply(loop)

    if loop.is_running():
        # Attempt to run directly after applying nest_asyncio
        try:
            result = loop.run_until_complete(func(*args, **kwargs))
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                logger.warning(
                    "Event loop is running, using "
                    "`run_coroutine_threadsafe`, which will block the "
                    f"process until the func `{func.__name__}` is finished. "
                    f"This operation has a timeout of"
                    f" {COROUTINE_TIMEOUT_SECONDS} seconds.",
                )

                # Fallback to thread-safe execution with timeout
                result = asyncio.run_coroutine_threadsafe(
                    func(*args, **kwargs),
                    loop,
                ).result(timeout=COROUTINE_TIMEOUT_SECONDS)
            else:
                raise
    else:
        result = loop.run_until_complete(func(*args, **kwargs))
    return result


def session_decorator(func: Callable) -> Callable:
    """
    Decorator to manage session creation and closure around a function.

    Args:
        func (Callable): The function to decorate.

    Returns:
        Callable: The wrapped function with session management.
    """

    @wraps(func)
    async def wrapper(
        handler: "MCPSessionHandler",
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        try:
            # Initialize the handler session
            await handler.create_session()
            # Execute the function
            result = await func(handler, *args, **kwargs)
            return result
        finally:
            # Ensure close_session is called even if the function fails
            await handler.close_session()

    return wrapper


class MCPSessionHandler:
    """Handles MCP session connections and tool execution."""

    def __init__(
        self,
        name: str,
        config: dict[str, Any],
        sync: bool = True,
    ) -> None:
        """
        Initialize an MCPSessionHandler instance.

        Parameters:
        name (str): The unique name of the MCP server. This identifies the
            server within the toolkit and is used to distinguish between
            different server configurations.

        config (dict[str, Any]): A dictionary containing the configuration
            details for the MCP server. This configuration includes
            protocol-specific settings required to establish and manage
            communication with the server.

            Example structure:
            {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/xxxx"],
            } or
            {
                "url": "http://xxx.xxx.xxx.xxx:xxxx/sse"
            }

            - "command": (Optional) A string indicating the command to be
                executed, following the stdio protocol for communication.
            - "args": (Optional) A list of arguments for the command.
            - "url": (Optional) A string representing the server's endpoint,
                which follows the Server-Sent Events (SSE) protocol for data
                transmission.

        sync (bool, default=True): A boolean flag indicating whether the
            MCPSessionHandler should operate in synchronous mode. If True,
            the stdio server will initialize in `__init__` in a sync mode.
        """
        if mcp is None:
            raise ModuleNotFoundError(
                "MCP is not available. Please ensure that MCP "
                "is installed via `pip install mcp` and that you are using "
                "Python 3.10 or higher.",
            )

        self.name: str = name
        self.config: dict[str, Any] = config
        self.session: Optional[mcp.ClientSession] = None
        self.stdio_transport = None
        self._session_lock: asyncio.Lock = asyncio.Lock()
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        # Manage session context
        self._session_exit_stack: AsyncExitStack = AsyncExitStack()
        # Manage stdio server context
        self._stdio_exit_stack: AsyncExitStack = AsyncExitStack()

        # Initialize stdio_transport if necessary
        command = (
            shutil.which("npx")
            if self.config.get("command") == "npx"
            else self.config.get("command")
        )
        if command is not None and sync:
            self.stdio_transport = sync_exec(self._initialize_stdio_transport)

    async def _initialize_stdio_transport(
        self,
    ) -> Tuple[MemoryObjectReceiveStream, MemoryObjectSendStream]:
        """
        Initialize `stdio_transport`
        """
        command = (
            shutil.which("npx")
            if self.config.get("command") == "npx"
            else self.config.get("command")
        )
        args = self.config.get("args", [])
        env = self.config.get("env", {})

        try:
            server_params = mcp.StdioServerParameters(
                command=command,
                args=args,
                env={**os.environ, **env},
            )
            # If an error happens in the process after `anyio.open_process`
            # in `stdio_client`, it might not raise an exception, please
            # make sure your mcp server is well-configured and the command is
            # correct before you using this function.
            stdio_transport = await self._stdio_exit_stack.enter_async_context(
                stdio_client(server_params),
            )
            return stdio_transport
        except Exception as e:
            if self._stdio_exit_stack:
                await self._stdio_exit_stack.aclose()
            raise e

    async def close(self) -> None:
        """
        Clean up server stream resources.
        """
        if self._stdio_exit_stack and self.stdio_transport:
            async with self._cleanup_lock:
                try:
                    await self._stdio_exit_stack.aclose()
                    self.stdio_transport = None
                except Exception:
                    pass
                finally:
                    logger.info(f"Clean up MCP Server `{self.name}` finished.")

    def __del__(self) -> None:
        """
        Close all resources using a potentially risky synchronous execution
        method.

        Notes:
        This method attempts to close resources across different threads and
        event loops. While it may raise a RuntimeError due to task/event
        loop boundary crossing, the underlying AsyncExitStack mechanism
        ensures resource cleanup. Please use `self.close()` in async mode.

        Behavior:
        - Attempts to synchronously execute the async close method
        - May trigger a RuntimeError during execution
        - Resource cleanup is still performed due to AsyncExitStack's
        internal mechanism
        - Error is effectively suppressed, ensuring no resource leaks

        Caution:
        This is a temporary workaround that relies on implementation-specific
        behavior of AsyncExitStack and sync_exec. Future versions should
        implement a more robust resource management strategy.

        Warning:
        Do not modify this method without careful consideration of its
        subtle resource management implications.
        """
        if asyncio is None or asyncio.get_event_loop is None:
            # When the code is executed directly at the top level in a script,
            # the `asyncio` will recycle before the instance. In such case,
            # when the function is triggered by `__del__`, there is nothing to
            # delete. Unless you call `del` in the end.
            return

        if self._stdio_exit_stack and self.stdio_transport:
            sync_exec(self.close)

    async def create_session(self) -> None:
        """Create a session connection."""
        try:
            if self.stdio_transport:
                read, write = self.stdio_transport
                session = await self._session_exit_stack.enter_async_context(
                    mcp.ClientSession(read, write),
                )
            else:
                streams = await self._session_exit_stack.enter_async_context(
                    sse_client(url=self.config["url"]),
                )
                session = await self._session_exit_stack.enter_async_context(
                    mcp.ClientSession(*streams),
                )
            await session.initialize()
            self.session = session
        except Exception as e:
            logger.error(f"Error initializing session for {self.name}: {e}")
            await self.close_session()
            raise

    async def close_session(self) -> None:
        """Clean up session resources."""
        async with self._session_lock:
            try:
                await self._session_exit_stack.aclose()
                self.session = None
            except Exception as e:
                logger.error(
                    f"Error during closing session {self.name}: {e}",
                )

    @session_decorator
    async def list_tools(self) -> list[Any]:
        """List available tools from the server."""
        if not self.session:
            raise RuntimeError(f"Session {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = [
            tool
            for item in tools_response
            if isinstance(item, tuple) and item[0] == "tools"
            for tool in item[1]
        ]

        return tools

    @session_decorator
    async def execute_tool(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> ServiceResponse:
        """Execute a tool and return ServiceResponse"""
        if not self.session:
            raise RuntimeError(f"Session {self.name} not initialized")

        logger.info(f"Executing {tool_name}...")

        try:
            result = await self.session.call_tool(tool_name, kwargs)
            content, is_error = result.content, result.isError

            if is_error:
                return ServiceResponse(
                    status=ServiceExecStatus.ERROR,
                    content=content,
                )
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=content,
            )
        except Exception as e:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=f"Error: {e}\n\n"
                f"Traceback:\n"
                f"{traceback.format_exc()}",
            )
