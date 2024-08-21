import os
import argparse
import time
from loguru import logger

import agentscope
from agentscope.message import Msg
from agentscope.studio._client import _studio_client
from agentscope.web.gradio.utils import user_input

from envs.chatroom import ChatRoom, ChatRoomAgent


class ChatRoomAgentWithAssistant(ChatRoomAgent):
    def reply(self, x: Msg = None) -> Msg:
        if _studio_client.active:
            logger.info(
                f"Waiting for input from:\n\n"
                f"    * {_studio_client.get_run_detail_page_url()}\n",
            )
            raw_input = _studio_client.get_user_input(
                agent_id=self.agent_id,
                name=self.name,
                require_url=False,
                required_keys=None,
            )

            print("Python: receive ", raw_input)
            content = raw_input["content"]
        else:
            time.sleep(0.5)
            content = user_input(timeout=None)

        if content != '[assistant]':
            response = content
        else:
            msg_hint = self.generate_hint()
            self_msg = Msg(name=self.name, content=f"", role="assistant")

            history = self.room.get_history(self.agent_id)
            prompt = self.model.format(
                msg_hint,
                history,
                self_msg,
            )
            logger.debug(prompt)
            response = self.model(
                prompt,
                parse_func=self.room.chatting_parse_func,
                max_retries=3,
            ).text
            if not response.startswith('[assistant]'):
                response = '[assistant] ' + response
        msg = Msg(name=self.name, content=response, role="user")
        self.speak(msg)
        return msg


def parse_args() -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--logger-level",
        choices=['DEBUG', 'INFO'],
        default="INFO",
    )
    parser.add_argument(
        "--use-dist",
        action="store_true",
    )
    parser.add_argument(
        '--studio-url',
        default=None,
        type=str,
    )
    return parser.parse_args()

def main(args):
    # Prepare the model configuration
    YOUR_MODEL_CONFIGURATION_NAME = "dash"
    YOUR_MODEL_CONFIGURATION = [{"model_type": "dashscope_chat", "config_name": "dash", "model_name": "qwen-turbo", "api_key": os.environ.get('DASH_API_KEY', '')}]

    # Initialize the agents
    agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION, use_monitor=False, logger_level=args.logger_level, studio_url=args.studio_url)

    ann = Msg(name="Boss", content="This is a game development work group, please discuss how to develop an open world game.", role="system")
    r = ChatRoom(name="chat", announcement=ann, to_dist=args.use_dist)

    # Setup the persona of Alice, Bob and Carol
    alice = ChatRoomAgent(
        name="Alice", 
        sys_prompt=r"""""",
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    alice.join(r)

    bob = ChatRoomAgentWithAssistant(
        name="Bob",
        sys_prompt=r"""You are Bob's chat room assistant and he is currently unable to reply to messages. """
        r"""Please generate a suitable response based on the following chat history. """
        r"""The content you reply to must be based on the chat history. Please refuse to reply to questions that are beyond the scope of the chat history.""",
        # r"""Your reply must have appeared in the chat history. If you are unable to reply, please refuse to reply.""",
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    bob.join(r)

    # Setup some chatting history
    alice.speak(Msg(name="Alice", content="Hi Bob, nice to meet you. Can you tell me a bit about yourself?", role="assistant"))
    bob.speak(Msg(name="Bob", content="Of course, nice to meet you too, Alice. I'm originally from Hunan, a beautiful province in southern China known for its spicy food and stunning natural scenery.", role="user"))
    alice.speak(Msg(name="Alice", content="Oh, that sounds fascinating! So, what do you do for a living, Bob?", role="assistant"))
    bob.speak(Msg(name="Bob", content="I work as a software engineer. I've been in this field for about 5 years now, designing and developing various applications and systems. It's a challenging but rewarding job that keeps me on my toes.", role="user"))
    alice.speak(Msg(name="Alice", content="That's great! It takes a lot of skill and creativity to be a good software engineer. Speaking of creativity, do you have any hobbies or activities you enjoy outside of work?", role="assistant"))
    bob.speak(Msg(name="Bob", content="Yes, I'm quite passionate about playing board games. There's something really enjoyable about the strategy, competition, and social interaction they provide. Whether it's classic games like chess or more modern ones like Settlers of Catan, I find them all very engaging.", role="user"))
    alice.speak(Msg(name="Alice", content="Board games are a wonderful way to unwind and connect with friends and family. It sounds like you have a great balance between your professional and personal life, Bob. Thanks for sharing!", role="assistant"))
    bob.speak(Msg(name="Bob", content="Absolutely, thank you for asking, Alice. It was a pleasure chatting with you.", role="user"))

    carol = ChatRoomAgent(
        name="Carol",
        sys_prompt=r"""You are Carol, and now you need to interview Bob. Just ask him where he is from, which school he graduated from, his profession, and his hobbies. """
        r"""At the end of the interview, please output a reply containing Goodbye to indicate the end of the conversation.""",
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
        to_dist=args.use_dist,
    )
    carol.join(r)

    # Start the chat
    r.chatting(delay={carol._agent_id: 0, bob._agent_id: 5})


if __name__ == '__main__':
    args = parse_args()
    main(args)
