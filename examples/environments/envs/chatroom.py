# -*- coding: utf-8 -*-
"""An env used as a chatroom."""
from typing import List, Any, Union, Mapping
from copy import deepcopy
import asyncio
import re
from loguru import logger

from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.exception import (
    EnvListenerError,
)
from agentscope.environment import (
    Env,
    BasicEnv,
    EventListener,
    Event,
    event_func,
)
from agentscope.models import ModelResponse
from .immutable import ImmutableEnv


class ChatRoomAgentEnv(ImmutableEnv):
    """An immutable env that can be get and set."""

    def __init__(
        self,
        name: str,
        value: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Env] = None,
        parent: Env = None,
    ) -> None:
        super().__init__(
            name=name,
            listeners=listeners,
            children=children,
            parent=parent,
            value=value,
        )

    @property
    def history_idx(self) -> int:
        return self._value['history_idx']

    @property
    def agent_name(self) -> str:
        return self._value['agent'].name

    async def chatting(self, delay: int = 1):
        await asyncio.sleep(delay)
        while True:
            msg = self._value['agent'](Msg(name="user", content="", role="user"))
            if 'goodbye' in msg.content.lower():
                break
            await asyncio.sleep(5)


class ChatRoom(BasicEnv):
    """A chatroom env."""

    def __init__(
        self,
        name: str = None,
        announcement: Msg = None,
        participants: List[AgentBase] = None,
        all_history: bool = False,
    ) -> None:
        """Init a ChatRoom instance.

        Args:
            name (`str`): The name of the chatroom.
            announcement (`Msg`): The announcement message.
            participants (`List[AgentBase]`): A list of agents
            all_history (`bool`): If `True`, new participant can see all
            history messages, else only messages generated after joining
            can be seen. Default to `False`.
        """
        super().__init__(
            name=name,
        )
        self.children = {}
        for p in (participants if participants else []):
            self.join(p)
        self.event_listeners = {}
        self.all_history = all_history
        self.history = []
        self.announcement = announcement

    @event_func
    def join(self, agent: AgentBase) -> bool:
        """Add a participant to the chatroom."""
        if agent.agent_id in self.children:
            return False
        self.children[agent.agent_id] = ChatRoomAgentEnv(
            name=agent.agent_id,
            value={
                "history_idx": len(self.history),
                "agent": agent,
            },
        )
        return True

    @event_func
    def leave(self, agent: AgentBase) -> bool:
        """Remove the participant agent from the chatroom."""
        if agent.agent_id not in self.children:
            return False
        del self.children[agent.agent_id]
        return True

    @event_func
    def speak(self, message: Msg) -> None:
        """Speak a message in the chatroom."""
        self.history.append(message)
        logger.debug(f'id(self) = {id(self)}, len(history) = {len(self.history)}')

    @event_func
    def get_history(self, agent_id: str) -> List[Msg]:
        """Get all history messages, since the participant join in the
        chatroom"""
        if agent_id not in self.children:
            # only participants can get history message
            return []
        if self.all_history:
            history_idx = 0
        else:
            history_idx = self.children[agent_id].history_idx
        logger.debug(f'id(self) = {id(self)}, hisotry_idx = {history_idx}, len(self.history) = {len(self.history)}')
        return deepcopy(self.history[history_idx:])

    @event_func
    def set_announcement(self, announcement: Msg) -> None:
        """Set the announcement of the chatroom."""
        self.announcement = announcement

    @event_func
    def get_announcement(self) -> Msg:
        """Get the announcement of the chatroom."""
        return deepcopy(self.announcement)

    # Syntaic sugar, not an event function
    def listen_to(
        self,
        target_names: List[str],
        listener: EventListener,
    ) -> None:
        """The listener will be called when a message whose name is in
        `target_names` is send to the chatroom."""
        if target_names is None or len(target_names) == 0:
            return

        class ListenTo(EventListener):
            """A middleware that activates `target_listener`"""

            def __init__(
                self,
                name: str,
                target_names: List[str],
                target_listener: EventListener,
            ) -> None:
                super().__init__(name=name)
                self.target_names = target_names
                self.target_listener = target_listener

            def __call__(self, env: Env, event: Event) -> None:
                if event.args["message"].name in self.target_names:
                    self.target_listener(env, event)

        if not self.add_listener(
            "speak",
            listener=ListenTo(
                name=f"listen_to_{listener.name}",
                target_names=target_names,
                target_listener=listener,
            ),
        ):
            raise EnvListenerError("Fail to add listener.")

    def chatting_parse_func(self, response: ModelResponse) -> ModelResponse:
        pattern_str = ""
        for child in self.children.values():
            if pattern_str:
                pattern_str += "|"
            pattern_str += rf"""\s{child.agent_name}: """
        pattern = re.compile(pattern_str, re.DOTALL)
        logger.debug(response.text)
        texts = [s.strip() for s in pattern.split(response.text) if s.strip()]
        logger.debug(texts)
        return ModelResponse(text=texts[0])

    def chatting(self, delay: Union[int, Mapping[str, int]] = 1):
        async def start_chatting():
            tasks = []
            for agent_id, child in self.children.items():
                if isinstance(delay, int):
                    tasks.append(asyncio.create_task(child.chatting(delay=delay)))
                else:
                    tasks.append(asyncio.create_task(child.chatting(delay=delay[agent_id])))
            await asyncio.gather(*tasks)
        asyncio.run(start_chatting())


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
        logger.debug(f'id(room) = {id(room)}')
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
        logger.debug(prompt)
        response = self.model(
            prompt,
            parse_func=self.room.chatting_parse_func,
            max_retries=3,
        ).text
        msg = Msg(name=self.name, content=response, role="assistant")
        self.speak(msg)
        self.room.speak(msg)
        return msg
