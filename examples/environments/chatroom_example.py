import os
import argparse

import agentscope
from agentscope.message import Msg
from agentscope.logging import LOG_LEVEL

from envs.chatroom import ChatRoom, AgentWithChatRoom


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--logger-level",
        choices=LOG_LEVEL,
        default="INFO",
    )
    parser.add_argument(
        "--use-dist",
        action="store_true",
    )
    return parser.parse_args()

def main(args):
    # Prepare the model configuration
    YOUR_MODEL_CONFIGURATION_NAME = "dash"
    YOUR_MODEL_CONFIGURATION = [{"model_type": "dashscope_chat", "config_name": "dash", "model_name": "qwen-turbo", "api_key": os.environ.get('DASH_API_KEY', '')}]

    # Initialize the agents
    agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION, use_monitor=False, logger_level=args.logger_level)

    ann = Msg(name="Boss", content="This is a game development work group, please discuss how to develop an open world game.", role="system")
    r = ChatRoom(name="chat", announcement=ann, to_dist=args.use_dist)

    # Setup the persona of Alice, Bob and Carol
    alice = AgentWithChatRoom(
        name="Alice", 
        sys_prompt=r"""You are a game art designer named Alice. Programmer Bob and game planner Carol are your colleagues, and you need to collaborate with them to complete an open world game. """
        r"""Please ask appropriate question to planner or generate appropriate responses in this work group based on the following chat history. """
        r"""When you need to mention someone, you can use @ to remind them. """
        r"""You only need to output Alice's possible replies, without giving anyone else's replies or continuing the conversation. """
        r"""When the discussion is complete, you need to reply with a message containing 'Goodbye' to indicate exiting the conversation.""", # Game Art Designer
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    alice.join(r)

    bob = AgentWithChatRoom(
        name="Bob",
        sys_prompt=r"""You are a game programmer named Bob. Art designer Alice and game planner Carol are your colleagues, and you need to collaborate with them to complete an open world game. """
        r"""Please ask appropriate questions or generate appropriate responses in the work group based on the following historical records. """
        r"""When you need to mention someone, you can use @ to remind them. """
        r"""You only need to output Bob's possible replies, without giving anyone else's replies or continuing the conversation. """
        r"""When the discussion is complete, you need to reply with a message containing 'Goodbye' to indicate exiting the conversation.""", # Game Programmer
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    bob.join(r)

    carol = AgentWithChatRoom(
        name="Carol",
        sys_prompt=r"""You are a game planner named Carol. Programmer Bob and art designer Alice are your colleagues, and you need to guide them in developing an open world game. """
        r"""Please generate a suitable response in this work group based on the following chat history. """
        r"""When you need to mention someone, you can use @ to remind them. """
        r"""You only need to output Carol's possible replies, without giving anyone else's replies or continuing the conversation. """
        r"""When the discussion is complete, you need to reply with a message containing 'Goodbye' to indicate exiting the conversation.""", # Game Designer
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    carol.join(r)

    # Start the chat
    r.chatting(delay={carol._agent_id: 0, alice._agent_id: 5, bob._agent_id:7})


if __name__ == '__main__':
    # TODO: add argparse and to dist
    args = parse_args()
    main(args)
