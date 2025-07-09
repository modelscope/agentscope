# -*- coding: utf-8 -*-
"""
This module defines a set of event classes for handling different types of
events that can occur during the execution of an application or process.
"""
from typing import Optional, Dict, Any


class Event:
    """Base class for all events."""

    def __init__(
        self,
        name: str,
        message: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.message = message
        self.context = context if context is not None else {}

    def __str__(self) -> str:
        context_str = ", ".join(
            f"{key}: {value}" for key, value in self.context.items()
        )
        return f"{self.name}: {self.message} | Context: {{{context_str}}}"


class NormalEvent(Event):
    """Event for normal operations that are part of the standard flow."""

    def __init__(
        self,
        name: str = "NormalEvent",
        message: str = "Normal operation.",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name=name, message=message, context=context)


class RetryEvent(Event):
    """
    Event for retrying an operation or task, as part of normal operations.
    """

    def __init__(
        self,
        name: str = "RetryEvent",
        message: str = "Retrying operation.",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name=name, message=message, context=context)


class StopEvent(Event):
    """Class for stop events."""

    def __init__(
        self,
        name: str = "StopEvent",
        message: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name=name, message=message, context=context)


class SuccessEvent(StopEvent):
    """Class for all success events. Such as stop on stop_nodes"""

    def __init__(
        self,
        name: str = "SuccessEvent",
        message: str = "Execution succeeded.",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name=name, message=message, context=context)


class FailureEvent(StopEvent):
    """Class for all failure events."""

    def __init__(
        self,
        name: str = "FailureEvent",
        message: str = "Execution failed.",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name=name, message=message, context=context)


class FallbackEvent(Event):
    """Class for triggering fallback strategies."""

    def __init__(
        self,
        name: str = "FallbackEvent",
        message: str = "Fallback strategy triggered.",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            name=name,
            message=message,
            context=context,
        )
