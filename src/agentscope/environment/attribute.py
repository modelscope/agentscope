# -*- coding: utf-8 -*-
"""The attribute used in environment."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List

from ..exception import (
    EnvAttributeNotFoundError,
    EnvAttributeAlreadyExistError,
)
from .event import Event


class EventListener(ABC):
    """A class representing a listener for listening the event of an
    attribute."""

    def __init__(self, name: str) -> None:
        """Init a EventListener instance.

        Args:
            name (`str`): The name of the listener.
        """
        self.name = name

    @abstractmethod
    def __call__(
        self,
        attr: Attribute,
        event: Event,
    ) -> None:
        """Activate the listener.

        Args:
            attr (`Attribute`): The attribute bound to the listener.
            event (`Event`): The event information.
        """


class Attribute(ABC):
    """The Attribute Interface.
    Attribute is a key concept of AgentScope, which is used to
    represent global data shared among agents.

    Each attribute has its own name and value, and multiple attributes
    can be organized into a tree structure, where each attribute can
    have multiple children attributes and one parent attribute.

    Different implementation of attributes may have different event functions,
    which are marked by `@event_func`.
    Users can bind `EventListener` to specific event functions, and
    the listener will be activated when the event function is called.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the attribute.

        Returns:
            `str`: The name of the attribute.
        """

    @abstractmethod
    def get_parent(self) -> Attribute:
        """Get the parent attribute of the current attribute.

        Returns:
            `Attribute`: The parent attribute.
        """

    @abstractmethod
    def set_parent(self, parent: Attribute) -> None:
        """Set the parent attribute of the current attribute.

        Args:
            parent (`Attribute`): The parent attribute.
        """

    @abstractmethod
    def get_children(self) -> dict[str, Attribute]:
        """Get the children attributes of the current attribute.

        Returns:
            `dict[str, Attribute]`: The children attributes.
        """

    @abstractmethod
    def add_child(self, child: Attribute) -> bool:
        """Add a child attribute to the current attribute.

        Args:
            child (`Attribute`): The children
            attributes.

        Returns:
            `bool`: Whether the children were added successfully.
        """

    @abstractmethod
    def remove_child(self, children_name: str) -> bool:
        """Remove a child attribute from the current attribute.

        Args:
            children_name (`str`): The name of the children attribute.

        Returns:
            `bool`: Whether the children were removed successfully.
        """

    @abstractmethod
    def add_listener(self, target_event: str, listener: EventListener) -> bool:
        """Add a listener to the attribute.

        Args:
            target_event (`str`): The event function to listen.
            listener (`EventListener`): The listener to add.

        Returns:
            `bool`: Whether the listener was added successfully.
        """

    @abstractmethod
    def remove_listener(self, target_event: str, listener_name: str) -> bool:
        """Remove a listener from the attribute.

        Args:
            target_event (`str`): The event function.
            listener_name (`str`): The name of the listener to remove.

        Returns:
            `bool`: Whether the listener was removed successfully.
        """

    @abstractmethod
    def __getitem__(self, attr_name: str) -> Attribute:
        """Get a child attribute."""

    @abstractmethod
    def __setitem__(self, attr_name: str, attr: Attribute) -> None:
        """Set a child attribute."""


class BasicAttribute(Attribute):
    """A basic implementation of Attribute, which has no event function
    and cannot get value.

    Note:
        `BasicAttribute` is used as the base class to implement other
        attributes. Application developers should not use this class.
    """

    def __init__(
        self,
        name: str,
        value: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Attribute] = None,
        parent: Attribute = None,
    ) -> None:
        """Init an BasicAttribute instance.

        Args:
            name (`str`): The name of the attribute.
            value (`Any`): The default value of the attribute.
            listeners (`dict[str, List[EventListener]]`, optional): The
            listener dict. Defaults to None.
            env (`Environment`): An instance of the Environment class.
            Defaults to None.
            children (`List[Attribute]`, optional): A list of children
            attributes. Defaults to None.
            parent (`Attribute`, optional): The parent attribute. Defaults
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
        """Name of the attribtue"""
        return self._name

    def get_parent(self) -> Attribute:
        """Get the parent attribute of the current attribute.

        Returns:
            `Attribute`: The parent attribute.
        """
        return self.parent

    def set_parent(self, parent: Attribute) -> None:
        """Set the parent attribute of the current attribute.

        Args:
            parent (`Attribute`): The parent attribute.
        """
        self.parent = parent

    def get_children(self) -> dict[str, Attribute]:
        """Get the children attributes of the current attribute.

        Returns:
            `dict[str, Attribute]`: The children attributes.
        """
        return self.children

    def add_child(self, child: Attribute) -> bool:
        """Add a child attribute to the current attribute.

        Args:
            child (`Attribute`): The children
            attributes.

        Returns:
            `bool`: Whether the children were added successfully.
        """
        if child.name in self.children:
            return False
        self.children[child.name] = child
        return True

    def remove_child(self, children_name: str) -> bool:
        """Remove a child attribute from the current attribute.

        Args:
            children_name (`str`): The name of the children attribute.

        Returns:
            `bool`: Whether the children were removed successfully.
        """
        if children_name in self.children:
            del self.children[children_name]
            return True
        return False

    def add_listener(self, target_event: str, listener: EventListener) -> bool:
        """Add a listener to the attribute.

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
        """Remove a listener from the attribute.

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
        """Dump the attribute tree to a dict."""
        return {
            "value": self._value,
            "type": self.__class__.__name__,
            "children": {
                child.name: child.dump()
                for child in (self.children.values() if self.children else [])
            },
        }

    def __getitem__(self, attr_name: str) -> Attribute:
        if attr_name in self.children:
            return self.children[attr_name]
        else:
            raise EnvAttributeNotFoundError(attr_name)

    def __setitem__(self, attr_name: str, attr: Attribute) -> None:
        if not isinstance(attr, Attribute):
            raise TypeError("Only Attribute can be set")
        if attr_name not in self.children:
            self.children[attr_name] = attr
        else:
            raise EnvAttributeAlreadyExistError(attr_name)


class RpcAttribute(Attribute):
    """A attribute that can be accessed through RPC."""

    def __init__(
        self,
        name: str,
        host: str = "localhost",
        port: int = None,
        attr_id: str = None,
    ) -> None:
        pass
