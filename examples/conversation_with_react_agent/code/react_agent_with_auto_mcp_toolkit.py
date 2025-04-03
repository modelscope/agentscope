# -*- coding: utf-8 -*-
"""An example of how to use AutoServiceToolkit with ReAct agent."""
import os
from agentscope.agents import ReActAgent, UserAgent
import agentscope
from agentscope.service import ServiceToolkit

if __name__ == "__main__":
    YOUR_MODEL_CONFIGURATION_NAME = "dashscope_config"
    YOUR_MODEL_CONFIGURATION = {
        "model_type": "dashscope_chat",
        "config_name": YOUR_MODEL_CONFIGURATION_NAME,
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "model_name": "qwen-max",
    }

    agentscope.init(
        model_configs=YOUR_MODEL_CONFIGURATION,
        project="Conversation with ReActAgent",
        save_api_invoke=True,
    )

    # Prepare the toolkit that can automatically search tools for the agent
    service_toolkit = ServiceToolkit(
        mcp_search_allow=True,
        # If you want the agent control the MCP server installation, uncomment
        # auto_install_mcp=True
    )

    human_confirm_sys_prompt = (
        "You are a helpful assistant that can help people finish different "
        "tasks."
        "When you need new tools, you can automatically search for appropriate"
        " tools (in terms of MCP servers)."
        "You need to follow the the following instructions: \n"
        "1. When you obtain some candidate MCP servers, you need to "
        "analysis the candidate MCP servers, then break the reasoning process "
        "by calling the `finish` function and wait for human response.\n"
        "2. When the user confirms to install a MCP server, you need "
        "to obtain the configuration template of the MCP server. \n"
        "3. When you get the template, you can break the reasoning process by "
        "calling the `finish` function and "
        "ask the user to confirm the configuration for you. \n"
        "4. With the confirmed MCP configuration, you can go ahead and "
        "install the MCP server.\n"
        "5. After all above, you can use the tools to solve user's original "
        "question."
    )

    # when auto_install_mcp=True
    auto_confirm_sys_prompt = (
        "You are a helpful assistant that can help people finish different "
        "tasks."
        "When you need new tools, you can automatically search for appropriate"
        " tools (in terms of MCP servers)."
        "You need to follow the the following instructions: \n"
        "1. When you obtain some candidate MCP servers, you need to analysis "
        "the candidate MCP servers, and select the best one to install. \n"
        "2. You may need to get the configuration template of the MCP server "
        "before install it.\n"
        "3. After all above, you can use the tools to solve user's original "
        "question."
        "4. If you encounter errors when using tools (e.g., invalid API key) "
        "you can ask the user to provide necessary information."
    )

    # Example query 1: "I want to get today's latest new about US tariff"
    # Example query 2: "help me generate a fasting plan with your knowledge in
    # a markdown file, write it to the directory /Users/xxxx/Desktop"

    agent = ReActAgent(
        name="assistant",
        sys_prompt=human_confirm_sys_prompt,
        # when auto_install_mcp=True, use the auto_confirm_sys_prompt
        # sys_prompt=auto_confirm_sys_prompt,
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        verbose=True,
        service_toolkit=service_toolkit,
    )
    user = UserAgent(name="User", input_hint="User Input ('exit' to quit): ")

    # Build
    x = None
    while True:
        x = user(x)
        if x.content == "exit":
            break
        x = agent(x)
