# -*- coding: utf-8 -*-
"""
This module manages MCP (ModelContextProtocol) sessions and tool execution
within an asynchronous context. It includes functionality to create, manage,
and close sessions, as well as execute various tools provided by an MCP server.
"""
import atexit
import threading
import asyncio
import os
import shutil
import traceback
from contextlib import AsyncExitStack
from typing import Any, Optional, Callable
import nest_asyncio
from loguru import logger

try:
    import mcp
    from mcp.client.sse import sse_client
    from mcp.client.stdio import stdio_client

except ImportError:
    mcp = None

from .service_response import ServiceResponse, ServiceExecStatus


# Apply nest_asyncio to allow nested event loops
# This step enables running event loops multiple times within the same thread
# Note: There is a known issue with uvloop, referenced here:
# https://github.com/MagicStack/uvloop/issues/405
# Users might encounter conflicts with uvloop when using nested event loops
# with the following lines.
# nest_asyncio.apply()


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

    try:
        result = loop.run_until_complete(func(*args, **kwargs))
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            # Apply nest_asyncio to allow nested event loops
            # To support jupyter notebook, etc.
            nest_asyncio.apply()
            result = loop.run_until_complete(func(*args, **kwargs))
        else:
            raise
    return result


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

        self._exit_stack: AsyncExitStack = AsyncExitStack()
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()

        # Initialize
        if sync:
            sync_exec(self.initialize)
            if threading.current_thread().name == "MainThread":
                # No need to do it at subthread, which will block the main
                # thread
                atexit.register(lambda: sync_exec(self.cleanup))

    async def initialize(self) -> None:
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
            if command:
                server_params = mcp.StdioServerParameters(
                    command=command,
                    args=args,
                    env={**os.environ, **env},
                )
                # If an error happens in the process after `anyio.open_process`
                # in `stdio_client`, it might not raise an exception, please
                # make sure your mcp server is well-configured and the
                # command is correct before you using this function.
                streams = await self._exit_stack.enter_async_context(
                    stdio_client(server_params),
                )
            else:
                streams = await self._exit_stack.enter_async_context(
                    sse_client(url=self.config["url"]),
                )
            session = await self._exit_stack.enter_async_context(
                mcp.ClientSession(*streams),
            )
            await session.initialize()
            self.session = session
        except Exception as e:
            logger.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """
        Clean up server stream resources.
        """
        async with self._cleanup_lock:
            try:
                await self._exit_stack.aclose()
                self.session = None
                self._exit_stack = None
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

        if self._exit_stack:
            sync_exec(self.cleanup)

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
            # TODO: consider support image data and embedding resources
            content, is_error = (
                [x.model_dump() for x in result.content],
                result.isError,
            )

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
