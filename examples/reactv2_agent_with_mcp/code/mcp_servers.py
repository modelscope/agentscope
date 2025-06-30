# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager, AsyncExitStack
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount


mcp_add = FastMCP("Add")


@mcp_add.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


mcp_multiply = FastMCP("Miltiply")


@mcp_multiply.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


def combine_lifespans(*lifespans):
    @asynccontextmanager
    async def combined_lifespan(app):
        async with AsyncExitStack() as stack:
            for l in lifespans:
                ctx = l(app)
                await stack.enter_async_context(ctx)
            yield

    return combined_lifespan


main_app = Starlette(
    routes=[
        Mount("/sse_app/", app=mcp_add.sse_app()),
        Mount("/streamable_http_app/", app=mcp_multiply.streamable_http_app()),
    ],
    lifespan=combine_lifespans(lambda app: mcp_multiply.session_manager.run()),
)

if __name__ == "__main__":
    uvicorn.run(main_app, host="0.0.0.0", port=8001)
