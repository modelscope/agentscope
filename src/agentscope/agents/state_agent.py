# -*- coding: utf-8 -*-
""" State agent module. """
from typing import Any, Callable, Dict, Union
from loguru import logger

from .agent import AgentBase


class StateAgent(AgentBase):
    """
    Manages the state of an agent, allowing for actions to be executed
    based on the current state.

    Methods:
        reply(self, x: dict = None) -> dict: Processes the input based on
            the current state handler.
        register_state(self, state: str, handler: Callable, properties:
            Dict[str, Any] = None): Registers a new state handler.
        transition(self, new_state: str): Transitions the agent to a new state.
    """

    def __init__(self, *arg: Any, **kwargs: Any):
        super().__init__(*arg, **kwargs)
        self.cur_state = None
        self.state_handlers = {}
        self.state_properties = {}

    def reply(self, x: dict = None) -> dict:
        """
        Define the actions taken by this agent. Handler the input based
        on the current state handler and returns the response message.

        Args:
            x (`dict`, defaults to `None`):
                Dialog history and some environment information

        Returns:
            The agent's response to the input.
        """
        handler = self.state_handlers.get(self.cur_state)
        if handler is None:
            raise ValueError(
                f"No handler registered for state '{self.cur_state}'",
            )
        msg = handler(x)
        return msg

    def register_state(
        self,
        state: Union[int, str, float, tuple],
        handler: Callable,
        properties: Dict[str, Any] = None,
    ) -> None:
        """
        Registers a new state, its handler function, and optionally
        properties associated with the state.

        Args:
            state (Union[int, str, float, tuple]): The name of the state to
                register.
            handler (Callable): The function that handles the state.
            properties (dict, optional): A dictionary of properties related
                to the state.

        Returns:
            None
        """
        if state in self.state_handlers:
            logger.warning(
                f"State '{state}' is already registered. Overwriting.",
            )
        self.state_handlers[state] = handler
        if properties:
            self.state_properties[state] = properties

    def transition(self, new_state: Union[int, str, float, tuple]) -> None:
        """
        Transitions the agent to a new state and updates any associated
        properties.

        Args:
            new_state (Union[int, str, float, tuple]): The state to which
                the agent should transition.

        Returns:
            None

        Raises:
            ValueError: If the new_state is not registered.
        """
        if new_state not in self.state_handlers:
            raise ValueError(f"State '{new_state}' is not registered.")
        self.cur_state = new_state
        # Switch other properties related to the new state
        if new_state in self.state_properties:
            for prop, value in self.state_properties[new_state].items():
                setattr(self, prop, value)
        else:
            logger.debug(
                f"No additional properties to switch for state '{new_state}'.",
            )
