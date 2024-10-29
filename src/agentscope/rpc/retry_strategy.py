# -*- coding: utf-8 -*-
"""
Timeout retry strategies
"""
from __future__ import annotations
import time
import random
import inspect
from abc import ABC, abstractmethod
from typing import Callable, Any
from functools import partial
from loguru import logger


class RetryBase(ABC):
    """The base class for all retry strategies"""

    @abstractmethod
    def retry(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Retry the func when any exception occurs"""

    def __call__(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Call the retry method"""
        return self.retry(func, *args, **kwargs)

    @classmethod
    def load_dict(cls, data: dict) -> RetryBase:
        """Load the retry strategy from a dict"""
        retry_type = data.pop("type", None)
        if retry_type == "fixed":
            return RetryFixedTimes(**data)
        elif retry_type == "expential":
            return RetryExpential(**data)
        else:
            raise NotImplementedError(
                f"Unknown retry strategy type: {retry_type}",
            )


class RetryFixedTimes(RetryBase):
    """
    Retry a fixed number of times, and wait a fixed delay time between each attempt.

    Init dict format:

        - type: 'fixed'
        - max_retries (`int`): The max retry times
        - delay (`float`): The delay time between each attempt

    .. code-block:: python

        retry = RetryBase.load_dict({
            "type": "fixed",
            "max_retries": 10,
            "delay": 5,
        })
    """

    def __init__(self, max_retries: int = 10, delay: float = 5) -> None:
        """Initialize the retry strategy

        Args:
            max_retries (`int`): The max retry times
            delay (`float`): The delay time between each attempt
        """
        self.max_retries = max_retries
        self.delay = delay

    def retry(  # pylint: disable=R1710
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        exception_type = kwargs.pop("expect_exception_type", Exception)
        func = partial(func, *args, **kwargs)
        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except exception_type as e:
                if attempt == self.max_retries:
                    raise TimeoutError("Max timeout exceeded.") from e
                random_delay = (random.random() + 0.5) * self.delay
                frame_info = inspect.getframeinfo(
                    inspect.currentframe().f_back,  # type: ignore[arg-type]
                )
                file_name = frame_info.filename
                line_number = frame_info.lineno
                logger.debug(
                    f"Attempt {attempt + 1} at [{file_name}:{line_number}] failed:"
                    f"\n{e}.\nRetrying in {random_delay:.2f} seconds...",
                )
                time.sleep(random_delay)
        logger.error(f"Max timeout exceeded at [{file_name}:{line_number}].")
        raise TimeoutError("Max retry exceeded.")


class RetryExpential(RetryBase):
    """
    Retry with exponential backoff, which means the delay time will increase exponentially.

    Init dict format:

        - type: 'expential'
        - max_retries (`int`): The max retry times
        - base_delay (`float`): The base delay time
        - max_delay (`float`): The max delay time, which will be used if the calculated delay time
        - exceeds it.

    .. code-block:: python

        retry = RetryBase.load_dict({
            "type": "expential",
            "max_retries": 10,
            "base_delay": 5,
            "max_delay": 300,
        })
    """

    def __init__(
        self,
        max_retries: int = 10,
        base_delay: float = 5,
        max_delay: float = 300,
    ) -> None:
        """Initialize the retry strategy

        Args:
            max_retries (`int`): The max retry times
            base_delay (`float`): The base delay time
            max_delay (`float`): The max delay time
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def retry(  # pylint: disable=R1710
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        exception_type = kwargs.pop("expect_exception_type", Exception)
        func = partial(func, *args, **kwargs)
        delay = self.base_delay
        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except exception_type as e:
                if attempt == self.max_retries:
                    raise TimeoutError("Max timeout exceeded.") from e
                random_delay = min(
                    (random.random() + 0.5) * delay,
                    self.max_delay,
                )
                frame_info = inspect.getframeinfo(
                    inspect.currentframe().f_back,  # type: ignore[arg-type]
                )
                file_name = frame_info.filename
                line_number = frame_info.lineno
                logger.debug(
                    f"Attempt {attempt + 1} at [{file_name}:{line_number}] failed:"
                    f"\n{e}.\nRetrying in {random_delay:.2f} seconds...",
                )
                time.sleep(random_delay)
                delay *= 2
        logger.error(f"Max timeout exceeded at [{file_name}:{line_number}].")
        raise TimeoutError("Max retry exceeded.")


_DEAFULT_RETRY_STRATEGY = RetryFixedTimes(max_retries=10, delay=5)
