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


class Knowledge(ABC):
    """
    Base class for RAG, CANNOT be instantiated directly
    """

    def __init__(
        self,
        knowledge_id: str,
        emb_model: Any = None,
        knowledge_config: Optional[dict] = None,
        model: Optional[ModelWrapperBase] = None,
        **kwargs: Any,
    ) -> None:
        # pylint: disable=unused-argument
        """
        initialize the knowledge component
        Args:
        knowledge_id (str):
            The id of the knowledge unit.
        emb_model (ModelWrapperBase):
            The embedding model used for generate embeddings
        knowledge_config (dict):
            The configuration to generate or load the index.
        """
        self.knowledge_id = knowledge_id
        self.emb_model = emb_model
        self.knowledge_config = knowledge_config or {}
        self.postprocessing_model = model

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
        similarity_top_k: int = None,
        to_list_strs: bool = False,
        **kwargs: Any,
    ) -> list[Any]:
        """
        retrieve list of content from database (vector stored index) to memory
        Args:
            query (Any):
                query for retrieval
            similarity_top_k (int):
                the number of most similar data returned by the
                retriever.
            to_list_strs (bool):
                whether return a list of str

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

    def _prepare_args_from_config(self, config: dict) -> Any:
        """
        Helper function to build objects in RAG classes.

        Args:
            config (dict): a dictionary containing configurations
        Returns:
            Any: an object that is parsed/built to be an element
                of input to the function of RAG module.
        """
        if not isinstance(config, dict):
            return config

        if "create_object" in config:
            # if a term in args is an object,
            # recursively create object with args from config
            module_name = config.get("module", "")
            class_name = config.get("class", "")
            init_args = config.get("init_args", {})
            try:
                cur_module = importlib.import_module(module_name)
                cur_class = getattr(cur_module, class_name)
                init_args = self._prepare_args_from_config(init_args)
                logger.info(
                    f"load and build object: {class_name}",
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
                            self._prepare_args_from_config(c),
                        )
                elif isinstance(value, dict):
                    prepared_args[key] = self._prepare_args_from_config(value)
                else:
                    prepared_args[key] = value
            return prepared_args
