# -*- coding: utf-8 -*-
"""A simple example for conversation between user and assistant agent."""
import os
import json

from agent import MCPAgent

import agentscope
from agentscope.agents.user_agent import UserAgent
from agentscope.pipelines.functional import sequentialpipeline


def main() -> None:
    """A basic MCP conversation demo"""

    agentscope.init(
        model_configs=[
            {
                "model_type": "dashscope_chat",
                "config_name": "qwen",
                "model_name": "qwen-max",
                "api_key": os.getenv("DASHSCOPE_API_KEY"),
                "generate_args": {
                    "temperature": 0.5,
                },
            },
        ],
        project="Multi-Agent Conversation",
        save_api_invoke=True,
    )

    # TODO: make this happen in `agentscope.init`
    with open("mcp_servers_config.json", "r", encoding="utf-8") as f:
        server_configs = json.load(f)

    # Init two agents
    agent = MCPAgent(
        name="Assistant",
        model_config_name="qwen",  # replace by your model config name
        server_configs=server_configs,
    )

    user_agent = UserAgent()

    # start the conversation between user and assistant
    x = None
    while x is None or x.content != "exit":
        x = sequentialpipeline([agent, user_agent], x)

    # Clean up connections
    agent.cleanup_servers_sync()


if __name__ == "__main__":
    main()
