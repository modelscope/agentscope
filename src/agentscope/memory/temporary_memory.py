# -*- coding: utf-8 -*-
"""The in-memory store for memory, which stores the memory in a list, as well
as a temporary memory class that inherits from the in-memory store and memory
actions."""
from typing import Optional, Callable, Union

from . import MemoryActions
from ..constants import Embedding
from ..manager import ModelManager
from ..memory import MemoryStoreBase
from ..message import Msg, serialize
from ..models import ModelResponse
from ..service import retrieve_from_list


class InMemoryStore(MemoryStoreBase):
    """The in-memory store for memory, which stores the memory in a list."""

    def __init__(
        self,
        embedding_model: Optional[Union[str, Callable]] = None,
    ) -> None:
        """Initialize the in-memory store.

        Args:
            embedding_model (`Optional[Union[str, Callable]]`,
            defaults to `None`):
                The embedding model to embed the memory unit. If not provided,
                the memory unit will not be embedded.
        """

        # The memory store
        self._content = []
        # The embeddings of the memory store
        self._embeddings = []

        # prepare embedding model if needed
        if isinstance(embedding_model, str):
            model_manager = ModelManager.get_instance()
            self.embedding_model = model_manager.get_model_by_config_name(
                embedding_model,
            )
        else:
            self.embedding_model = embedding_model

    def _insert(self, msg: Msg, index: int = -1) -> None:
        """Insert a new memory unit

        Args:
            msg (`Msg`):
                The memory unit to be inserted.
            index (`int`, defaults to `-1`):
                The index to insert the memory unit. If the index is `-1`, the
                memory unit will be appended to the memory store
        """
        self._content.append(msg)

        if self.embedding_model is not None:
            self._embeddings.append(self._get_embedding(msg))

    def _delete(self, index: int) -> None:
        """Delete a memory unit by index

        Args:
            index (`int`):
                The index of the memory unit to be deleted.
        """
        self._content.pop(index)

        if self.embedding_model is not None:
            self._embeddings.pop(index)

    def _get(self, index: int) -> Msg:
        """Get a memory unit by index

        Args:
            index (`int`):
                The index of the memory unit to be retrieved.
        """
        return self._content[index]

    def _update(self, index: int, new_msg: Msg) -> None:
        """Update a memory unit by index

        Args:
            index (`int`):
                The index of the memory unit to be updated.
            new_msg (`Msg`):
                The new memory unit to replace the old one
        """
        self._content[index] = new_msg

        # Update the embedding if the embedding model is provided
        if self.embedding_model is not None:
            self._embeddings[index] = self._get_embedding(new_msg)

    def _size(self) -> int:
        """The size of the memory store"""
        return len(self._content)

    def _clear(self) -> None:
        """Clear the memory store"""
        self._content = []
        self._embeddings = []

    def _contain(self, msg_id: str) -> bool:
        """Check if the memory store contains a memory unit by msg id

        Args:
            msg_id (`str`):
                The id of the memory unit to be checked.
        """
        for _ in range(self._size()):
            if self._get(_).id == msg_id:
                return True
        return False

    def _export(self, file_path: Optional[str] = None) -> str:
        """Export the memory store to a file

        Args:
            file_path (`Optional[str]`, defaults to `None`):
                The file path to save the memory store
        """
        serialized_msgs: str = serialize(self._content)

        if file_path is not None:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(serialized_msgs)

        return serialized_msgs

    def _load(
        self,
        memories: list[Msg],
        overwrite: bool = True,
    ) -> None:
        """Load the memory from a file

        Args:
            memories (`list[Msg]`):
                The memory to be loaded.
            overwrite (`bool`, defaults to `True`):
                Whether to overwrite the current memory store.
        """
        # Handle the embedding if needed
        loaded_embeddings = []
        if self.embedding_model is not None:
            for msg in memories:
                loaded_embeddings.append(self._get_embedding(msg))

        # Overwrite the memory store if needed
        if overwrite:
            self._clear()
            self._content = memories
            self._embeddings = loaded_embeddings
        else:
            self._content.extend(memories)
            self._embeddings.extend(loaded_embeddings)

    def _retrieve_by_embedding(
        self,
        query: Union[str, Embedding],
        metric: Callable[[Embedding, Embedding], float],
        top_k: int = 1,
        preserve_order: bool = True,
    ) -> list[dict]:
        """Retrieve memory by their embeddings.

        Args:
            query (`Union[str, Embedding]`):
                Query string or embedding.
            metric (`Callable[[Embedding, Embedding], float]`):
                A metric to compute the relevance between embeddings of query
                and memory. In default, higher relevance means better match,
                and you can set `reverse` to `True` to reverse the order.
            top_k (`int`, defaults to `1`):
                The number of memory units to retrieve.
            preserve_order (`bool`, defaults to `True`):
                Whether to preserve the original order of the retrieved memory
                units.

        Returns:
            `list[dict]`: a list of retrieved memory units in
            specific order.
        """

        retrieved_items = retrieve_from_list(
            query,
            self._embeddings,
            metric,
            top_k,
            self.embedding_model,
            preserve_order,
        ).content

        # obtain the corresponding memory item
        response = []
        for score, index, _ in retrieved_items:
            response.append(
                {
                    "score": score,
                    "index": index,
                    "memory": self._content[index],
                },
            )

        return response

    def _get_embedding(self, msg: Msg) -> Embedding:
        """Get embedding of a message unit.

        Args:
            msg (`Msg`):
                The message unit to be embedded.

        Returns:
            `Embedding`: The embedding of the message unit.
        """
        # Raise error if the embedding model is not provided
        if self.embedding_model is None:
            raise ModuleNotFoundError(
                "The embedding model is not provided during initialization.",
            )

        response = self.embedding_model(serialize(msg))

        if isinstance(response, ModelResponse):
            return response.content
        else:
            return response


class TemporaryMemory(InMemoryStore, MemoryActions):
    """The temporary memory class that inherits from the in-memory store and
    memory actions."""

    def __init__(
        self,
        embedding_model: Optional[Union[str, Callable]] = None,
    ) -> None:
        """Initialize the temporary memory object.

        Args:
            embedding_model (`Optional[str, Callable]`, defaults to `None`):
                The embedding model to embed the memory unit. If not provided,
                the memory unit will not be embedded.
        """

        InMemoryStore.__init__(self, embedding_model)
        MemoryActions.__init__(self)
