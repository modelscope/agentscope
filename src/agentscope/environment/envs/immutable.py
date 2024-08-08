# -*- coding: utf-8 -*-
"""An env that is immutable and only support get."""

from typing import List, Any
from copy import deepcopy

from ..env import Env, BasicEnv, EventListener
from ..event import event_func, Event, Getable


class ImmutableEnv(BasicEnv, Getable):
    """An immutable env that can be get and set."""

    def __init__(
        self,
        name: str,
        value: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Env] = None,
        parent: Env = None,
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
