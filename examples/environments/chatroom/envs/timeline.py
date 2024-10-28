# -*- coding: utf-8 -*-
"""An env representing a timeline."""

from typing import List, Any, Optional
from agentscope.environment import (
    Env,
    BasicEnv,
    event_func,
)
from agentscope.environment.event import Getable


class Timeline(BasicEnv, Getable):
    """A timeline env."""

    def __init__(
        self,
        name: str,
        start: int,
        unit: int = 1,
        end: Optional[int] = None,
        children: List[Env] = None,
    ) -> None:
        super().__init__(
            name=name,
            children=children,
        )
        self.cur_time = start
        self.unit = unit
        self.max_value = end

    def get(self) -> Any:
        return self.cur_time

    @event_func
    def step(self) -> None:
        """Step the timeline."""
        self.cur_time += self.unit

    def run(self) -> None:
        """Run the timeline."""
        while self.max_value is None or (self.cur_time < self.max_value):
            self.step()
