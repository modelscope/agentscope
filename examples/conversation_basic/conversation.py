# -*- coding: utf-8 -*-
"""A simple example for conversation between user and assistant agent."""
import agentscope
from agentscope.agents import DialogAgent
from agentscope.agents.user_agent import UserAgent
from agentscope.pipelines.functional import sequentialpipeline


def main() -> None:
    """A basic conversation demo"""

    agentscope.init(
        model_configs=[
        {
            "model_type": "dashscope_chat",
            "config_name": "qwen",

            "model_name": "qwen-max",
            "api_key": "sk-1419b0a223f442fcb7b7c137a411cca6"
        },
        {
            "model_type": "post_api_chat",
            "config_name": "gpt-4",

            "api_url": "https://api.mit-spider.alibaba-inc.com/chatgpt/api/ask",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjIyNTE4NiIsInBhc3N3b3JkIjoiMjI1MTg2IiwiZXhwIjoyMDA2OTMzNTY1fQ.wHKJ7AdJ22yPLD_-1UHhXek4b7uQ0Bxhj_kJjjK0lRM"
            },
            "json_args": {
                "model": "gpt-4",
                "temperature": 0.0,
            },
            "messages_key": "messages"
        },
        {
            "model_type": "ollama_chat",
            "config_name": "ollama",

            "model_name": "llama2",
        },
    ],
        studio_url="http://127.0.0.1:5000"
    )

    # Init two agents
    dialog_agent = DialogAgent(
        name="Assistant",
        sys_prompt="You're a helpful assistant.",
        model_config_name="gpt-4",  # replace by your model config name
    )
    user_agent = UserAgent()

    # start the conversation between user and assistant
    x = None
    while x is None or x.content != "exit":
        x = sequentialpipeline([dialog_agent, user_agent], x)


if __name__ == "__main__":
    main()
