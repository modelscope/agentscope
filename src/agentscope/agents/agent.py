# -*- coding: utf-8 -*-
""" Base class for Agent """

from __future__ import annotations
from typing import Optional
from typing import Sequence
from typing import Union
from typing import Any
from typing import Callable

from loguru import logger

from .operator import _Operator
from ..models import load_model_by_name
from ..memory import TemporaryMemory


class AgentBase(_Operator):
    """Base class for all agents.

    All agents should inherit from this class and implement the `reply`
    function.
    """

    _version: int = 1

    def __init__(
        self,
        name: str,
        config: Optional[dict] = None,
        sys_prompt: Optional[str] = None,
        model: Optional[Union[Callable[..., Any], str]] = None,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
    ) -> None:
        r"""Initialize an agent from the given arguments.

        Args:
            name (`str`):
                The name of the agent.
            config (`Optional[dict]`):
                The configuration of the agent, if provided, the agent will
                be initialized from the config rather than the other
                parameters.
            sys_prompt (`Optional[str]`):
                The system prompt of the agent, which can be passed by args
                or hard-coded in the agent.
            model (`Optional[Union[Callable[..., Any], str]]`, defaults to
            None):
                The callable model object or the model name, which is used to
                load model from configuration.
            use_memory (`bool`, defaults to `True`):
                Whether the agent has memory.
            memory_config (`Optional[dict]`):
                The config of memory.
        """

        self.name = name
        self.config = config
        self.memory_config = memory_config

        if sys_prompt is not None:
            self.sys_prompt = sys_prompt

        if model is not None:
            if isinstance(model, str):
                self.model = load_model_by_name(model)
            else:
                self.model = model

        if use_memory:
            self.memory = TemporaryMemory(memory_config)

        # The audience of this agent, which means if this agent generates a
        # response, it will be passed to all agents in the audience.
        self._audience = None

    def reply(self, x: dict = None) -> dict:
        """Define the actions taken by this agent.

        Args:
            x (`dict`, defaults to `None`):
                Dialog history and some environment information

        Returns:
            The agent's response to the input.

        Note:
            Given that some agents are in an adversarial environment,
            their input doesn't include the thoughts of other agents.
        """
        raise NotImplementedError(
            f"Agent [{type(self).__name__}] is missing the required "
            f'"reply" function.',
        )

    def load_from_config(self, config: dict) -> None:
        """Load configuration for this agent.

        Args:
            config (`dict`): model configuration
        """

    def export_config(self) -> dict:
        """Return configuration of this agent.

        Returns:
            The configuration of current agent.
        """
        return {}

    def load_memory(self, memory: Sequence[dict]) -> None:
        r"""Load input memory."""

    def __call__(self, *args: Any, **kwargs: Any) -> dict:
        """Calling the reply function, and broadcast the generated
        response to all audiences if needed."""
        res = self.reply(*args, **kwargs)

        # broadcast to audiences if needed
        if self._audience is not None:
            self._broadcast_to_audience(res)

        return res

    def observe(self, x: Union[dict, Sequence[dict]]) -> None:
        """Observe the input, store it in memory without response to it.

        Args:
            x (`Union[dict, Sequence[dict]]`):
                The input message to be recorded in memory.
        """
        self.memory.add(x)

    def reset_audience(self, audience: Sequence[AgentBase]) -> None:
        """Set the audience of this agent, which means if this agent
        generates a response, it will be passed to all audiences.

        Args:
            audience (`Sequence[AgentBase]`):
                The audience of this agent, which will be notified when this
                agent generates a response message.
        """
        # TODO: we leave the consideration of nested msghub for future.
        #  for now we suppose one agent can only be in one msghub
        self._audience = [_ for _ in audience if _ != self]

    def clear_audience(self) -> None:
        """Remove the audience of this agent."""
        # TODO: we leave the consideration of nested msghub for future.
        #  for now we suppose one agent can only be in one msghub
        self._audience = None

    def rm_audience(
        self,
        audience: Union[Sequence[AgentBase], AgentBase],
    ) -> None:
        """Remove the given audience from the Sequence"""
        if not isinstance(audience, Sequence):
            audience = [audience]

        for agent in audience:
            if self._audience is not None and agent in self._audience:
                self._audience.pop(self._audience.index(agent))
            else:
                logger.warning(
                    f"Skip removing agent [{agent.name}] from the "
                    f"audience for its inexistence.",
                )

    def _broadcast_to_audience(self, x: dict) -> None:
        """Broadcast the input to all audiences."""
        for agent in self._audience:
            agent.observe(x)
