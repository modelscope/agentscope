# -*- coding: utf-8 -*-
"""An agent used as environment"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List

from agentscope.agents import AgentBase


class Trigger(ABC):
    """A class representing a trigger used in environment."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def trigger(self, attr: Attribute) -> None:
        """Call the trigger.

        Arguments:
            attr (`Attribute`): The attribute bound to the trigger.
        """

    def __call__(self, attr: Attribute) -> None:
        self.trigger(attr)


class Attribute:
    """A class representing an attribute."""

    def __init__(
        self,
        name: str,
        default: Any,
        env: Environment,
        triggers: List[Trigger] = None,
    ) -> None:
        """Init an Attribute instance.

        Args:
            name (`str`): The name of the attribute.
            default (`Any`): The default value of the attribute.
            env (`Environment`): An instance of the Environment class.
            triggers (`List[Trigger]`, optional): A list of callable triggers.
            Defaults to None
        """
        self.name = name
        self.value = default
        self.env = env
        self.triggers = (
            {trigger.name: trigger for trigger in triggers} if triggers else {}
        )

    def set(self, value: Any, disable_trigger: bool = False) -> None:
        """Set the value of the attribute.

        Args:
            value (`Any`): The new value of the attribute.
            disable_trigger (`bool`, optional): Whether to disable triggers.
            Defaults to False.
        """
        self.value = value
        if not disable_trigger:
            self._trigger_all()

    def get(self) -> Any:
        """Get the value of the attribute.

        Returns:
            `Any`: The value of the attribute.
        """
        return self.value

    def remove_trigger(self, name: str) -> bool:
        """Remove a trigger from the attribute.

        Args:
            name (`str`): The name of the trigger to remove.

        Returns:
            `bool`: Whether the trigger was removed successfully.
        """
        if name in self.triggers:
            del self.triggers[name]
            return True
        return False

    def add_trigger(self, trigger: Trigger) -> bool:
        """Add a trigger to the attribute.

        Args:
            trigger (`Trigger`): The trigger function to add.

        Returns:
            `bool`: Whether the trigger was added successfully.
        """
        if trigger.name in self.triggers:
            return False
        self.triggers[trigger.name] = trigger
        return True

    def environment(self) -> Environment:
        """Get the environment of this attribute.

        Returns:
            `Environment`: The environment.
        """
        return self.env

    def _trigger_all(self):
        """Trigger all the registered triggers."""
        for trigger in self.triggers.values():
            trigger(self)


class Environment(AgentBase):
    """A class representing an environment."""

    def __init__(self, name: str, attrs: List[Attribute]) -> None:
        """Init an Environment instance.

        Args:
            name (`str`): The name of the environment.
            attrs (`List[Attribute]`): A list of attributes.
        """
        super().__init__(name, use_memory=False)
        self.attrs = {attr.name: attr for attr in attrs}

    def get(self, name: str) -> Any:
        """Get the value of an attribute.

        Args:
            name (`str`): The name of the attribute.

        Returns:
            `Any`: The value of the attribute.
        """
        return self.attrs[name].get()

    def set(
        self, name: str, value: Any, disable_trigger: bool = False
    ) -> bool:
        """Set the value of an attribute.

        Args:
            name (`str`): The name of the attribute.
            value (`Any`): The new value of the attribute.
            disable_trigger (`bool`, optional): Whether to disable triggers.
                Defaults to False.

        Returns:
            `bool`: Whether the attribute was set successfully.
        """
        if name in self.attrs:
            self.attrs[name].set(value, disable_trigger=disable_trigger)
            return True
        else:
            return False

    def remove_trigger(self, attr_name: str, trigger_name: str) -> bool:
        """Remove a trigger from an attribute.

        Args:
            attr_name (`str`): The name of the attribute.
            trigger_name (`str`): The name of the trigger to remove.

        Returns:
            `bool`: Whether the trigger was removed successfully.
        """
        if attr_name in self.attrs:
            self.attrs[attr_name].remove_trigger(trigger_name)
            return True
        else:
            return False

    def add_trigger(
        self, attr_name: str, trigger_name: str, trigger: Trigger
    ) -> bool:
        """Add a trigger to an attribute.

        Args:
            attr_name (`str`): The name of the attribute.
            trigger_name (`str`): The name of the trigger to add.
            trigger (`Trigger`): The trigger function to add.

        Returns:
            `bool`: Whether the trigger was added successfully.
        """
        if attr_name in self.attrs:
            return self.attrs[attr_name].add_trigger(trigger_name, trigger)
        else:
            return False
