# -*- coding: utf-8 -*-
"""An env that is immutable and only support get."""

from typing import List, Any
from copy import deepcopy

from agentscope.environment import (
    Env,
    BasicEnv,
    EventListener,
    event_func,
)
from agentscope.environment.event import Getable


class ImmutableEnv(BasicEnv, Getable):
    """An immutable env that can be get and set."""

    def __init__(
        self,
        name: str,
        value: Any,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Env] = None,
    ) -> None:
        super().__init__(
            name=name,
            listeners=listeners,
            children=children,
        )
        self._value = value

    @property
    def value(self) -> Any:
        """Get the value of the env."""
        return self.get()

    @event_func
    def get(self) -> Any:
        return deepcopy(self._value)
