# -*- coding: utf-8 -*-
"""An attribute representing a timeline."""

from typing import List, Any, Optional
from ..attribute import BasicAttribute, Attribute
from ..event import event_func, Getable


class Timeline(BasicAttribute, Getable):
    """A timeline attribute."""

    def __init__(
        self,
        name: str,
        start: int,
        unit: int = 1,
        end: Optional[int] = None,
        children: List[Attribute] = None,
        parent: Attribute = None,
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
        return self.value

    @event_func
    def step(self) -> None:
        """Step the timeline."""
        self._value += self.unit

    def run(self) -> None:
        """Run the timeline."""
        while self.max_value is None or (self.value < self.max_value):
            self.step()
