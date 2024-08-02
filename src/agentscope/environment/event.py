# -*- coding: utf-8 -*-
"""The events which can be bound to attributes."""
from abc import ABC, abstractmethod
from typing import Callable, Any


def event(func: Callable) -> Callable:
    """A decorator to register an event function.

    Args:
        func (`Callable`): The event function.

    Returns:
        `Callable`: The decorated function.
    """
    func._is_event = True  # pylint: disable=W0212
    return func


class Get(ABC):
    """Representing an attribute whose value can be obtained."""

    @abstractmethod
    def get(self) -> Any:
        """Get the value of the attribute.

        Returns:
            `Any`: The value of the attribute.
        """


class Set(ABC):
    """Representing an attribute whose value can be set."""

    @abstractmethod
    def set(self, value: Any) -> bool:
        """Set the value of the attribute.

        Args:
            value (`Any`): The new value of the attribute.

        Returns:
            `bool`: Whether the value was set successfully.
        """


class Move2D(ABC):
    """A class representing an attribute can be moved in 2D."""

    @abstractmethod
    def move(self, x: float, y: float) -> bool:
        """Move the attribute in 2D with given vector.

        Args:
            x (`float`): The movement in x direction.
            y (`float`): The movement in y direction.

        Returns:
            `bool`: Whether the movement was successful.
        """


class Hold(ABC):
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
