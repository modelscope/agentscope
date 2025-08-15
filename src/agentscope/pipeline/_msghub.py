# -*- coding: utf-8 -*-
"""MsgHub is designed to share messages among a group of agents."""
from typing import Any

from .._logging import logger

from ..agent import AgentBase
from ..message import Msg


class MsgHub:
    """MsgHub class that controls the subscription of the participated agents.

    Example:
        In the following example, the reply message from `agent1`, `agent2`,
        and `agent3` will be broadcasted to all the other agents in the MsgHub.

        .. code-block:: python

            with MsgHub(participant=[agent1, agent2, agent3]):
                agent1()
                agent2()

        Actually, it has the same effect as the following code, but much more
        easy and elegant!

        .. code-block:: python

            x1 = agent1()
            agent2.observe(x1)
            agent3.observe(x1)

            x2 = agent2()
            agent1.observe(x2)
            agent3.observe(x2)

    """

    def __init__(
        self,
        participants: list[AgentBase],
        announcement: list[Msg] | Msg | None = None,
    ) -> None:
        """Initialize a MsgHub context manager.

        Args:
            participants (`list[AgentBase]`):
                A list of agents that participate in the MsgHub.
            announcement （`list[Msg] | Msg | None`):
                The message that will be broadcast to all participants when
                entering the MsgHub.
        """
        self.participants = participants
        self.announcement = announcement

    async def __aenter__(self) -> "MsgHub":
        """Will be called when entering the MsgHub."""
        self._reset_subscriber()

        # broadcast the input message to all participants
        if self.announcement is not None:
            for agent in self.participants:
                await agent.observe(self.announcement)

        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        """Will be called when exiting the MsgHub."""
        for agent in self.participants:
            agent.reset_subscribers([])

    def _reset_subscriber(self) -> None:
        """Reset the subscriber for agent in `self.participant`"""
        for agent in self.participants:
            agent.reset_subscribers(self.participants)

    def add(
        self,
        new_participant: list[AgentBase] | AgentBase,
    ) -> None:
        """Add new participant into this hub"""
        if isinstance(new_participant, AgentBase):
            new_participant = [new_participant]

        for agent in new_participant:
            if agent not in self.participants:
                self.participants.append(agent)

        self._reset_subscriber()

    def delete(
        self,
        participant: list[AgentBase] | AgentBase,
    ) -> None:
        """Delete agents from participant."""
        if isinstance(participant, AgentBase):
            participant = [participant]

        for agent in participant:
            if agent in self.participants:
                # Clear the subscriber of the deleted agent firstly
                agent.reset_subscribers([])

                # remove agent from self.participant
                self.participants.pop(self.participants.index(agent))
            else:
                logger.warning(
                    "Cannot find the agent with ID %s, skip its deletion.",
                    agent.id,
                )

        # Remove this agent from the subscriber of other agents
        self._reset_subscriber()

    async def broadcast(self, msg: list[Msg] | Msg) -> None:
        """Broadcast the message to all participants.

        Args:
            msg (`list[Msg] | Msg`):
                Message(s) to be broadcast among all participants.
        """
        for agent in self.participants:
            await agent.observe(msg)
