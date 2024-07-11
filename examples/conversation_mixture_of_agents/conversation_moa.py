# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""
Implementation of paper [MoA](https://github.com/togethercomputer/MoA).
Here is a simple example for conversation with MoA in Agentscope.
"""
import argparse
from loguru import logger

import agentscope
from agentscope.agents.user_agent import UserAgent
from agentscope.utils.mixture_of_agent import MixtureOfAgents


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--show_internal",
        action="store_true",
        help="Whether to show the internal messages in MoA. Default is False.",
    )
    parser.add_argument(
        "--multi_turn",
        action="store_true",
        help="Enables multi-turn interaction, allowing the conversation to build context over multiple exchanges. When True, the system maintains context and builds upon previous interactions. Default is False. When False, the system generates responses independently for each input.",  # noqa
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="Number of layers of MoA. Default is 1. Can be set to 0",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # fill you api keys, or host local models using vllm or ollama.
    model_configs = [
        {
            "config_name": "qwen-max",
            "model_type": "dashscope_chat",
            "model_name": "qwen-max",
            "api_key": "{your_api_key}",
            "generate_args": {
                "temperature": 0.7,
            },
        },
        {
            "config_name": "gemini-pro",
            "model_type": "gemini_chat",
            "model_name": "gemini-pro",
            "api_key": "{your_api_key}",
        },
        {
            "config_name": "gpt-4",
            "model_type": "openai_chat",
            "model_name": "gpt-4",
            "api_key": "{your_api_key}",
            "client_args": {
                "max_retries": 3,
            },
            "generate_args": {
                "temperature": 0.7,
            },
        },
    ]

    agentscope.init(model_configs=model_configs, project="Mixture of Agents")

    if args.multi_turn:
        history = []
    user_agent = UserAgent(name="user")

    moa_module = MixtureOfAgents(
        main_model="qwen-max",
        reference_models=["gpt-4", "qwen-max", "gemini-pro"],
        show_internal=args.show_internal,
        rounds=args.rounds,
    )

    x = user_agent(None)
    while True:
        if x.content == "exit":  # type "exit" to break the loop
            break
        if args.multi_turn:
            history.append(x)
            x = moa_module.reply(history)
            history.append(x)
        else:
            x = moa_module.reply(x)
        logger.chat(x)
        x = user_agent(x)
