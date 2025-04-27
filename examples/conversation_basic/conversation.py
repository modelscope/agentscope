# -*- coding: utf-8 -*-
"""A simple example for conversation between user and assistant agent."""
import agentscope
from agentscope.agents import (
    DialogAgent,
    UserAgent,
)
from agentscope.pipelines import sequential_pipeline

YOUR_MODEL_CONFIGURATION_NAME = "{YOUR_MODEL_CONFIGURATION_NAME}"
YOUR_MODEL_CONFIGURATION = [
    {
        "model_type": "openai_chat",
        "config_name": YOUR_MODEL_CONFIGURATION_NAME,
        "model_name": "gpt-4o",
        "api_key": "sk-fda3f93bf6294bfdb31b5b5809526b9c",
        "stream": False,
        "client_args": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        },
    },
]


def main() -> None:
    """A basic conversation demo"""

    agentscope.init(
        model_configs=YOUR_MODEL_CONFIGURATION,
        project="Multi-Agent Conversation",
        save_api_invoke=True,
        # studio_url="http://localhost:3000",
    )

    # Init two agents
    dialog_agent = DialogAgent(
        name="Assistant",
        sys_prompt="You're a helpful assistant.",
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
    )
    user_agent = UserAgent()

    # start the conversation between user and assistant
    x = None
    while x is None or x.content != "exit":
        x = sequential_pipeline([user_agent, dialog_agent], x)


if __name__ == "__main__":
    main()
