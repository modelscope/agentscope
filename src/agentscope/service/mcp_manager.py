# -*- coding: utf-8 -*-
"""
This module manages MCP (ModelContextProtocal) sessions and tool execution
within an asynchronous context. It includes functionality to create, manage,
and close sessions, as well as execute various tools provided by an MCP server.
"""
import asyncio
import os
import shutil
import traceback
from contextlib import AsyncExitStack
from functools import wraps
from typing import Any, Optional, Callable

from loguru import logger

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from .service_response import ServiceResponse, ServiceExecStatus


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
    loop = asyncio.get_event_loop()

    if loop.is_running():
        results = asyncio.run_coroutine_threadsafe(
            func(*args, **kwargs),
            loop,
        ).result()
    else:
        results = loop.run_until_complete(func(*args, **kwargs))
    return results


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

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name: str = name
        self.config: dict[str, Any] = config
        self.session: Optional[ClientSession] = None
        self.stdio_transport = None
        self._session_lock: asyncio.Lock = asyncio.Lock()
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
        if command is not None:
            server_params = StdioServerParameters(
                command=command,
                args=self.config["args"],
                env={**os.environ, **self.config.get("env", {})},
            )
            self.stdio_transport = sync_exec(
                self._stdio_exit_stack.enter_async_context,
                stdio_client(server_params),
            )

    async def create_session(self) -> None:
        """Create a session connection."""
        try:
            if self.stdio_transport:
                read, write = self.stdio_transport
                session = await self._session_exit_stack.enter_async_context(
                    ClientSession(read, write),
                )
            else:
                streams = await self._session_exit_stack.enter_async_context(
                    sse_client(url=self.config["url"]),
                )
                session = await self._session_exit_stack.enter_async_context(
                    ClientSession(*streams),
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
        arguments: dict[str, Any],
    ) -> Any:
        """Execute a tool with retry mechanism."""
        if not self.session:
            raise RuntimeError(f"Session {self.name} not initialized")

        logger.info(f"Executing {tool_name}...")
        result = await self.session.call_tool(tool_name, arguments)
        return result

    def sync_list_tools(self) -> list[Any]:
        """Synchronously list available tools."""
        return sync_exec(self.list_tools)

    def sync_execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] = None,
    ) -> Any:
        """Synchronously execute a tool with given arguments."""
        try:
            result = sync_exec(self.execute_tool, tool_name, arguments)
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=result,
            )
        except Exception as e:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=f"Error: {e}\n\n"
                f"Traceback:\n"
                f"{traceback.format_exc()}",
            )
