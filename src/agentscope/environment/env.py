# -*- coding: utf-8 -*-
"""The env module."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Callable
from concurrent.futures import ThreadPoolExecutor
import inspect
from ..exception import (
    EnvNotFoundError,
    EnvAlreadyExistError,
)
from .event import Event
from ..rpc.rpc_meta import RpcMeta, sync_func


def trigger_listener(env: "Env", event: Event) -> None:
    """Trigger the listener bound to the event.

    Args:
        env (`Env`): The env that trigger the listener.
        event (`Event`): The event information.
    """
    futures = []
    with ThreadPoolExecutor() as executor:
        for listener in env.get_listeners(event.name):
            futures.append(executor.submit(listener, env, event))
    for future in futures:
        future.result()


def event_func(func: Callable) -> Callable:
    """A decorator to register an event function.

    Args:
        func (`Callable`): The event function.

    Returns:
        `Callable`: The decorated event function.
    """

    def wrapper(  # type: ignore[no-untyped-def]
        *args,
        **kwargs,
    ) -> Any:
        # get the dict format args of the decorated function
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        args_dict = bound_args.arguments
        # call the function
        returns = func(*args, **kwargs)
        self = args_dict.pop("self")
        trigger_listener(
            env=self,
            event=Event(
                name=func.__name__,
                args=args_dict,
                returns=returns,
            ),
        )
        return returns

    return wrapper


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
        env: Env,
        event: Event,
    ) -> None:
        """Activate the listener.

        Args:
            env (`Env`): The env bound to the listener.
            event (`Event`): The event information.
        """


class Env(ABC, metaclass=RpcMeta):
    """The Env Interface.
    `Env` is a key concept of AgentScope, representing global
    data shared among agents.

    Each env has its own name and value, and multiple envs can
    be organized into a tree structure, where each env can have
    multiple children envs and one parent env.

    Different implementations of envs may have different event
    functions, which are marked by `@event_func`.
    Users can bind `EventListener` to specific event functions,
    and the listener will be activated when the event function
    is called.
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
    def get_listeners(self, target_event: str) -> List[EventListener]:
        """Get the listeners of the specific event.

        Args:
            target_event (`str`): The event name.

        Returns:
            `List[EventListener]`: The listeners of the specific event.
        """

    @sync_func
    @abstractmethod
    def __getitem__(self, env_name: str) -> Env:
        """Get a child env."""

    @abstractmethod
    def __setitem__(self, env_name: str, env: Env) -> None:
        """Set a child env."""

    @abstractmethod
    def describe(self, **kwargs: Any) -> str:
        """Describe the current state of the environment."""


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
        listeners: dict[str, List[EventListener]] = None,
        children: List[Env] = None,
        parent: Env = None,
    ) -> None:
        """Init an BasicEnv instance.

        Args:
            name (`str`): The name of the env.
            listeners (`dict[str, List[EventListener]]`, optional): The
            listener dict. Defaults to None.
            children (`List[Env]`, optional): A list of children
            envs. Defaults to None.
            parent (`Env`, optional): The parent env. Defaults
            to None.
        """
        self._name = name
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
        child.set_parent(self)
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
            target_event (`str`): The name of the event to listen.
            listener (`EventListener`): The listener to add.

        Returns:
            `bool`: Whether the listener was added successfully.
        """
        if hasattr(self, target_event):
            if target_event not in self.event_listeners:
                self.event_listeners[target_event] = {}
            if listener.name not in self.event_listeners[target_event]:
                self.event_listeners[target_event][listener.name] = listener
                return True
        return False

    def remove_listener(self, target_event: str, listener_name: str) -> bool:
        """Remove a listener from the env.

        Args:
            target_event (`str`): The event name.
            listener_name (`str`): The name of the listener to remove.

        Returns:
            `bool`: Whether the listener was removed successfully.
        """
        if target_event in self.event_listeners:
            if listener_name in self.event_listeners[target_event]:
                del self.event_listeners[target_event][listener_name]
                return True
        return False

    def get_listeners(self, target_event: str) -> List[EventListener]:
        """Get the listeners of the specific event.

        Args:
            target_event (`str`): The event name.

        Returns:
            `List[EventListener]`: The listeners of the specific event.
        """
        if target_event in self.event_listeners:
            return list(self.event_listeners[target_event].values())
        else:
            return []

    def describe(self, **kwargs: Any) -> str:
        """Describe the current state of the environment."""
        raise NotImplementedError(
            "`describe` is not implemented in `BasicEnv`.",
        )

    def __getitem__(self, env_name: str) -> Env:
        if env_name in self.children:
            return self.children[env_name]
        else:
            raise EnvNotFoundError(env_name)

    def __setitem__(self, env_name: str, env: Env) -> None:
        if not isinstance(env, Env):
            raise TypeError("Only Env can be set")
        if env_name not in self.children:
            self.children[env_name] = env
            env.set_parent(self)
        else:
            raise EnvAlreadyExistError(env_name)
