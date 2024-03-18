# -*- coding: utf-8 -*-
"""
Base class for memory

TODO: a abstract class for a piece of memory
TODO: data structure to organize multiple memory pieces in memory class
"""

from abc import ABC, abstractmethod
from typing import Iterable
from typing import Optional
from typing import Union
from typing import Callable


class MemoryBase(ABC):
    """Base class for memory."""

    _version: int = 1

    def __init__(
        self,
        config: Optional[dict] = None,
    ) -> None:
        """MemoryBase is a base class for memory of agents.

        Args:
            config (`Optional[dict]`, defaults to `None`):
                Configuration of this memory.
        """
        self.config = {} if config is None else config

    def update_config(self, config: dict) -> None:
        """
        Configure memory as specified in config
        """
        self.config = config

    @abstractmethod
    def get_memory(
        self,
        recent_n: Optional[int] = None,
        filter_func: Optional[Callable[[int, dict], bool]] = None,
    ) -> list:
        """
        Return a certain range (`recent_n` or all) of memory, filtered by
        `filter_func`
        """

    @abstractmethod
    def add(self, memories: Union[list[dict], dict, None]) -> None:
        """
        Adding new memory fragment, depending on how the memory are stored
        """

    @abstractmethod
    def delete(self, index: Union[Iterable, int]) -> None:
        """
        Delete memory fragment, depending on how the memory are stored
        and matched
        """

    @abstractmethod
    def load(
        self,
        memories: Union[str, dict, list],
        overwrite: bool = False,
    ) -> None:
        """
        Load memory, depending on how the memory are passed, design to load
        from both file or dict
        """

    @abstractmethod
    def export(
        self,
        to_mem: bool = False,
        file_path: Optional[str] = None,
    ) -> Optional[list]:
        """Export memory, depending on how the memory are stored"""

    @abstractmethod
    def clear(self) -> None:
        """Clean memory, depending on how the memory are stored"""

    @abstractmethod
    def size(self) -> int:
        """Returns the number of memory segments in memory."""
        raise NotImplementedError
