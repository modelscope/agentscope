# -*- coding: utf-8 -*-
"""An env used as a chatroom."""
from typing import List, Any, Union, Mapping, Generator, Tuple, Optional
from copy import deepcopy
import re
import random
import threading
import time
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
from agentscope.studio._client import _studio_client
from agentscope.web.gradio.utils import user_input


class ChatRoomMember(BasicEnv):
    """A member of chatroom."""

    def __init__(
        self,
        name: str,
        agent: AgentBase,
        history_idx: int = 0,
    ) -> None:
        super().__init__(name)
        self._agent = agent
        self._history_idx = history_idx

    @property
    def agent_name(self) -> str:
        """Get the name of the agent."""
        return self._agent.name

    @property
    def history_idx(self) -> int:
        """Get the history index of the agent."""
        return self._history_idx

    @property
    def agent(self) -> AgentBase:
        """Get the agent of the member."""
        return self._agent

    def chatting(self, delay: int = 1) -> None:
        """Make the agent chatting in the chatroom."""
        time.sleep(delay)
        while True:
            msg = self._agent()
            if "goodbye" in msg.content.lower():
                break
            sleep_time = random.randint(1, 5)
            time.sleep(sleep_time)


class ChatRoom(BasicEnv):
    """A chatroom env."""

    def __init__(
        self,
        name: str = None,
        announcement: Msg = None,
        participants: List[AgentBase] = None,
        all_history: bool = False,
        **kwargs: Any,
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
            **kwargs,
        )
        self.children = {}
        for p in participants if participants else []:
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
        self.children[agent.agent_id] = ChatRoomMember(
            name=agent.agent_id,
            agent=agent,
            history_idx=len(self.history),
        )
        self.add_listener("speak", Mentioned(agent))
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
        """Parse the response of the chatting agent."""
        pattern_str = ""
        for child in self.children.values():
            if pattern_str:
                pattern_str += "|"
            pattern_str += rf"""\s?{child.agent_name}: """
        pattern = re.compile(pattern_str, re.DOTALL)
        logger.debug(repr(pattern_str))
        logger.debug(response.text)
        texts = [s.strip() for s in pattern.split(response.text)]
        logger.debug(texts)
        return ModelResponse(text=texts[0])

    def chatting(self, delay: Union[int, Mapping[str, int]] = 1) -> None:
        """Make all agents chatting in the chatroom."""
        tasks = []
        for agent_id, child in self.children.items():
            if isinstance(delay, int):
                tasks.append(
                    threading.Thread(target=child.chatting, args=(delay,)),
                )
            else:
                if agent_id not in delay:
                    continue
                tasks.append(
                    threading.Thread(
                        target=child.chatting,
                        args=(delay[agent_id],),
                    ),
                )
        for task in tasks:
            task.start()
        for task in tasks:
            task.join()


class Mentioned(EventListener):
    """A listener that will be called when a message is mentioned the agent"""

    def __init__(
        self,
        agent: AgentBase,
    ) -> None:
        super().__init__(name=f"mentioned_agent_{agent.name}")
        self.agent = agent
        self.pattern = re.compile(r"""(?<=@)\w*""", re.DOTALL)

    def __call__(self, env: Env, event: Event) -> None:
        find_result = self.pattern.findall(str(event.args["message"].content))
        if self.agent.name in find_result:
            logger.info(
                f"{event.args['message'].name} mentioned {self.agent.name}.",
            )
            self.agent.add_mentioned_message(event.args["message"])


class ChatRoomAgent(AgentBase):
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
            model_config_name=model_config_name,
        )
        self.room = None
        self.mentioned_messages = []
        self.mentioned_messages_lock = threading.Lock()

    def add_mentioned_message(self, msg: Msg) -> None:
        """Add mentioned messages"""
        with self.mentioned_messages_lock:
            self.mentioned_messages.append(msg)

    def join(self, room: ChatRoom) -> bool:
        """Join a room"""
        self.room = room
        return room.join(self)

    def generate_hint(self) -> Msg:
        """Generate a hint for the agent"""
        if self.mentioned_messages:
            hint = (
                self.sys_prompt
                + r"""\n\nYou have be mentioned in the following message, """
                r"""please generate an appropriate response."""
            )
            for message in self.mentioned_messages:
                hint += f"\n{message.name}: " + message.content
            self.mentioned_messages = []
            return Msg("system", hint, role="system")
        else:
            return Msg("system", self.sys_prompt, role="system")

    def speak(
        self,
        content: Union[str, Msg, Generator[Tuple[bool, str], None, None]],
    ) -> None:
        """Speak to room.

        Args:
            content
            (`Union[str, Msg, Generator[Tuple[bool, str], None, None]]`):
                The content of the message to be spoken in chatroom.
        """
        super().speak(content)
        self.room.speak(content)

    def reply(self, x: Msg = None) -> Msg:
        """Generate reply to chat room"""
        msg_hint = self.generate_hint()
        self_msg = Msg(name=self.name, content="", role="assistant")

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
        if response:
            self.speak(msg)
        return msg


class ChatRoomAgentWithAssistant(ChatRoomAgent):
    """A ChatRoomAgent with assistant"""

    def __init__(
        self,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.timeout = timeout

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
                timeout=self.timeout,
            )

            logger.info("Python: receive ", raw_input)
            if raw_input is None:
                content = None
            else:
                content = raw_input["content"]
        else:
            time.sleep(0.5)
            try:
                content = user_input(timeout=self.timeout)
            except TimeoutError:
                content = None

        if content is not None:  # user input
            response = content
        else:  # assistant reply
            msg_hint = self.generate_hint()
            self_msg = Msg(name=self.name, content="", role="assistant")

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
            if not response.startswith("[auto reply]"):
                response = "[auto reply] " + response
        msg = Msg(name=self.name, content=response, role="user")
        self.speak(msg)
        return msg
