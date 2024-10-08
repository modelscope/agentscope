# -*- coding: utf-8 -*-
"""A simple example of chatroom with three agents."""

import os
import argparse

from envs.chatroom import ChatRoom, ChatRoomAgent

import agentscope
from agentscope.message import Msg


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--logger-level",
        choices=["DEBUG", "INFO"],
        default="INFO",
    )
    parser.add_argument(
        "--use-dist",
        action="store_true",
    )
    parser.add_argument(
        "--studio-url",
        default=None,
        type=str,
    )
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    """Example for chatroom"""
    # Prepare the model configuration
    YOUR_MODEL_CONFIGURATION_NAME = "dash"
    YOUR_MODEL_CONFIGURATION = [
        {
            "model_type": "dashscope_chat",
            "config_name": "dash",
            "model_name": "qwen-turbo",
            "api_key": os.environ.get("DASH_API_KEY", ""),
        },
    ]

    # Initialize the agents
    agentscope.init(
        model_configs=YOUR_MODEL_CONFIGURATION,
        use_monitor=False,
        logger_level=args.logger_level,
        studio_url=args.studio_url,
    )

    ann = Msg(
        name="Boss",
        content=(
            "This is a game development work group, "
            "please discuss how to develop an open world game."
        ),
        role="system",
    )
    r = ChatRoom(name="chat", announcement=ann, to_dist=args.use_dist)

    # Setup the persona of Alice, Bob and Carol
    alice = ChatRoomAgent(  # Game Art Designer
        name="Alice",
        sys_prompt=r"""You are a game art designer named Alice. """
        r"""Programmer Bob and game planner Carol are your colleagues, """
        r"""and you need to collaborate with them to complete an open """
        r"""world game. Please ask appropriate question to planner or """
        r"""generate appropriate responses in this work group based on """
        r"""the following chat history. When you need to mention someone, """
        r"""you can use @ to remind them. You only need to output Alice's """
        r"""possible replies, without giving anyone else's replies or """
        r"""continuing the conversation. When the discussion is complete, """
        r"""you need to reply with a message containing 'Goodbye' to """
        r"""indicate exiting the conversation.""",
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    alice.join(r)

    bob = ChatRoomAgent(  # Game Programmer
        name="Bob",
        sys_prompt=r"""You are a game programmer named Bob. """
        r"""Art designer Alice and game planner Carol are your colleagues, """
        r"""and you need to collaborate with them to complete an open """
        r"""world game. Please ask appropriate questions or generate """
        r"""appropriate responses in the work group based on the following """
        r"""historical records. When you need to mention someone, you can """
        r"""use @ to remind them. You only need to output Bob's possible """
        r"""replies, without giving anyone else's replies or continuing """
        r"""the conversation. When the discussion is complete, you need """
        r"""to reply with a message containing 'Goodbye' to indicate """
        r"""exiting the conversation.""",
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    bob.join(r)

    carol = ChatRoomAgent(  # Game Designer
        name="Carol",
        sys_prompt=r"""You are a game planner named Carol. """
        r"""Programmer Bob and art designer Alice are your colleagues, """
        r"""and you need to guide them in developing an open world game. """
        r"""Please generate a suitable response in this work group based """
        r"""on the following chat history. When you need to mention """
        r"""someone, you can use @ to remind them. You only need to output """
        r"""Carol's possible replies, without giving anyone else's replies """
        r"""or continuing the conversation. When the discussion is """
        r"""complete, you need to reply with a message containing """
        r"""'Goodbye' to indicate exiting the conversation.""",
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    carol.join(r)

    # Start the chat
    r.chatting(
        delay={carol.agent_id: 0, alice.agent_id: 5, bob.agent_id: 7},
    )


if __name__ == "__main__":
    main(parse_args())
