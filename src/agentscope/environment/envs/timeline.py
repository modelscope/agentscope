# -*- coding: utf-8 -*-
"""An env representing a timeline."""

from typing import List, Any, Optional
from ..env import BasicEnv, Env
from ..event import event_func, Getable


class Timeline(BasicEnv, Getable):
    """A timeline env."""

    def __init__(
        self,
        name: str,
        start: int,
        unit: int = 1,
        end: Optional[int] = None,
        children: List[Env] = None,
        parent: Env = None,
    ) -> None:
        super().__init__(
            name=name,
            value=start,
            children=children,
            parent=parent,
        )
        self.unit = unit
        self.max_value = end

    @event_func
    def get(self) -> Any:
        return self._value

    @event_func
    def step(self) -> None:
        """Step the timeline."""
        self._value += self.unit

    def run(self) -> None:
        """Run the timeline."""
        while self.max_value is None or (self._value < self.max_value):
            self.step()
