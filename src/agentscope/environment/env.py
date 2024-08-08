# -*- coding: utf-8 -*-
"""The env module."""
from __future__ import annotations
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, List
from loguru import logger

from ..exception import (
    EnvNotFoundError,
    EnvAlreadyExistError,
)
from .event import Event


class EventListener(ABC):
    """A class representing a listener for listening the event of an
    env."""

    def __init__(self, name: str) -> None:
        """Init a EventListener instance.

        Args:
            name (`str`): The name of the listener.
        """
        self.name = name

    @abstractmethod
    def __call__(
        self,
        attr: Env,
        event: Event,
    ) -> None:
        """Activate the listener.

        Args:
            attr (`Env`): The env bound to the listener.
            event (`Event`): The event information.
        """


class _EnvMeta(ABCMeta):
    """The metaclass for env."""

    def __init__(cls, name: Any, bases: Any, attrs: Any) -> None:
        if not hasattr(cls, "_registry"):
            cls._registry = {}
        else:
            if name in cls._registry:
                logger.warning(
                    f"Env class with name [{name}] already exists.",
                )
            else:
                cls._registry[name] = cls
        super().__init__(name, bases, attrs)

    def __call__(cls, *args: tuple, **kwargs: dict) -> Any:
        pass


class Env(ABC):
    """The Env Interface.
    Env is a key concept of AgentScope, which is used to
    represent global data shared among agents.

    Each env has its own name and value, and multiple envs
    can be organized into a tree structure, where each env can
    have multiple children envs and one parent env.

    Different implementation of envs may have different event functions,
    which are marked by `@event_func`.
    Users can bind `EventListener` to specific event functions, and
    the listener will be activated when the event function is called.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the env.

        Returns:
            `str`: The name of the env.
        """

    @abstractmethod
    def get_parent(self) -> Env:
        """Get the parent env of the current env.

        Returns:
            `Env`: The parent env.
        """

    @abstractmethod
    def set_parent(self, parent: Env) -> None:
        """Set the parent env of the current env.

        Args:
            parent (`Env`): The parent env.
        """

    @abstractmethod
    def get_children(self) -> dict[str, Env]:
        """Get the children envs of the current env.

        Returns:
            `dict[str, Env]`: The children envs.
        """

    @abstractmethod
    def add_child(self, child: Env) -> bool:
        """Add a child env to the current env.

        Args:
            child (`Env`): The children
            envs.

        Returns:
            `bool`: Whether the children were added successfully.
        """

    @abstractmethod
    def remove_child(self, children_name: str) -> bool:
        """Remove a child env from the current env.

        Args:
            children_name (`str`): The name of the children env.

        Returns:
            `bool`: Whether the children were removed successfully.
        """

    @abstractmethod
    def add_listener(self, target_event: str, listener: EventListener) -> bool:
        """Add a listener to the env.

        Args:
            target_event (`str`): The event function to listen.
            listener (`EventListener`): The listener to add.

        Returns:
            `bool`: Whether the listener was added successfully.
        """

    @abstractmethod
    def remove_listener(self, target_event: str, listener_name: str) -> bool:
        """Remove a listener from the env.

        Args:
            target_event (`str`): The event function.
            listener_name (`str`): The name of the listener to remove.

        Returns:
            `bool`: Whether the listener was removed successfully.
        """

    @abstractmethod
    def __getitem__(self, env_name: str) -> Env:
        """Get a child env."""

    @abstractmethod
    def __setitem__(self, env_name: str, attr: Env) -> None:
        """Set a child env."""


