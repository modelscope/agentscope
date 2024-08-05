# -*- coding: utf-8 -*-
""" A Attribute that represented a 2D location point."""
from typing import List, Tuple, Any

from ..attribute import Attribute, EventListener
from .basic import BasicAttribute
from ..event import event_func, Event, Movable2D


class Point2D(Attribute, Movable2D):
    """A Point in 2D space."""

    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Attribute] = None,
        parent: Attribute = None,
    ) -> None:
        super().__init__(name, (x, y), listeners, children, parent)

    @event_func
    def move_to(self, x: float, y: float) -> bool:
        """Move the point to a new position."""
        cur_loc = {"x": self.value[0], "y": self.value[1]}
        self.value = (x, y)
        self._trigger_listener(
            Event("move_to", {"new": {"x": x, "y": y}, "old": cur_loc}),
        )
        return True

    # Syntactic sugar, not an event function
    def move_by(self, x: float, y: float) -> bool:
        """Move the attribute in 2D by the given vector.

        Args:
            x (`float`): The movement in x direction.
            y (`float`): The movement in y direction.

        Returns:
            `bool`: Whether the movement was successful.
        """
        self.move_to(self.value[0] + x, self.value[1] + y)
        return True

    @event_func
    def get_position(self) -> Tuple[float, float]:
        """Get the current position of the point.

        Returns:
            `Tuple[float, float]`: The current position of the point.
        """
        value = (self.value[0], self.value[1])
        self._trigger_listener(Event("get", {}))
        return value


class AttributeWithPoint2D(BasicAttribute, Movable2D):
    """An enhanced basicAttribute whose child `position` is a `Point2D`
    instance."""

    def __init__(
        self,
        name: str,
        value: Any,
        x: float,
        y: float,
        listeners: dict[str, List[EventListener]] = None,
        children: List[Attribute] = None,
        parent: Attribute = None,
    ) -> None:
        super().__init__(name, value, listeners, children, parent)
        self.add_child(Point2D("position", x, y))

    @event_func
    def move_to(self, x: float, y: float) -> bool:
        """Move the point to a new position."""
        return self.children["position"].move_to(x, y)

    # Syntactic sugar, not an event function
    def move_by(self, x: float, y: float) -> bool:
        """Move the attribute in 2D by the given vector.."""
        return self.children["position"].move_by(x, y)

    @event_func
    def get_position(self) -> Tuple[float, float]:
        """Get the current position of the point.

        Returns:
            `Tuple[float, float]`: The current position of the point.
        """
        return self.children["position"].get_position()
