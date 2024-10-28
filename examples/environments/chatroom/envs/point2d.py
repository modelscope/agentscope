# -*- coding: utf-8 -*-
""" An Env that represented a 2D location point."""
from typing import List, Tuple, Any

from agentscope.environment import (
    Env,
    BasicEnv,
    EventListener,
    event_func,
)
from agentscope.environment.event import Movable2D
from .mutable import MutableEnv


class Point2D(BasicEnv, Movable2D):
    """A Point in 2D space."""

    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Env] = None,
    ) -> None:
        super().__init__(
            name=name,
            listeners=listeners,
            children=children,
        )
        self.x = x
        self.y = y

    @event_func
    def move_to(self, x: float, y: float) -> bool:
        """Move the point to a new position."""
        self.x = x
        self.y = y
        return True

    # Syntactic sugar, not an event function
    def move_by(self, x: float, y: float) -> bool:
        """Move the env in 2D by the given vector.

        Args:
            x (`float`): The movement in x direction.
            y (`float`): The movement in y direction.

        Returns:
            `bool`: Whether the movement was successful.
        """
        return self.move_to(self.x + x, self.y + y)

    @event_func
    def get_position(self) -> Tuple[float, float]:
        """Get the current position of the point.

        Returns:
            `Tuple[float, float]`: The current position of the point.
        """
        return (self.x, self.y)


class EnvWithPoint2D(MutableEnv, Movable2D):
    """An enhanced MutableEnv whose child `position` is a `Point2D`
    instance."""

    def __init__(
        self,
        name: str,
        value: Any,
        x: float,
        y: float,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Env] = None,
    ) -> None:
        super().__init__(
            name=name,
            value=value,
            listeners=listeners,
            children=children,
        )
        self.add_child(Point2D("position", x, y))

    @event_func
    def move_to(self, x: float, y: float) -> bool:
        """Move the point to a new position."""
        return self.children["position"].move_to(x, y)

    # Syntactic sugar, not an event function
    def move_by(self, x: float, y: float) -> bool:
        """Move the point in 2D by the given vector.."""
        return self.children["position"].move_by(x, y)

    @event_func
    def get_position(self) -> Tuple[float, float]:
        """Get the current position of the point.

        Returns:
            `Tuple[float, float]`: The current position of the point.
        """
        return self.children["position"].get_position()
