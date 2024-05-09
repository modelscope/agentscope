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
        model: Optional[ModelWrapperBase] = None,
        emb_model: Any = None,
        index_config: Optional[dict] = None,
        rag_config: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        # pylint: disable=unused-argument
        self.postprocessing_model = model
        self.emb_model = emb_model
        self.index_config = index_config or {}
        self.rag_config = rag_config or {}

    @abstractmethod
    def _init_rag(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Initiate the RAG module.
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
