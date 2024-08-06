# -*- coding: utf-8 -*-
"""The basic memory store interface, which defines the basic data related
operations."""
from abc import ABC, abstractmethod
from typing import Optional, List

from agentscope.message import Msg


class MemoryStoreBase(ABC):
    """The basic memory store interface, which defines the basic data related
    operations for memory store."""

    @abstractmethod
    def _insert(self, msg: Msg, index: int = -1) -> None:
        """Insert a new memory unit

        Args:
            msg (`Msg`):
                The memory unit to be inserted.
            index (`int`, defaults to `-1`):
                The index to insert the memory unit. If the index is `-1`, the
                memory unit will be appended to the memory store
        """

    @abstractmethod
    def _delete(self, index: int) -> Msg:
        """Delete a memory unit by index

        Args:
            index (`int`):
                The index of the memory unit to be deleted.
        """

    @abstractmethod
    def _get(self, index: int) -> Msg:
        """Get a memory unit by index

        Args:
            index (`int`):
                The index of the memory unit to be retrieved.
        """

    @abstractmethod
    def _update(self, index: int, new_msg: Msg) -> None:
        """Update a memory unit by index

        Args:
            index (`int`):
                The index of the memory unit to be updated.
            new_msg (`Msg`):
                The new memory unit to replace the old one
        """

    @abstractmethod
    def _size(self) -> int:
        """The size of the memory store"""

    @abstractmethod
    def _clear(self) -> None:
        """Clear the memory store"""

    @abstractmethod
    def _contain(self, msg_id: str) -> bool:
        """Check if the memory store contains a memory unit by msg id

        Args:
            msg_id (`str`):
                The id of the memory unit to be checked.
        """

    @abstractmethod
    def _export(self, file_path: Optional[str] = None) -> str:
        """Export the memory store to a file

        Args:
            file_path (`Optional[str]`, defaults to `None`):
                The file path to save the memory store
        """

    @abstractmethod
    def _load(self, memories: List[Msg], overwrite: bool) -> None:
        """Load the memory from a file

        Args:
            memories (`List[Msg]`):
                The list of memory units to be loaded.
            overwrite (`bool`):
                Whether to overwrite the current memory store.
        """
