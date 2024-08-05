# -*- coding: utf-8 -*-
""" A basic Attribute that can be get and set."""
from typing import List, Any
from copy import deepcopy

from ..attribute import Attribute, EventListener
from ..event import event_func, Event, Getable, Setable


class BasicAttribute(Attribute, Getable, Setable):
    """A basic Attribute that can be get and set."""

    def __init__(
        self,
        name: str,
        default: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Attribute] = None,
        parent: Attribute = None,
    ) -> None:
        super().__init__(
            name=name,
            default=default,
            listeners=listeners,
            children=children,
            parent=parent,
        )

    @event_func
    def get(self) -> Any:
        self._trigger_listener(Event("get", None))
        return deepcopy(self.value)

    @event_func
    def set(self, value: Any) -> bool:
        self.value = value
        self._trigger_listener(Event("set", {"value": value}))
        return True
