# -*- coding: utf-8 -*-
"""
A simple example for conversation between user and
an agent with RAG capability.
"""
import os
import argparse
from loguru import logger

from rag_agents import LlamaIndexAgent, LangChainRAGAgent
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

    if args.module == "llamaindex":
        AgentClass = LlamaIndexAgent
    else:
        AgentClass = LangChainRAGAgent
    rag_agent = AgentClass(
        name="Assistant",
        sys_prompt="You're a helpful assistant. You need to generate"
        " answers based on the provided context:\n "
        "Context: \n {retrieved_context}\n ",
        model_config_name="qwen_config",  # your model config name
        emb_model_config_name="qwen_emb_config",
        config={
            "data_path": args.data_path,
            "chunk_size": 2048,
            "chunk_overlap": 40,
            "similarity_top_k": 10,
        },
    )
    user_agent = UserAgent()
    # start the conversation between user and assistant
    while True:
        x = user_agent()
        x.role = "user"  # to enforce dashscope requirement on roles
        if len(x["content"]) == 0 or str(x["content"]).startswith("exit"):
            break
        rag_agent(x)


if __name__ == "__main__":
    # The default parameters can set a AgentScope consultant to
    # answer question about agentscope based on tutorial.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--module",
        choices=["llamaindex", "langchain"],
        default="llamaindex",
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default="../../docs/sphinx_doc/en/source/tutorial",
    )
    args = parser.parse_args()
    if args.module == "langchain":
        logger.warning(
            "LangChain RAG Chosen. May require install pandoc in advanced.",
            "For example, run ` brew install pandoc` on MacOS.",
        )
    main()
