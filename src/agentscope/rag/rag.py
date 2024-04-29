# -*- coding: utf-8 -*-
"""
Base class module for retrieval augmented generation (RAG).
To accommodate the RAG process of different packages,
we abstract the RAG process into four stages:
- data loading: loading data into memory for following processing;
- data indexing and storage: document chunking, embedding generation,
and off-load the data into VDB;
- data retrieval: taking a query and return a batch of documents or
document chunks;
- post-processing of the retrieved data: use the retrieved data to
generate an answer.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from agentscope.models import ModelWrapperBase

DEFAULT_CHUNK_SIZE = 1024
DEFAULT_CHUNK_OVERLAP = 20
DEFAULT_TOP_K = 5


class RAGBase(ABC):
    """
    Base class for RAG, CANNOT be instantiated directly
    """

    def __init__(
        self,
        model: Optional[ModelWrapperBase],
        emb_model: Any = None,
        rag_config: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        # pylint: disable=unused-argument
        self.postprocessing_model = model
        self.emb_model = emb_model
        self.rag_config = rag_config or {}

    @abstractmethod
    def _init_rag(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Initiate the RAG module.
        """

    @abstractmethod
    def retrieve(
        self,
        query: Any,
        to_list_strs: bool = False,
    ) -> list[Any]:
        """
        retrieve list of content from database (vector stored index) to memory
        Args:
            query (Any): query to retrieve
            to_list_strs (bool): whether return a list of str

        Returns:
            return a list with retrieved documents (in strings)
        """

    def post_processing(
        self,
        retrieved_docs: list[str],
        prompt: str,
        **kwargs: Any,
    ) -> Any:
        """
        A default solution for post-processing function, generates answer
        based on the retrieved documents.
        Args:
            retrieved_docs (list[str]):
                list of retrieved documents
            prompt (str):
                prompt for LLM generating answer with the retrieved documents

        Returns:
            Any: a synthesized answer from LLM with retrieved documents

        Example:
            self.postprocessing_model(prompt.format(retrieved_docs))
        """
        assert self.postprocessing_model
        prompt = prompt.format("\n".join(retrieved_docs))
        return self.postprocessing_model(prompt, **kwargs).text
