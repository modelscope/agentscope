# -*- coding: utf-8 -*-
"""A 2D map env with mutiple child envibtues
who have Location2D position"""
import math
from typing import List
from agentscope.exception import (
    EnvNotFoundError,
    EnvTypeError,
    EnvAlreadyExistError,
    EnvListenerError,
)
from agentscope.environment import (
    Env,
    BasicEnv,
    EventListener,
    Event,
    event_func,
)
from agentscope.environment.event import Movable2D


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


class Map2D(BasicEnv):
    """A 2D Map env"""

    def __init__(
        self,
        name: str,
        children: List[Env] = None,
    ) -> None:
        """Initialize a Map2D env.

        Args:
            name (`str`): The name of the env.
            children (`List[envibute]`): The children of the env. Note
            that all children must be Movable2D.
        """
        for child in children if children else []:
            if not isinstance(child, Movable2D):
                raise EnvTypeError(
                    child.name,
                    "Moveable2D",
                )
        super().__init__(
            name=name,
            children=children,
        )

    @event_func
    def move_child_to(self, env_name: str, x: float, y: float) -> None:
        """Move the child env to a position.

        Args:
            env_name (`str`): The name of the env to move.
            x (`float`): The x coordinate of the new position.
            y (`float`): The y coordinate of the new position.
        """
        if env_name in self.children:
            self.children[env_name].move_to(x, y)
        else:
            raise EnvNotFoundError(env_name)

    @event_func
    def register_point(self, point: Env) -> None:
        """Register a point env to the map.

        Args:
            point (`envibute`): The point env to register.
        """
        if not isinstance(point, Movable2D):
            raise EnvTypeError(point.name, "Moveable2D")
        if not self.add_child(point):
            raise EnvAlreadyExistError(point.name)

    # Syntactic sugar, not an event function
    def in_range_of(
        self,
        env_name: str,
        listener: EventListener,
        distance: float,
        distance_type: str = "euclidean",
    ) -> None:
        """Set a listenerwhich is activated when the distance from
        any env in the map to `env_name` is not larger than
        `distance`.

        Args:
            env_name (`str`): The name of the env that is the center.
            listener (`EventListener`): The listener to activate when the
                distance is not larger than `distance`.
            distance (`float`): The distance threshold.
            distance_type (`str`): The distance type, either "euclidean" or
                "manhattan".
        """
        if env_name not in self.children:
            raise EnvNotFoundError(env_name)

        class EnterRangeListener(EventListener):
            """A middleware that activates `target_listener` when any env
            is in range of `center_env`"""

            def __init__(
                self,
                name: str,
                center_env: Env,
                target_listener: EventListener,
                distance: float,
                distance_type: str = "euclidean",
            ) -> None:
                super().__init__(name=name)
                self.center_env = center_env
                self.target_listener = target_listener
                self.distance = distance
                self.distance_type = distance_type

            def __call__(self, env: Env, event: Event) -> None:
                if event.args["env_name"] == self.center_env.name:
                    # center is moving, recalculate all distance
                    x1, y1 = self.center_env.get_position()
                    for child in env.children.values():
                        if child.name == self.center_env.name:
                            continue
                        x2, y2 = child.get_position()
                        if (
                            distance2d(x1, y1, x2, y2, self.distance_type)
                            <= self.distance
                        ):
                            self.target_listener(
                                env,
                                Event(
                                    name="in_range",
                                    args={
                                        "env_name": child.name,
                                        "x": x2,
                                        "y": y2,
                                    },
                                ),
                            )
                    return
                else:
                    x1, y1 = self.center_env.get_position()
                    x2 = event.args["x"]  # type: ignore[index]
                    y2 = event.args["y"]  # type: ignore[index]
                    if (
                        distance2d(x1, y1, x2, y2, self.distance_type)
                        <= self.distance
                    ):
                        self.target_listener(
                            env,
                            Event(name="in_range", args=event.args),
                        )

        if not self.add_listener(
            "move_child_to",
            listener=EnterRangeListener(
                name=f"in_range_of_{env_name}_{distance}",
                center_env=self.children[env_name],
                target_listener=listener,
                distance=distance,
                distance_type=distance_type,
            ),
        ):
            raise EnvListenerError("Fail to add listener.")

        # trigger listener for existing envs
        x1, y1 = self.children[env_name].get_position()
        for child in self.children.values():
            if child.name == env_name:
                continue
            x2, y2 = child.get_position()
            if distance2d(x1, y1, x2, y2, distance_type) <= distance:
                listener(
                    child,
                    Event(
                        name="in_range",
                        args={
                            "env_name": child.name,
                            "x": x2,
                            "y": y2,
                        },
                    ),
                )

    def out_of_range_of(
        self,
        env_name: str,
        listener: EventListener,
        distance: float,
        distance_type: str = "euclidean",
    ) -> None:
        """Set a listener which is activated when the distance from
        any env in the map to `env_name` is larger than
        `distance`.
        Args:
            env_name (`str`): The name of the env that is the center.
            listener (`EventListener`): The listener to activate when the
                distance is larger than `distance`.
            distance (`float`): The distance threshold.
            distance_type (`str`): The distance type, either "euclidean" or
                "manhattan".
        """
        if env_name not in self.children:
            raise EnvNotFoundError(env_name)

        class OutofRange(EventListener):
            """A middleware that activates `target_listener` when any env
            is out of range of `center_env`"""

            def __init__(
                self,
                name: str,
                center_env: Env,
                target_listener: EventListener,
                distance: float,
                distance_type: str = "euclidean",
            ) -> None:
                super().__init__(name=name)
                self.center_env = center_env
                self.target_listener = target_listener
                self.distance = distance
                self.distance_type = distance_type

            def __call__(self, env: Env, event: Event) -> None:
                if event.args["env_name"] == self.center_env.name:
                    # center is moving, recalculate all distance
                    x1, y1 = self.center_env.get_position()
                    for child in env.children.values():
                        if child.name == self.center_env.name:
                            continue
                        x2, y2 = child.get_position()
                        if (
                            distance2d(x1, y1, x2, y2, self.distance_type)
                            > self.distance
                        ):
                            self.target_listener(
                                env,
                                Event(
                                    name="out_of_range",
                                    args={
                                        "env_name": child.name,
                                        "x": child.get_position()[0],
                                        "y": child.get_position()[1],
                                    },
                                ),
                            )
                else:
                    x1, y1 = self.center_env.get_position()
                    x2 = event.args["x"]  # type: ignore[index]
                    y2 = event.args["y"]  # type: ignore[index]
                    if (
                        distance2d(x1, y1, x2, y2, self.distance_type)
                        > self.distance
                    ):
                        self.target_listener(
                            env,
                            Event(name="out_of_range", args=event.args),
                        )

        if not self.add_listener(
            "move_child_to",
            listener=OutofRange(
                name=f"out_of_range_of_{env_name}_{distance}",
                center_env=self.children[env_name],
                target_listener=listener,
                distance=distance,
                distance_type=distance_type,
            ),
        ):
            raise EnvListenerError("Fail to add listener.")
        # trigger listener for existing envs
        x1, y1 = self.children[env_name].get_position()
        for child in self.children.values():
            if child.name == env_name:
                continue
            x2, y2 = child.get_position()
            if distance2d(x1, y1, x2, y2, distance_type) > distance:
                listener(
                    child,
                    Event(
                        name="out_of_range",
                        args={
                            "env_name": child.name,
                            "x": x2,
                            "y": y2,
                        },
                    ),
                )