class BasicEnv(Env):
    """A basic implementation of Env, which has no event function
    and cannot get value.

    Note:
        `BasicEnv` is used as the base class to implement other
        envs. Application developers should not use this class.
    """

    def __init__(
        self,
        name: str,
        value: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Env] = None,
        parent: Env = None,
    ) -> None:
        """Init an BasicEnv instance.

        Args:
            name (`str`): The name of the env.
            value (`Any`): The default value of the env.
            listeners (`dict[str, List[EventListener]]`, optional): The
            listener dict. Defaults to None.
            children (`List[Env]`, optional): A list of children
            envs. Defaults to None.
            parent (`Env`, optional): The parent env. Defaults
            to None.
        """
        self._name = name
        self._value = value
        self.children = {
            child.name: child for child in (children if children else [])
        }
        self.parent = parent
        self.event_listeners = {}
        if listeners:
            for target_func, listener in listeners.items():
                if isinstance(listener, EventListener):
                    self.add_listener(target_func, listener)
                else:
                    for ls in listener:
                        self.add_listener(target_func, ls)

    @property
    def name(self) -> str:
        """Name of the env"""
        return self._name

    def get_parent(self) -> Env:
        """Get the parent env of the current env.

        Returns:
            `Env`: The parent env.
        """
        return self.parent

    def set_parent(self, parent: Env) -> None:
        """Set the parent env of the current env.

        Args:
            parent (`Env`): The parent env.
        """
        self.parent = parent

    def get_children(self) -> dict[str, Env]:
        """Get the children envs of the current env.

        Returns:
            `dict[str, Env]`: The children envs.
        """
        return self.children

    def add_child(self, child: Env) -> bool:
        """Add a child env to the current env.

        Args:
            child (`Env`): The children
            envs.

        Returns:
            `bool`: Whether the children were added successfully.
        """
        if child.name in self.children:
            return False
        self.children[child.name] = child
        return True

    def remove_child(self, children_name: str) -> bool:
        """Remove a child env from the current env.

        Args:
            children_name (`str`): The name of the children env.

        Returns:
            `bool`: Whether the children were removed successfully.
        """
        if children_name in self.children:
            del self.children[children_name]
            return True
        return False

    def add_listener(self, target_event: str, listener: EventListener) -> bool:
        """Add a listener to the env.

        Args:
            target_event (`str`): The event function to listen.
            listener (`EventListener`): The listener to add.

        Returns:
            `bool`: Whether the listener was added successfully.
        """
        if (
            hasattr(self, target_event)
            and hasattr(getattr(self, target_event), "_is_event")
            and getattr(self, target_event)._is_event  # pylint: disable=W0212
        ):
            if target_event not in self.event_listeners:
                self.event_listeners[target_event] = {}
            if listener.name not in self.event_listeners[target_event]:
                self.event_listeners[target_event][listener.name] = listener
                return True
        return False

    def remove_listener(self, target_event: str, listener_name: str) -> bool:
        """Remove a listener from the env.

        Args:
            target_event (`str`): The event function.
            listener_name (`str`): The name of the listener to remove.

        Returns:
            `bool`: Whether the listener was removed successfully.
        """
        if target_event in self.event_listeners:
            if listener_name in self.event_listeners[target_event]:
                del self.event_listeners[target_event][listener_name]
                return True
        return False

    def _trigger_listener(self, event: Event) -> None:
        """Trigger the listeners of the specific event.

        Args:
            event_name (`str`): The event function name.
            args (`dict`): The arguments to pass to the event.
        """
        if event.name in self.event_listeners:
            for listener in self.event_listeners[event.name].values():
                listener(self, event)

    def dump(self) -> dict:
        """Dump the env tree to a dict."""
        return {
            "value": self._value,
            "type": self.__class__.__name__,
            "children": {
                child.name: child.dump()
                for child in (self.children.values() if self.children else [])
            },
        }

    def __getitem__(self, env_name: str) -> Env:
        if env_name in self.children:
            return self.children[env_name]
        else:
            raise EnvNotFoundError(env_name)

    def __setitem__(self, env_name: str, attr: Env) -> None:
        if not isinstance(attr, Env):
            raise TypeError("Only Env can be set")
        if env_name not in self.children:
            self.children[env_name] = attr
        else:
            raise EnvAlreadyExistError(env_name)
