from typing import Any
import asyncio
import re
from pprint import pprint
from loguru import logger

import agentscope
from agentscope.environment import (
    Env,
    RpcEnv,
    Event,
    EventListener,
)
from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.models import ModelResponse

from envs.chatroom import ChatRoom


pattern = re.compile(r"""\s\w*: """, re.DOTALL)
def parse_func(response: ModelResponse) -> ModelResponse:
    texts = [s.strip() for s in pattern.split(response.text) if s.strip()]
    return ModelResponse(text=texts[0])


class AgentWithChatRoom(AgentBase):
    """A agent with chat room"""

    def __init__(  # pylint: disable=W0613
        self,
        name: str,
        sys_prompt: str,
        model_config_name: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name)
        self.room = None
        self.mentioned_messages = []

    def add_mentioned_listener(self, room: ChatRoom) -> None:
        class Mentioned(EventListener):
            def __init__(
                self,
                agent: AgentBase,
            ) -> None:
                super().__init__(name=f'mentioned_agent_{agent.name}')
                self.agent = agent
                self.pattern = re.compile(r"""(?<=@)\w*""", re.DOTALL)

            def __call__(self, env: Env, event: Event) -> None:
                find_result = self.pattern.findall(event.args["message"].content)
                if self.agent.name in find_result:
                    logger.info(f"{event.args['message'].name} mentioned {self.agent.name}.")
                    self.agent.mentioned_messages.append(event.args["message"])
        room.add_listener("speak", Mentioned(self))

    def join(self, room: ChatRoom) -> bool:
        """Join a room"""
        self.room = room
        self.add_mentioned_listener(room)
        return room.join(self)

    def generate_hint(self) -> Msg:
        if self.mentioned_messages:
            hint = self.sys_prompt + r"""\n\nYou have be mentioned in the following message, please generate an appropriate response."""
            for message in self.mentioned_messages:
                hint += f"\n{message.name}: " + message.content
            self.mentioned_messages = []
            return Msg("system", hint, role="system")
        else:
            return Msg("system", self.sys_prompt, role="system")

    def reply(self, x: Msg = None) -> Msg:
        msg_hint = self.generate_hint()
        self_msg = Msg(name=self.name, content=f"", role="assistant")

        history = self.room.get_history(self.agent_id)
        prompt = self.model.format(
            msg_hint,
            history,
            self_msg,
        )
        response = self.model(
            prompt,
            parse_func=parse_func,
            max_retries=3,
        ).text
        msg = Msg(name=self.name, content=response, role="assistant")
        self.speak(msg)
        self.room.speak(msg)
        return msg

    def get_event(self, idx: int) -> Event:
        """Get the specific event."""
        return self.event_list[idx]


async def chatting(agent: AgentWithChatRoom, delay: int = 1):
    await asyncio.sleep(delay)
    while True:
        msg = agent(Msg(name="user", content="", role="user"))
        if 'goodbye' in msg.content.lower():
            break
        await asyncio.sleep(5)

def main():
    # Prepare the model configuration
    YOUR_MODEL_CONFIGURATION_NAME = "{YOUR_MODEL_CONFIGURATION_NAME}"
    YOUR_MODEL_CONFIGURATION = {
        "config_name": YOUR_MODEL_CONFIGURATION_NAME,
        # ...
    }

    # Initialize the agents
    agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION, use_monitor=False)

    ann = Msg(name="Boss", content="This is a game development work group, please discuss how to develop an open world game.", role="system")
    r = ChatRoom(name="chat", announcement=ann)

    alice = AgentWithChatRoom(
        name="Alice", 
        sys_prompt=r"""You are a game art designer named Alice. Programmer Bob and game planner Carol are your colleagues, and you need to collaborate with them to complete an open world game. """
        r"""Please ask appropriate question to planner or generate appropriate responses in this work group based on the following chat history. """
        r"""When you need to mention someone, you can use @ to remind them. """
        r"""You only need to output Alice's possible replies, without giving anyone else's replies or continuing the conversation. """
        r"""When the discussion is complete, you need to reply with a message containing 'Goodbye' to indicate exiting the conversation.""", # Game Art Designer
        model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
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
    )
    carol.join(r)
    async def start_chatting():
        tasks = [
            asyncio.create_task(chatting(carol, delay=0)),
            asyncio.create_task(chatting(alice, delay=5)),
            asyncio.create_task(chatting(bob, delay=7)),
        ]
        await asyncio.gather(*tasks)
    asyncio.run(start_chatting())

if __name__ == '__main__':
    main()
