# -*- coding: utf-8 -*-
"""
FastMCP Echo Server
"""
from pydantic import Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Echo Server")


@mcp.tool()
def echo(
    text: str = Field(
        description="Input text",
    ),
) -> str:
    """Echo the input text"""
    return text


if __name__ == "__main__":
    mcp.run()
