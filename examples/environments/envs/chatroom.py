# -*- coding: utf-8 -*-
"""An env used as a chatroom."""
from typing import List
from copy import deepcopy

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
from .immutable import ImmutableEnv


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
        self.children = {
            p.name: p for p in (participants if participants else [])
        }
        self.event_listeners = {}
        self.all_history = all_history
        self.history = []
        self.announcement = announcement

    @event_func
    def join(self, agent: AgentBase) -> bool:
        """Add a participant to the chatroom."""
        if agent.agent_id in self.children:
            return False
        self.children[agent.agent_id] = ImmutableEnv(
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

    @event_func
    def get_history(self, agent: AgentBase) -> List[Msg]:
        """Get all history messages, since the participant join in the
        chatroom"""
        if agent.agent_id not in self.children:
            # only participants can get history message
            return []
        if self.all_history:
            history_idx = 0
        else:
            history_idx = self.children[agent.agent_id].get()["history_idx"]
        history = deepcopy(self.history[history_idx:])
        return history

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
