# -*- coding: utf-8 -*-
"""
A simple example for conversation between user and
an agent with RAG capability.
"""
import os

import agentscope
from agentscope.agents import UserAgent
from agentscope.message import Msg


def main() -> None:
    """A RAG multi-agent demo"""
    agents = agentscope.init(
        model_configs=[
            {
                "model_type": "dashscope_chat",
                "config_name": "qwen_config",
                "model_name": "qwen-max",
                "api_key": f"{os.environ.get('DASHSCOPE_API_KEY')}",
            },
            {
                "model_type": "dashscope_text_embedding",
                "config_name": "qwen_emb_config",
                "model_name": "text-embedding-v2",
                "api_key": f"{os.environ.get('DASHSCOPE_API_KEY')}",
            },
        ],
        agent_configs="./agent_config.json",
    )

    tutorial_agent, code_explain_agent, summarize_agent = agents

    user_agent = UserAgent()
    # start the conversation between user and assistant
    while True:
        x = user_agent()
        x.role = "user"  # to enforce dashscope requirement on roles
        if len(x["content"]) == 0 or str(x["content"]).startswith("exit"):
            break
        tutorial_response = tutorial_agent(x)
        code_explain = code_explain_agent(x)
        msg = Msg(
            name="user",
            role="user",
            content=tutorial_response["content"]
            + "\n"
            + code_explain["content"]
            + "\n"
            + x["content"],
        )
        summarize_agent(msg)


if __name__ == "__main__":
    main()
