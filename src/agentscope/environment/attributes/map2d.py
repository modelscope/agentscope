# -*- coding: utf-8 -*-
"""A 2D map attribute with mutiple child attribtues
who have Location2D position"""
import math
from typing import List
from ...exception import (
    EnvAttributeNotFoundError,
    EnvAttributeTypeError,
    EnvAttributeAlreadyExistError,
    EnvListenerError,
)
from ..attribute import Attribute, EventListener
from ..event import event_func, Event, Movable2D


def distance2d(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    distance_type: str = "euclidean",
) -> float:
    """Calculate the distance between two points"""
    if distance_type == "euclidean":
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    else:
        # else calculate manhattan distance
        return abs(x2 - x1) + abs(y2 - y1)


class Map2D(Attribute):
    """A 2D Map attribute"""

    def __init__(
        self,
        name: str,
        children: List[Attribute] = None,
        parent: Attribute = None,
    ) -> None:
        """Initialize a Map2D attribute.

        Args:
            name (`str`): The name of the attribute.
            children (`List[Attribute]`): The children of the attribute. Note
            that all children must be Movable2D.
            parent (`Attribute`): The parent of the attribute.
        """
        for child in children if children else []:
            if not isinstance(child, Movable2D):
                raise EnvAttributeTypeError(
                    child.name,
                    "Moveable2D",
                )
        super().__init__(
            name=name,
            default=None,
            children=children,
            parent=parent,
        )

    @event_func
    def move_attr_to(self, attr_name: str, x: float, y: float) -> None:
        """Move the attribute to a position.

        Args:
            attr_name (`str`): The name of the attribute to move.
            x (`float`): The x coordinate of the new position.
            y (`float`): The y coordinate of the new position.
        """
        if attr_name in self.children:
            self.children[attr_name].move_to(x, y)
            self._trigger_listener(
                Event(
                    name="move_attr_to",
                    args={
                        "attr_name": attr_name,
                        "x": x,
                        "y": y,
                    },
                ),
            )
        else:
            raise EnvAttributeNotFoundError(attr_name)

    @event_func
    def register_point(self, point: Attribute) -> None:
        """Register a point attribute to the map.

        Args:
            point (`Attribute`): The point attribute to register.
        """
        if not isinstance(point, Movable2D):
            raise EnvAttributeTypeError(point.name, "Moveable2D")
        if not self.add_child(point):
            raise EnvAttributeAlreadyExistError(point.name)
        self._trigger_listener(
            Event(
                name="register_point",
                args={
                    "point": point.name,
                },
            ),
        )

    # Syntactic sugar, not an event function
    def in_range_of(
        self,
        attr_name: str,
        listener: EventListener,
        distance: float,
        distance_type: str = "euclidean",
    ) -> None:
        """Set a listenerwhich is activated when the distance from
        any attribute in the map to `attr_name` is not larger than
        `distance`.

        Args:
            attr_name (`str`): The name of the attribute that is the center.
            listener (`EventListener`): The listener to activate when the
                distance is not larger than `distance`.
            distance (`float`): The distance threshold.
            distance_type (`str`): The distance type, either "euclidean" or
                "manhattan".
        """
        if attr_name not in self.children:
            raise EnvAttributeNotFoundError(attr_name)

        class EnterRangeListener(EventListener):
            """A middleware that activates `target_listener` when any attribute
            is in range of `center_attr`"""

            def __init__(
                self,
                name: str,
                center_attr: Attribute,
                target_listener: EventListener,
                distance: float,
                distance_type: str = "euclidean",
            ) -> None:
                super().__init__(name=name)
                self.center_attr = center_attr
                self.target_listener = target_listener
                self.distance = distance
                self.distance_type = distance_type

            def __call__(self, attr: Attribute, event: Event) -> None:
                if event.args["attr_name"] == self.center_attr.name:
                    # center is moving, recalculate all distance
                    x1, y1 = self.center_attr.get_position()
                    for child in attr.children.values():
                        if child.name == self.center_attr.name:
                            continue
                        x2, y2 = child.get_position()
                        if (
                            distance2d(x1, y1, x2, y2, self.distance_type)
                            <= self.distance
                        ):
                            self.target_listener(
                                attr,
                                Event(
                                    name="in_range",
                                    args={
                                        "attr_name": child.name,
                                        "x": x2,
                                        "y": y2,
                                    },
                                ),
                            )
                    return
                else:
                    x1, y1 = self.center_attr.get_position()
                    x2 = event.args["x"]  # type: ignore[index]
                    y2 = event.args["y"]  # type: ignore[index]
                    if distance2d(x1, y1, x2, y2) <= self.distance:
                        self.target_listener(
                            attr,
                            Event(name="in_range", args=event.args),
                        )

        if not self.add_listener(
            "move_attr_to",
            listener=EnterRangeListener(
                name=f"in_range_of_{attr_name}_{distance}",
                center_attr=self.children[attr_name],
                target_listener=listener,
                distance=distance,
                distance_type=distance_type,
            ),
        ):
            raise EnvListenerError("Fail to add listener.")

        # trigger listener for existing attributes
        x1, y1 = self.children[attr_name].get_position()
        for child in self.children.values():
            if child.name == attr_name:
                continue
            x2, y2 = child.get_position()
            if distance2d(x1, y1, x2, y2, distance_type) <= distance:
                listener(
                    child,
                    Event(
                        name="in_range",
                        args={
                            "attr_name": child.name,
                            "x": x2,
                            "y": y2,
                        },
                    ),
                )

    def out_of_range_of(
        self,
        attr_name: str,
        listener: EventListener,
        distance: float,
        distance_type: str = "euclidean",
    ) -> None:
        """Set a listener which is activated when the distance from
        any attribute in the map to `attr_name` is larger than
        `distance`.
        Args:
            attr_name (`str`): The name of the attribute that is the center.
            listener (`EventListener`): The listener to activate when the
                distance is larger than `distance`.
            distance (`float`): The distance threshold.
            distance_type (`str`): The distance type, either "euclidean" or
                "manhattan".
        """
        if attr_name not in self.children:
            raise EnvAttributeNotFoundError(attr_name)

        class OutofRange(EventListener):
            """A middleware that activates `target_listener` when any attribute
            is out of range of `center_attr`"""

            def __init__(
                self,
                name: str,
                center_attr: Attribute,
                target_listener: EventListener,
                distance: float,
                distance_type: str = "euclidean",
            ) -> None:
                super().__init__(name=name)
                self.center_attr = center_attr
                self.target_listener = target_listener
                self.distance = distance
                self.distance_type = distance_type

            def __call__(self, attr: Attribute, event: Event) -> None:
                if event.args["attr_name"] == self.center_attr.name:
                    # center is moving, recalculate all distance
                    x1, y1 = self.center_attr.get_position()
                    for child in attr.children.values():
                        if child.name == self.center_attr.name:
                            continue
                        x2, y2 = child.get_position()
                        if (
                            distance2d(x1, y1, x2, y2, self.distance_type)
                            > self.distance
                        ):
                            self.target_listener(
                                attr,
                                Event(
                                    name="out_of_range",
                                    args={
                                        "attr_name": child.name,
                                        "x": child.get_position()[0],
                                        "y": child.get_position()[1],
                                    },
                                ),
                            )
                else:
                    x1, y1 = self.center_attr.get_position()
                    x2 = event.args["x"]  # type: ignore[index]
                    y2 = event.args["y"]  # type: ignore[index]
                    if distance2d(x1, y1, x2, y2) > self.distance:
                        self.target_listener(
                            attr,
                            Event(name="out_of_range", args=event.args),
                        )

        if not self.add_listener(
            "move_attr_to",
            listener=OutofRange(
                name=f"out_of_range_of_{attr_name}_{distance}",
                center_attr=self.children[attr_name],
                target_listener=listener,
                distance=distance,
                distance_type=distance_type,
            ),
        ):
            raise EnvListenerError("Fail to add listener.")
        # trigger listener for existing attributes
        x1, y1 = self.children[attr_name].get_position()
        for child in self.children.values():
            if child.name == attr_name:
                continue
            x2, y2 = child.get_position()
            if distance2d(x1, y1, x2, y2, distance_type) > distance:
                listener(
                    child,
                    Event(
                        name="out_of_range",
                        args={
                            "attr_name": child.name,
                            "x": x2,
                            "y": y2,
                        },
                    ),
                )
