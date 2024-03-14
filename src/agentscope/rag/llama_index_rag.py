# -*- coding: utf-8 -*-
"""
This module is integrate the Llama index RAG model into our AgentScope package
"""

from typing import Any, Union, Type, Optional
from pathlib import Path
from llama_index.core.readers.base import BaseReader
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

from agentscope.rag import RAGBase
from agentscope.models import ModelWrapperBase


class LlamaIndexRAG(RAGBase):
    """
    This class is a wrapper around the Llama index RAG.
    """

    def __init__(
        self,
        model: ModelWrapperBase,
        loader_type: Optional[Type[BaseReader]] = None,
        vector_store_type: Optional[Type[VectorStoreIndex]] = None,
        retriever_type: Optional[Type[BaseRetriever]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model, **kwargs)
        self.loader_type = loader_type or SimpleDirectoryReader
        self.vector_store_type = vector_store_type or VectorStoreIndex
        self.retriever_type = retriever_type
        self.retriever = None
        self.index = None
        self.persist_dir = kwargs.get("persist_dir", "./")

    def load_data(
        self,
        path: Union[Path, str],
        **kwargs: Any,
    ) -> Any:
        documents = self.loader_type(path).load_data()
        return documents

    def store_and_index(self, docs: Any) -> None:
        """
        In LlamaIndex terms, an Index is a data structure composed
        of Document objects, designed to enable querying by an LLM.
        A vector store index takes Documents and splits them up into
        Nodes (chunks). It then creates vector embeddings of the
        text of every node, ready to be queried by an LLM.
        """
        self.index = self.vector_store_type.from_documents(docs)
        self.index.storage_context.persist(persist_dir=self.persist_dir)
        self.retriever = self.index.as_retriever()

    def retrieve(self, query: Any) -> list[Any]:
        retrieved_docs = self.retriever.retrieve(str(query))
        return retrieved_docs
