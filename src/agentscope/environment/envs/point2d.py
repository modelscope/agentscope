# -*- coding: utf-8 -*-
""" An Env that represented a 2D location point."""
from typing import List, Tuple, Any

from ..env import Env, BasicEnv, EventListener
from .mutable import MutableEnv
from ..event import event_func, Event, Movable2D


class Point2D(BasicEnv, Movable2D):
    """A Point in 2D space."""

    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Env] = None,
        parent: Env = None,
    ) -> None:
        super().__init__(name, (x, y), listeners, children, parent)

    @event_func
    def move_to(self, x: float, y: float) -> bool:
        """Move the point to a new position."""
        cur_loc = {
            "x": self._value[0],  # type: ignore[has-type]
            "y": self._value[1],  # type: ignore[has-type]
        }
        self._value = (x, y)
        self._trigger_listener(
            Event("move_to", {"new": {"x": x, "y": y}, "old": cur_loc}),
        )
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
        self.move_to(self._value[0] + x, self._value[1] + y)
        return True

    @event_func
    def get_position(self) -> Tuple[float, float]:
        """Get the current position of the point.

        Returns:
            `Tuple[float, float]`: The current position of the point.
        """
        value = (self._value[0], self._value[1])
        self._trigger_listener(Event("get", {}))
        return value


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
        parent: Env = None,
    ) -> None:
        super().__init__(name, value, listeners, children, parent)
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
