# -*- coding: utf-8 -*-
"""The base class for memory actions."""
import json
import os
from typing import (
    Sequence,
    Optional,
    Callable,
    Union,
    List,
)

from loguru import logger

from ..message import Msg, deserialize


class MemoryActions:
    """The basic memory actions for memory store, which is data agnostic. The
    basic data operations are implemented in the memory store, and we just
    provide the placeholder methods for the memory storage."""

    def contain(self, msg: Msg) -> bool:
        """Check if the message is already in the memory by comparing the
        message id.

        Args:
            msg (`Msg`):
                The message to be checked.
        """
        return self._contain(msg.id)

    def add(
        self,
        messages: Union[Sequence[Msg], Msg, None],
        allow_duplicate: bool = True,
    ) -> None:
        """Adding new memory fragment, depending on how the memory are stored

        Args:
            messages (`Union[Sequence[Msg], Msg, None]`):
                Memories to be added.
            allow_duplicate (`bool`, defaults to `True`):
                Whether to allow duplicate memory fragments.
        """
        if messages is None:
            return

        if not isinstance(messages, Sequence):
            record_messages = [messages]
        else:
            record_messages = messages

        if not allow_duplicate:
            # Check if the memory already exists by checking the message id
            for msg in record_messages:
                if not self.contain(msg):
                    self._insert(msg)
                else:
                    logger.warning(
                        f"Memory {msg} already exists, "
                        f"skipping the addition.",
                    )
        else:
            for msg in record_messages:
                self._insert(msg)

    def delete(self, index: Union[int, List[int]]) -> None:
        """Delete memory fragment, depending on how the memory are stored
        and matched

        Args:
            index (Union[int, List[int]]):
                Indices of the memory fragments to delete
        """
        if self.size() == 0:
            logger.warning(
                "Skip delete operation for the empty memory.",
            )
            return

        if isinstance(index, int):
            index = [index]

        if isinstance(index, list):
            # Delete the memory in reverse order to avoid the index change
            for i in sorted(set(index), reverse=True):
                if i >= self._size():
                    logger.warning(f"Index {i} out of range, skip delete.")
                else:
                    self._delete(i)
        else:
            raise TypeError(
                f"Invalid index type {type(index)}, "
                f"int or list[int] is expected",
            )

    def export(
        self,
        file_path: Optional[str] = None,
    ) -> str:
        """Export memory, depending on how the memory are stored

        Args:
            file_path (`Optional[str]`, defaults to `None`):
                The file path to save the memory.
        """

        return self._export(file_path)

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
        if isinstance(memories, str):
            if os.path.isfile(memories):
                with open(memories, "r", encoding="utf-8") as f:
                    load_memories = deserialize(f.read())
            else:
                try:
                    load_memories = deserialize(memories)
                    if not isinstance(load_memories, dict) and not isinstance(
                        load_memories,
                        list,
                    ):
                        logger.warning(
                            "The memory loaded by json.loads is "
                            "neither a dict nor a list, which may "
                            "cause unpredictable errors.",
                        )
                except json.JSONDecodeError as e:
                    raise json.JSONDecodeError(
                        f"Cannot load [{memories}] via " f"json.loads.",
                        e.doc,
                        e.pos,
                    )
        else:
            load_memories = memories

        if not isinstance(load_memories, list):
            load_memories = [load_memories]

        self._load(load_memories, overwrite)

        # overwrite the original memories after loading the new ones
        if overwrite:
            self.clear()

        self.add(load_memories)

    def clear(self) -> None:
        """Clean memory."""
        self._clear()

    def size(self) -> int:
        """Return the number of memory fragments."""
        return self._size()

    def get_memory(
        self,
        recent_n: Optional[int] = None,
        filter_func: Optional[Callable[[int, dict], bool]] = None,
    ) -> List[Msg]:
        """Get the memory from the memory store.

        Args:
            recent_n (`Optional[int]`, default `None`):
                The last number of memories to return.
            filter_func
                (`Callable[[int, dict], bool]`, default to `None`):
                The function to filter memories, which take the index and
                memory unit as input, and return a boolean value.

        Returns:
            `List[Msg]`: The list of memory units.
        """
        # extract the recent `recent_n` entries in memories
        if recent_n is None:
            memories = [self._get(_) for _ in range(self._size())]

        else:
            if recent_n > self.size():
                logger.warning(
                    "The retrieved number of memories {} is "
                    "greater than the total number of memories {"
                    "}",
                    recent_n,
                    self.size(),
                )
            size = self._size()
            memories = [self._get(_) for _ in range(size - recent_n, size)]

        # filter the memories
        if filter_func is not None:
            memories = [_ for i, _ in enumerate(memories) if filter_func(i, _)]

        return memories

    # Placeholder methods for the memory storage
    def _insert(self, msg: Msg, index: int = -1) -> None:
        raise NotImplementedError(
            "The `_insert` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )

    def _delete(self, index: int) -> None:
        raise NotImplementedError(
            "The `_delete` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )

    def _get(self, index: int) -> Msg:
        raise NotImplementedError(
            "The `_get` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )

    def _update(self, index: int, new_msg: Msg) -> None:
        raise NotImplementedError(
            "The `_update` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )

    def _size(self) -> int:
        raise NotImplementedError(
            "The `_size` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )

    def _clear(self) -> None:
        raise NotImplementedError(
            "The `_clear` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )

    def _contain(self, msg_id: str) -> bool:
        raise NotImplementedError(
            "The `_contain` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )

    def _export(self, file_path: Optional[str] = None) -> str:
        raise NotImplementedError(
            "The `_export` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )

    def _load(self, memories: List[Msg], overwrite: bool) -> None:
        raise NotImplementedError(
            "The `_load` method should be implemented in a child class"
            "of `MemoryStoreBase`.",
        )
