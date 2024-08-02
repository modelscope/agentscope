# -*- coding: utf-8 -*-
"""The attribute used in environment."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List
import threading


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
        target_event: str,
        kwargs: dict,
    ) -> None:
        """Activate the listener.

        Args:
            attr (`Attribute`): The attribute bound to the listener.
            target_event (`str`): The target event function.
            kwargs (`dict`): The arguments to pass to the `target_event`.
        """


class Attribute:
    """The base class of all attribute."""

    def __init__(
        self,
        name: str,
        default: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: dict[str, Attribute] = None,
        parent: Attribute = None,
    ) -> None:
        """Init an Attribute instance.

        Args:
            name (`str`): The name of the attribute.
            default (`Any`): The default value of the attribute.
            listeners (`dict[str, List[EventListener]]`, optional): The
            listener dict. Defaults to None.
            env (`Environment`): An instance of the Environment class.
            Defaults to None.
            children (`dict[str, Attribute]`, optional): A dict of children
            attributes. Defaults to None.
            parent (`Attribute`, optional): The parent attribute. Defaults to
            None.
        """
        self.name = name
        self.value = default
        self.children = children
        self.parent = parent
        self.lock = threading.Lock()
        self.listeners = {}
        if listeners:
            for target_func, listener in listeners.items():
                if isinstance(listener, EventListener):
                    self.add_listener(target_func, listener)
                else:
                    for ls in listener:
                        self.add_listener(target_func, ls)

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

    def set_children(self, children: dict[str, Attribute]) -> None:
        """Set the children attributes of the current attribute.

        Args:
            children (`dict[str, Attribute]`): The children attributes.
        """
        self.children = children

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
            if target_event not in self.listeners:
                self.listeners[target_event] = {}
            if listener.name not in self.listeners[target_event]:
                self.listeners[target_event][listener.name] = listener
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
        if target_event in self.listeners:
            if listener_name in self.listeners[target_event]:
                del self.listeners[target_event][listener_name]
                return True
        return False

    def _trigger_listener(
        self,
        target_event: str,
        kwargs: dict = None,
    ) -> None:
        """Trigger the listeners of the specific event.

        Args:
            target_event (`str`): The event function.
            kwargs (`dict`): The arguments to pass to the target_event.
        """
        if target_event in self.listeners:
            for listener in self.listeners[target_event].values():
                listener(self, target_event, kwargs)

    def dump(self) -> dict:
        """Dump the attribute tree to a dict."""
        return {
            "value": self.value,
            "type": self.__class__.__name__,
            "children": {
                child.name: child.dump()
                for child in (self.children.values() if self.children else [])
            },
        }
