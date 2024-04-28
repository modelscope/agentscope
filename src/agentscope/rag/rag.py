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

import importlib
from abc import ABC, abstractmethod
from typing import Any, Optional
from loguru import logger

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
        config: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        # pylint: disable=unused-argument
        self.postprocessing_model = model
        self.emb_model = emb_model
        self.config = config or {}

    @abstractmethod
    def load_data(
        self,
        loader: Any,
        query: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Load data (documents) from disk to memory and chunking them
        Args:
            loader (Any): data loader, depending on the package
            query (str): query for getting data from DB

        Returns:
            Any: loaded documents
        """

    @abstractmethod
    def store_and_index(
        self,
        docs_list: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Store and index the documents.
        Args:
            docs (Any):
                documents to be processed, stored and indexed
            vector_store (Any):
                vector store to store the index and/or documents

        Returns:
            Any: can be indices, depending on the RAG package

        preprocessing the loaded documents, for example:
        1) chunking,
        2) generate embedding,
        3) store the embedding-content to vdb
        """

    @abstractmethod
    def retrieve(self, query: Any, to_list_strs: bool = False) -> list[Any]:
        """
        retrieve list of content from vdb to memory
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

    def prepare_args_from_config(
        self,
        config: dict,
    ) -> Any:
        """
        Helper function to build args for the two functions:
        load_data(...) and store_and_index(docs, ...)
        in RAG classes.
        Args:
            config (dict): a dictionary containing configurations

        Returns:
            Any: an object that is parsed/built to be an element
                of input to the function of RAG module.
        """
        if not isinstance(config, dict):
            return config

        if "create_object" in config:
            # if a term in args is a object,
            # recursively create object with args from config
            module_name = config.get("module", "")
            class_name = config.get("class", "")
            init_args = config.get("init_args", {})
            try:
                cur_module = importlib.import_module(module_name)
                cur_class = getattr(cur_module, class_name)
                init_args = self.prepare_args_from_config(init_args)
                logger.info(
                    f"load and build object{cur_module, cur_class, init_args}",
                )
                return cur_class(**init_args)
            except ImportError as exc_inner:
                logger.error(
                    f"Fail to load class {class_name} "
                    f"from module {module_name}",
                )
                raise ImportError(
                    f"Fail to load class {class_name} "
                    f"from module {module_name}",
                ) from exc_inner
        else:
            prepared_args = {}
            for key, value in config.items():
                if isinstance(value, list):
                    prepared_args[key] = []
                    for c in value:
                        prepared_args[key].append(
                            self.prepare_args_from_config(c),
                        )
                elif isinstance(value, dict):
                    prepared_args[key] = self.prepare_args_from_config(value)
                else:
                    prepared_args[key] = value
            return prepared_args
