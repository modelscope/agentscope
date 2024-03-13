# -*- coding: utf-8 -*-
"""
This module is integrate the Llama index RAG model into our AgentScope package
"""

from typing import Any, Union, Type
from pathlib import Path
from llama_index.core import VectorStoreIndex
from llama_index.core.readers.base import BaseReader
from llama_index.core.base.base_retriever import BaseRetriever

from agentscope.rag import RAGBase
from agentscope.models import ModelWrapperBase


class LlamaIndexRAG(RAGBase):
    """
    This class is a wrapper around the Llama index RAG.
    """

    def __init__(
        self,
        model: ModelWrapperBase,
        loader_type: Type[BaseReader],
        vector_store_type: Type[VectorStoreIndex],
        retriever_type: Type[BaseRetriever],
        **kwargs: Any,
    ) -> None:
        super().__init__(model, **kwargs)
        self.loader_type = loader_type
        self.vector_store_type = vector_store_type
        self.retriever_type = retriever_type
        self.retriever = None
        self.query_engine = None
        self.persist_dir = kwargs.get("persist_dir", "./")

    def load_data(
        self,
        path: Union[Path, str],
        **kwargs: Any,
    ) -> Any:
        documents = self.loader_type(path).load_data()
        return documents

    def store_and_index(self, docs: Any) -> None:
        index = self.vector_store_type.from_documents(docs)
        index.storage_context.persist(persist_dir=self.persist_dir)
        self.query_engine = index.as_query_engine()

    def retrieve(self, query: Any) -> list[Any]:
        response = self.query_engine.query(query)
        return response
