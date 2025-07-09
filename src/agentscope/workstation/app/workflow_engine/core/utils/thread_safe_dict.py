# -*- coding: utf-8 -*-
"""
This module provides a thread-safe dictionary implementation for write
operations. The `WriteThreadSafeDict` class inherits from the built-in dict
class and uses a threading lock to ensure that write operations are
thread-safe.
"""
import threading
from typing import Any


class WriteThreadSafeDict(dict):
    """
    A thread-safe dictionary for write operations. This class ensures
    that write operations are thread-safe using a threading lock.

    Inherits from the built-in dict class.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the WriteThreadSafeDict with optional dictionary
        arguments.

        :param args: Positional arguments for dictionary initialization.
        :param kwargs: Keyword arguments for dictionary initialization.
        """
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()

    def __setitem__(self, key: Any, value: Any) -> None:
        """
        Set the value for the given key in a thread-safe manner.

        :param key: The key where the value needs to be set.
        :param value: The value to set for the given key.
        """
        with self._lock:
            super().__setitem__(key, value)
