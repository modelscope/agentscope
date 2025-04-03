# -*- coding: utf-8 -*-
"""
FastMCP AS Nested Server
"""
import os
from pydantic import Field
from mcp.server.fastmcp import FastMCP

import nest_asyncio
import agentscope

# If you do not want to use nest_asyncio, you can comment out the following
# line, but might cause some issues, which can be ignored (RuntimeError:
# Attempted to exit cancel scope in a different task than it was entered in )
nest_asyncio.apply()

mcp = FastMCP("Nested Server")


@mcp.tool()
def echo(
    text: str = Field(
        description="Input text",
    ),
) -> str:
    """Echo the input text"""

    toolkit = agentscope.service.ServiceToolkit()

    server_path = os.path.abspath(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "echo_mcp_server.py",
        ),
    )

    toolkit.add_mcp_servers(
        server_configs={
            "mcpServers": {
                "my_echo_server": {
                    "command": "python",
                    "args": [
                        server_path,
                    ],
                },
            },
        },
    )

    return text


if __name__ == "__main__":
    mcp.run()
