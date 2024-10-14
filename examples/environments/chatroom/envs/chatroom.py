# -*- coding: utf-8 -*-
"""An env used as a chatroom."""
from typing import List, Any, Union, Generator, Tuple, Optional
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


CHATROOM_TEMPLATE = """
======= CHATROOM BEGIN ========

## ANNOUNCEMENT:
{announcement}

## HISTORY:
{history}

======= CHATROOM END ========
"""


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

    def chat_freely(
        self,
        delay: float = 5,
        interval: float = 3,
        max_round: int = 10,
    ) -> None:
        """Let the agent chat freely"""
        sleep_time = random.random() * delay
        time.sleep(sleep_time)
        for _ in range(max_round):
            msg = self._agent()
            if "goodbye" in msg.content.lower():
                break
            time.sleep(interval)

    def chat(self) -> None:
        """call the agent to chat"""
        self._agent()


class ChatRoom(BasicEnv):
    """A chatroom env."""

    def __init__(
        self,
        name: str = None,
        announcement: Msg = None,
        participants: List[AgentBase] = None,
        all_history: bool = False,
        use_mention: bool = True,
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
            use_mention (`bool`): If `True`, the agent can mention other
            agents by @name. Default to `True`.
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
        if use_mention:
            self.add_listener(
                "speak",
                listener=Notifier(),
            )
        self.history = []
        self.announcement = announcement

    @event_func
    def join(self, agent: AgentBase) -> bool:
        """Add a participant to the chatroom."""
        if agent.name in self.children:
            return False
        self.children[agent.name] = ChatRoomMember(
            name=agent.name,
            agent=agent,
            history_idx=len(self.history),
        )
        self.add_listener("speak", Notifier())
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
    def get_history(self, agent_name: str) -> List[Msg]:
        """Get all history messages, since the participant join in the
        chatroom"""
        if agent_name not in self.children:
            # only participants can get history message
            return []
        if self.all_history:
            history_idx = 0
        else:
            history_idx = self.children[agent_name].history_idx
        return deepcopy(self.history[history_idx:])

    def describe(self, agent_name: str, **kwargs: Any) -> str:
        """Get the description of the chatroom."""
        ann = self.announcement if self.announcement else "EMPTY"
        history = "\n\n".join(
            [
                f"{msg.name}: {msg.content}"
                for msg in self.get_history(agent_name)
            ],
        )
        return CHATROOM_TEMPLATE.format(
            announcement=ann,
            history=history,
        )

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

    def chat_freely(
        self,
        delay: float = 1,
        interval: float = 5,
        max_round: int = 10,
    ) -> None:
        """Let all agents to chat freely without any preset order"""
        tasks = []
        for agent_name in self.children.keys():
            task = threading.Thread(
                target=self.children[agent_name].chat_freely,
                kwargs={
                    "delay": delay,
                    "interval": interval,
                    "max_round": max_round,
                },
            )
            tasks.append(task)
            task.start()
        for task in tasks:
            task.join()

    def chat_in_sequence(self, agent_name_order: List[str] = None) -> None:
        """Let all agents to chat in a sequence

        Args:
            sequence (`List[str]`): Order of speakers' names.
        """
        for agent_name in agent_name_order:
            self.children[agent_name].chat()


class Notifier(EventListener):
    """A listener that will call the mentioned agent"""

    def __init__(
        self,
    ) -> None:
        super().__init__(name="mentioned_notifier")
        self.pattern = re.compile(r"(?<=@)\w+")

    def __call__(self, room: Env, event: Event) -> None:
        names = self.pattern.findall(str(event.args["message"].content))

        for name in names:
            if name in room.children:
                logger.info(
                    f"{event.args['message'].name} mentioned {name}.",
                )
                room.children[name].agent.add_mentioned_message(
                    event.args["message"],
                )


class ChatRoomAgent(AgentBase):
    """
    An agent in a chatroom.
    """

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

    def _is_mentioned(self) -> bool:
        """Check whether the agent is mentioned"""
        return bool(self.mentioned_messages)

    def _generate_mentioned_prompt(self) -> Tuple[bool, str]:
        """Generate a hint for the agent"""
        with self.mentioned_messages_lock:
            if len(self.mentioned_messages) > 0:
                hint = "You have been mentioned in the following messages:\n"
                hint += "\n".join(
                    [
                        f"{msg.name}: {msg.content}"
                        for msg in self.mentioned_messages
                    ],
                )
                return True, hint
            return False, ""

    def _want_to_speak(self, hint: str) -> bool:
        """Check whether the agent want to speak currently"""
        prompt = self.model.format(
            Msg(name="system", role="system", content=hint),
            Msg(
                name="user",
                role="user",
                content="Based on the CHATROOM."
                " Do you want to speak in the chatroom now?\n"
                "Speak yes or no.",
            ),
        )
        response = self.model(
            prompt,
            max_retries=3,
        ).text
        speak = "yes" in response.lower()
        logger.debug(f"[SPEAK OR NOT] {self.name}: {response}")
        return speak

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
        room_info = self.room.describe(self.name)
        system_hint = (
            f"{self.sys_prompt}\n\nYou are participating in a chatroom.\n"
            f"\n{room_info}"
        )
        mentioned, mentioned_hint = self._generate_mentioned_prompt()
        if mentioned:
            # if mentioned, response directly
            prompt = self.model.format(
                Msg(
                    name="system",
                    role="system",
                    content=system_hint,
                ),
                Msg(
                    name="user",
                    role="user",
                    content=mentioned_hint,
                ),
            )
        else:
            # decide whether to speak
            if self._want_to_speak(room_info):
                prompt = self.model.format(
                    Msg(
                        name="system",
                        role="system",
                        content=system_hint,
                    ),
                    Msg(
                        name="user",
                        role="user",
                        content="Please generate a response based on the "
                        "CHATROOM.",
                    ),
                )
            else:
                return Msg(name="assistant", role="assistant", content="")
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
            msg_hint = self._generate_mentioned_prompt()
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
