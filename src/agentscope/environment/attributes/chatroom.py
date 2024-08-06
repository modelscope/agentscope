# -*- coding: utf-8 -*-
"""An attribute used as a chatroom."""
from typing import List
from copy import deepcopy

from ...agents import AgentBase
from ...message import Msg
from ...exception import (
    EnvListenerError,
)
from .immutable import ImmutableAttribute
from ..attribute import (
    Attribute,
    BasicAttribute,
    EventListener,
)
from ..event import event_func, Event


class ChatRoom(BasicAttribute):
    """A chatroom attribute."""

    def __init__(
        self,
        name: str = None,
        announcement: Msg = None,
        participants: List[AgentBase] = None,
    ) -> None:
        super().__init__(
            name=name,
            value={"history": [], "announcement": announcement},
        )
        self.children = {
            p.name: p for p in (participants if participants else [])
        }
        self.event_listeners = {}

    @event_func
    def join(self, agent: AgentBase) -> bool:
        """Add a participant to the chatroom."""
        if agent.agent_id in self.children:
            return False
        self.children[agent.agent_id] = ImmutableAttribute(
            name=agent.agent_id,
            value={
                "history_idx": len(self._value["history"]),
                "agent": agent,
            },
        )
        self._trigger_listener(Event("join", {"agent": agent}))
        return True

    @event_func
    def leave(self, agent: AgentBase) -> bool:
        """Remove the participant agent from the chatroom."""
        if agent.agent_id not in self.children:
            return False
        del self.children[agent.agent_id]
        self._trigger_listener(Event("leave", {"agent": agent}))
        return True

    @event_func
    def speak(self, message: Msg) -> None:
        """Speak a message in the chatroom."""
        self._value["history"].append(message)
        self._trigger_listener(Event("speak", {"message": message}))

    @event_func
    def get_history(self, agent: AgentBase) -> List[Msg]:
        """Get all history messages, since the participant join in the
        chatroom"""
        if agent.agent_id not in self.children:
            # only participants can get history message
            return []
        history_idx = self.children[agent.agent_id].get()["history_idx"]
        history = deepcopy(self._value["history"][history_idx:])
        self._trigger_listener(Event("get_history", {"agent": agent}))
        return history

    @event_func
    def set_announcement(self, announcement: Msg) -> None:
        """Set the announcement of the chatroom."""
        self._value["announcement"] = announcement
        self._trigger_listener(
            Event("set_announcement", {"announcement": announcement}),
        )

    @event_func
    def get_announcement(self) -> Msg:
        """Get the announcement of the chatroom."""
        ann = self._value["announcement"]
        self._trigger_listener(Event("get_announcement", {}))
        return ann

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

            def __call__(self, attr: Attribute, event: Event) -> None:
                if event.args["message"].name in self.target_names:
                    self.target_listener(attr, event)

        if not self.add_listener(
            "speak",
            listener=ListenTo(
                name=f"listen_to_{listener.name}",
                target_names=target_names,
                target_listener=listener,
            ),
        ):
            raise EnvListenerError("Fail to add listener.")
