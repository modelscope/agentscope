# -*- coding: utf-8 -*-
"""
.. _MCP:

MCP
====================

In this tutorial, we will briefly introduce what MCP is and show how to use MCP in AgentScope. We will also demonstrate how to configure an existing AgentScope multi-agent application as an MCP server. Finally, to help advanced developers gain a deeper understanding, we will discuss how MCP integrates with AgentScope.

.. note:: 1. Before reading this chapter, please read the "Tools" chapter to understand the basic usage of the `ServiceToolkit` module.

 2. Using MCP in AgentScope requires your Python version to be at least 3.10, and you must have installed the `agentscope[service]` version.
"""

# %%
# What is MCP
# --------------------------
# MCP (Model Context Protocol) is an open standard introduced by Anthropic, aimed at standardizing communication between large language models and external data sources and tools, enabling AI models to fully realize their potential.
# Through MCP, AI applications can securely access and manipulate local and remote data, providing a connection method similar to a "USB-C interface" for AI applications.
# This standard not only facilitates API development by service providers but also avoids developers rebuilding basic functions, allowing existing MCP services to enhance the capabilities of intelligent agents. For example, MCP servers can provide predefined prompt templates for generating email drafts or optimizing code comments, thereby improving application development efficiency and quality.

# %%
# MCP supports two communication protocols: Standard Input/Output (STDIO) and HTTP Server-Sent Events (SSE).
# - The STDIO protocol is used for local communication, involving message transmission through standard input and output (i.e., the MCP Server is also started locally). This method typically involves parsing and processing messages line by line, suitable for communication between clients and servers running in the same computing environment.
# - The HTTP protocol is used for remote communication (i.e., the MCP Server is started remotely), encapsulating JSON-RPC messages as SSE events. This mechanism allows the server to push events to the client via a continuously open HTTP connection.

# %%
# Using MCP as a tool for agents in AgentScope
# --------------------------
# AgentScope, as an MCP client, supports starting a local MCP server via STDIO protocol and establishing a connection, as well as using the SSE protocol to connect with a remote MCP server. These usage methods are based on the `ServiceToolkit.add_mcp_servers` interface. The following code demonstrates how to start and connect a server providing browser automation functionality via STDIO locally. This server uses Puppeteer, enabling large models to interact with web pages, take screenshots, and execute JavaScript in a real browser environment. Note that before using the following MCP server, ensure that `Node.js` is installed on your system to ensure the `npx` command runs properly.


from agentscope.service import ServiceToolkit

local_configs = {
    "mcpServers": {
        "puppeteer": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        },
    },
}

# %%
# Initialize ServiceToolkit and add MCP server configuration (uncomment the
# code lines below)

toolkit = ServiceToolkit()
# toolkit.add_mcp_servers(server_configs=local_configs)

# %%
# Output tool configuration instructions to verify settings
print(toolkit.tools_instruction)

# %%
# If you need to use the HTTP protocol to connect to a remote server (or an MCP server running locally in another process using the SSE protocol), you can refer to the following configuration for the connection.

remote_configs = {
    "mcpServers": {
        "puppeteer": {
            "url": "http://127.0.0.1:8000/sse",
        },
    },
}

# Recycle the toolkit instance
del toolkit

# %%
# Adding multi-agent applications created with AgentScope to your own MCP server
# --------------------------
# You can easily add multi-agent applications to your own MCP server using the official MCP Python SDK. The following example code demonstrates how to achieve this purpose using AgentScope and the MCP library.

import agentscope

from agentscope.agents import DialogAgent
from agentscope.message import Msg
from mcp.server import FastMCP
from pydantic import Field

agentscope.init(
    model_configs={
        "config_name": "my-qwen-max",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
    },
)

mcp = FastMCP("My MCP Server")


# %%
# Use the @mcp.tool() decorator to define tools; here we create a joke-telling tool using AgentScope's `DialogAgent`.


@mcp.tool()
def tell_a_joke(
    topic: str = Field(
        description="The topic of a joke",
    ),
) -> int:
    """Generate a joke based on the given topic"""
    agent = DialogAgent(
        name="FunnyBot",
        model_config_name="my-qwen-max",
        sys_prompt="You are a witty comedian tasked with creating a joke about the given topic.",
    )
    msg_task = Msg("user", topic, "user")
    res = agent(msg_task)

    return res.content


# %%
# Save the above code to the file `my_mcp_server.py`.
# Then, run the following command in the terminal to start the server:
# `mcp run my_mcp_server.py -t sse`
# This command starts the MCP server and transmits the results of tool calls via Server-Sent Events (SSE).
# This way, you can access and use the multi-agent application through the configured MCP server.

# %%
# Principle of AgentScope integrating MCP
# --------------------------
# Since the client interface provided by the MCP Python SDK is asynchronous, the developers of AgentScope have encapsulated synchronous interfaces for user convenience.
# Through this encapsulation, users can call asynchronous methods in a synchronous environment, thus improving the usability and readability of the code.

# %%
from agentscope.service.mcp_manager import sync_exec

# %%
# The `sync_exec` function is used to synchronously execute an asynchronous function. It processes by checking the current event loop:
# - If the event loop is running, it runs the coroutine in a different thread using `asyncio.run_coroutine_threadsafe`.
# - If the event loop is not running, it creates a new event loop and runs the coroutine.
# This mechanism allows calling asynchronous functions in synchronous code, suitable for scenarios where the complexity of asynchronous operations is hidden.

# %%
from agentscope.service.mcp_manager import MCPSessionHandler

# %%
# The `MCPSessionHandler` module manages MCP sessions and tool execution, providing users with mechanisms to interact with MCP servers.
# It includes functions for creating, managing, and closing sessions, as well as executing various tools provided by the MCP server.

# %%
# `MCPSessionHandler.__del__` method:
# Since the STDIO server is launched in a subprocess and the official interface provides asynchronous read/write streams, we need to use `AsyncExitStack` to manage the STDIO server startup.
# This ensures that resources of the STDIO server are correctly reclaimed after the main process or main thread ends.
# `AsyncExitStack` ensures correct handling of context entry and exit in asynchronous environments, ensuring safe shutdown and cleanup of resources after server startup. Even if the main process or main thread encounters an exception during execution, `AsyncExitStack` ensures all resources are properly released.
# However, when the STDIO server encounters an exception in the subprocess, the read/write stream does not interrupt, causing the main process to block, leading to resource leakage or blocking issues.
# Therefore, we recommend using the HTTP SSE method to start the MCP server in an independent process. This approach avoids read/write stream blocking caused by subprocess exceptions and provides a more reliable resource management mechanism.
