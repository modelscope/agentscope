# -*- coding: utf-8 -*-
"""The enviromnent interface of AgentScope."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List
import threading


class Modifier(ABC):
    """A class to modify an attribute value in-place."""

    @abstractmethod
    def __call__(self, cur_value: Any) -> Any:
        """Modify the current value.

        Args:
            cur_value (`Any`): The current value.

        Returns:
            `Any`: The value after modification.
        """


class Watcher(ABC):
    """A class representing a watcher for monitoring the changing of an
    attribute."""

    def __init__(self, name: str) -> None:
        """Init a Watcher instance.

        Args:
            name (`str`): The name of the watcher.
        """
        self.name = name

    @abstractmethod
    def __call__(self, attr: Attribute) -> None:
        """Activate the watcher.

        Args:
            attr (`Attribute`): The attribute bound to the watcher.
        """


class Attribute:
    """A class representing an attribute."""

    def __init__(
        self,
        name: str,
        default: Any,
        watchers: List[Watcher] = None,
        env: Environment = None,
    ) -> None:
        """Init an Attribute instance.

        Args:
            name (`str`): The name of the attribute.
            default (`Any`): The default value of the attribute.
            watchers (`List[Watcher]`, optional): A list of watchers.
            Defaults to None.
            env (`Environment`): An instance of the Environment class.
            Defaults to None.
        """
        self.name = name
        self.value = default
        self.env = env
        self.lock = threading.Lock()
        self.watchers = (
            {watcher.name: watcher for watcher in watchers} if watchers else {}
        )

    def get(self) -> Any:
        """Get the value of the attribute.

        Returns:
            `Any`: The value of the attribute.
        """
        return self.value

    def modify(
        self,
        modifier: Modifier,
        disable_watcher: bool = False,
    ) -> Any:
        """Modify the value of the attribute.

        Args:
            modifier (`Modifier`): The modifier instance.
            disable_watcher (`bool`, optional): Whether to disable watchers.
            Defaults to False.

        Returns:
            `Any`: The value after modification.
        """
        with self.lock:
            modified_value = modifier(self.value)
            self.value = modified_value
        if not disable_watcher:
            self._activate_all()
        return modified_value

    def set(self, value: Any, disable_watcher: bool = False) -> None:
        """Set the value of the attribute.

        Args:
            value (`Any`): The new value of the attribute.
            disable_watcher (`bool`, optional): Whether to disable watchers.
            Defaults to False.
        """
        with self.lock:
            self.value = value
        if not disable_watcher:
            self._activate_all()

    def remove_watcher(self, name: str) -> bool:
        """Remove a watcher from the attribute.

        Args:
            name (`str`): The name of the watcher to remove.

        Returns:
            `bool`: Whether the watcher was removed successfully.
        """
        if name in self.watchers:
            del self.watchers[name]
            return True
        return False

    def add_watcher(self, watcher: Watcher) -> bool:
        """Add a watcher to the attribute.

        Args:
            watcher (`Watcher`): The watcher function to add.

        Returns:
            `bool`: Whether the watcher was added successfully.
        """
        if watcher.name in self.watchers:
            return False
        self.watchers[watcher.name] = watcher
        return True

    def environment(self) -> Environment:
        """Get the environment of this attribute.

        Returns:
            `Environment`: The environment.
        """
        return self.env

    def _activate_all(self) -> None:
        """Activate all the registered watchers."""
        for watcher in self.watchers.values():
            watcher(self)

    def _set_env(self, env: Environment) -> None:
        """Set the environment of this attribute."""
        self.env = env

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"


class Environment(ABC):
    """Interface of environment."""

    @abstractmethod
    def get(self, name: str) -> Any:
        """Get the value of an attribute.

        Args:
            name (`str`): The name of the attribute.

        Returns:
            `Any`: The value of the attribute.
        """

    @abstractmethod
    def set(
        self,
        attr_name: str,
        value: Any,
        disable_watcher: bool = False,
    ) -> bool:
        """Set the value of an attribute.

        Args:
            attr_name (`str`): The name of the attribute.
            value (`Any`): The new value of the attribute.
            disable_watcher (`bool`, optional): Whether to disable watchers.
                Defaults to False.

        Returns:
            `bool`: Whether the attribute was set successfully.
        """

    @abstractmethod
    def modifiy(
        self,
        attr_name: str,
        modifier: Modifier,
        disable_watcher: bool = False,
    ) -> Any:
        """Modify the value of an attribute.

        Args:
            attr_name (`str`): The name of the attribute.
            modifier (`Callable`): The modifier function.
            disable_watcher (`bool`, optional): Whether to disable watchers.
                Defaults to False.

        Returns:
            `Any`: The value after modification.
        """

    @abstractmethod
    def remove_watcher(self, attr_name: str, watcher_name: str) -> bool:
        """Remove a watcher from an attribute.

        Args:
            attr_name (`str`): The name of the attribute.
            watcher_name (`str`): The name of the watcher to remove.

        Returns:
            `bool`: Whether the watcher was removed successfully.
        """

    @abstractmethod
    def add_watcher(
        self,
        attr_name: str,
        watcher: Watcher,
    ) -> bool:
        """Add a watcher to an attribute.

        Args:
            attr_name (`str`): The name of the attribute.
            watcher (`Watcher`): The watcher function to add.

        Returns:
            `bool`: Whether the watcher was added successfully.
        """
