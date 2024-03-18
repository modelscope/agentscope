# -*- coding: utf-8 -*-
"""
A simple example for conversation between user and
a agent with RAG capability.
"""
import os
from rag_agents import LlamaIndexAgent
import agentscope
from agentscope.agents import UserAgent


def main() -> None:
    """A conversation demo"""

    agentscope.init(
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
    )

    # Init two agents
    rag_agent = LlamaIndexAgent(
        name="Assistant",
        sys_prompt="You're a helpful assistant. You need to generate answers "
        "based on the provided context:\n "
        "Context: \n {retrieved_context}\n ",
        model_config_name="qwen_config",  # replace by your model config name
        emb_model_config_name="qwen_emb_config",
    )
    user_agent = UserAgent()
    # start the conversation between user and assistant
    x = user_agent()
    x.role = "user"  # to enforce dashscope requirement on roles
    rag_agent(x)


if __name__ == "__main__":
    main()
