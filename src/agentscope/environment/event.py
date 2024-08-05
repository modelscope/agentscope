# -*- coding: utf-8 -*-
"""The events which can be bound to attributes."""
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional, Tuple


def event_func(func: Callable) -> Callable:
    """A decorator to register an event function.

    Args:
        func (`Callable`): The event function.

    Returns:
        `Callable`: The decorated function.
    """
    func._is_event = True  # pylint: disable=W0212
    return func


class Event:
    """A class representing the information of an event."""

    def __init__(self, name: str, args: Optional[dict] = None) -> None:
        self._name = name
        self._args = args

    @property
    def name(self) -> str:
        """Return the name of the event."""
        return self._name

    @property
    def args(self) -> Optional[dict]:
        """Return the arguments of the event."""
        return self._args


class Getable(ABC):
    """Representing an attribute whose value can be gotten."""

    @abstractmethod
    def get(self) -> Any:
        """Get the value of the attribute.

        Returns:
            `Any`: The value of the attribute.
        """


class Setable(ABC):
    """Representing an attribute whose value can be set."""

    @abstractmethod
    def set(self, value: Any) -> bool:
        """Set the value of the attribute.

        Args:
            value (`Any`): The new value of the attribute.

        Returns:
            `bool`: Whether the value was set successfully.
        """


class Movable2D(ABC):
    """A class representing an attribute can be moved in 2D."""

    @abstractmethod
    def move_by(self, x: float, y: float) -> bool:
        """Move the attribute in 2D by the given vector.

        Args:
            x (`float`): The movement in x direction.
            y (`float`): The movement in y direction.

        Returns:
            `bool`: Whether the movement was successful.
        """

    @abstractmethod
    def move_to(self, x: float, y: float) -> bool:
        """Move the attribute to the given position.

        Args:
            x (`float`): The x coordinate of the new position.
            y (`float`): The y coordinate of the new position.

        Returns:
            `bool`: Whether the movement was successful.
        """

    @abstractmethod
    def get_position(self) -> Tuple[float, float]:
        """Get the position of the attribute.

        Returns:
            `Tuple[float, float]`: The position of the attribute.
        """


class Holdable(ABC):
    """A class representing an attribute can be held,and during
    the holding period, all access behaviors except the owner
    are prohibited.
    """

    @abstractmethod
    def acquire(self, owner: str) -> bool:
        """Acquire the attribute.

        Args:
            owner (`str`): The owner of the attribute.

        Returns:
            `bool`: Whether the attribute was acquired successfully.
        """

    @abstractmethod
    def release(self, owner: str) -> bool:
        """Release the attribute.

        Args:
            owner (`str`): The owner of the attribute.

        Returns:
            `bool`: Whether the attribute was released successfully.
        """
