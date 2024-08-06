# -*- coding: utf-8 -*-
"""A attribute that is immutable and only support get."""

from typing import List, Any
from copy import deepcopy

from ..attribute import Attribute, BasicAttribute, EventListener
from ..event import event_func, Event, Getable


class ImmutableAttribute(BasicAttribute, Getable):
    """An immutable attribute that can be get and set."""

    def __init__(
        self,
        name: str,
        value: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Attribute] = None,
        parent: Attribute = None,
    ) -> None:
        super().__init__(
            name=name,
            value=value,
            listeners=listeners,
            children=children,
            parent=parent,
        )

    @event_func
    def get(self) -> Any:
        value = deepcopy(self._value)
        self._trigger_listener(Event("get", {}))
        return value
