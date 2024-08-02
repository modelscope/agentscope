# -*- coding: utf-8 -*-
""" A basic Attribute that can be get and set."""
from typing import List, Any

from ..attribute import Attribute, EventListener
from ..event import event
from ..event import Get, Set


class BasicAttribute(Attribute, Get, Set):
    """A basic Attribute that can be get and set."""

    def __init__(
        self,
        name: str,
        default: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: dict[str, Attribute] = None,
        parent: Attribute = None,
    ) -> None:
        super().__init__(
            name=name,
            default=default,
            listeners=listeners,
            children=children,
            parent=parent,
        )

    @event
    def get(self) -> Any:
        self._trigger_listener("get", None)  # type: ignore[arg-type]
        return self.value

    @event
    def set(self, value: Any) -> bool:
        self.value = value
        self._trigger_listener("set", {"value": value})
        return True
