# -*- coding: utf-8 -*-
"""A common base class for AgentBase and PipelineBase"""
from abc import ABC
from abc import abstractmethod
from typing import Any


class Operator(ABC):
    """
    Abstract base class `Operator` defines a protocol for classes that
    implement callable behavior.
    The class is designed to be subclassed with an overridden `__call__`
    method that specifies the execution logic for the operator.
    """

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> dict:
        """Calling function"""
