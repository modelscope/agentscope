# -*- coding: utf-8 -*-
"""Pipeline classes."""
from typing import Type

from pydantic import BaseModel

from ._functional import sequential_pipeline
from ..agent import AgentBase
from ..message import Msg


class SequentialPipeline:
    """An async sequential pipeline class, which executes a sequence of
    agents sequentially. Compared with functional pipeline, this class
    can be re-used."""

    def __init__(
        self,
        agents: list[AgentBase],
    ) -> None:
        """Initialize a sequential pipeline class

        Args:
            agents (`list[AgentBase]`):
                A list of agents.
        """
        self.agents = agents

    async def __call__(
        self,
        msg: Msg | list[Msg] | None = None,
        structured_model: Type[BaseModel] | None = None,
    ) -> Msg | list[Msg] | None:
        """Execute the sequential pipeline

        Args:
            msg (`Msg | list[Msg] | None`, defaults to `None`):
                The initial input that will be passed to the first agent.
             structured_model (`Type[BaseModel] | None`, defaults to `None`):
                A Pydantic BaseModel class that defines the expected structure
                for the agents' output.
        """
        return await sequential_pipeline(
            agents=self.agents,
            msg=msg,
            structured_model=structured_model,
        )
