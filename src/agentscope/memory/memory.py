# -*- coding: utf-8 -*-
"""
Base class for memory

TODO: a abstract class for a piece of memory
TODO: data structure to organize multiple memory pieces in memory class
"""

from abc import ABC, abstractmethod
from typing import Iterable, Sequence
from typing import Optional
from typing import Union
from typing import Callable

from ..message import Msg


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
        Args:
            config (`dict`): Configuration of resetting this memory
        """
        self.config = config

    @abstractmethod
    def get_memory(
        self,
        recent_n: Optional[int] = None,
        filter_func: Optional[Callable[[int, dict], bool]] = None,
    ) -> list:
        """
        Return a certain range (`recent_n` or all) of memory,
        filtered by `filter_func`
        Args:
            recent_n (int, optional):
                indicate the most recent N memory pieces to be returned.
            filter_func (Optional[Callable[[int, dict], bool]]):
                filter function to decide which pieces of memory should
                be returned, taking the index and a piece of memory as
                input and return True (return this memory) or False
                (does not return)
        """

    @abstractmethod
    def add(
        self,
        memories: Union[Sequence[Msg], Msg, None],
    ) -> None:
        """
        Adding new memory fragment, depending on how the memory are stored
        Args:
            memories (Union[Sequence[Msg], Msg, None]):
                Memories to be added.
        """

    @abstractmethod
    def delete(self, index: Union[Iterable, int]) -> None:
        """
        Delete memory fragment, depending on how the memory are stored
        and matched
        Args:
            index (Union[Iterable, int]):
                indices of the memory fragments to delete
        """

    @abstractmethod
    def load(
        self,
        memories: Union[str, list[Msg], Msg],
        overwrite: bool = False,
    ) -> None:
        """
        Load memory, depending on how the memory are passed, design to load
        from both file or dict
        Args:
            memories (Union[str, list[Msg], Msg]):
                memories to be loaded.
                If it is in str type, it will be first checked if it is a
                file; otherwise it will be deserialized as messages.
                Otherwise, memories must be either in message type or list
                 of messages.
            overwrite (bool):
                if True, clear the current memory before loading the new ones;
                if False, memories will be appended to the old one at the end.
        """

    @abstractmethod
    def export(
        self,
        file_path: Optional[str] = None,
        to_mem: bool = False,
    ) -> Optional[list]:
        """
        Export memory, depending on how the memory are stored
        Args:
            file_path (Optional[str]):
                file path to save the memory to.
            to_mem (Optional[str]):
                if True, just return the list of messages in memory
        Notice: this method prevents file_path is None when to_mem
        is False.
        """

    @abstractmethod
    def clear(self) -> None:
        """Clean memory, depending on how the memory are stored"""

    @abstractmethod
    def size(self) -> int:
        """Returns the number of memory segments in memory."""
        raise NotImplementedError
