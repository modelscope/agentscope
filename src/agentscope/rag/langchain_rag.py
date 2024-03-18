# -*- coding: utf-8 -*-
"""
This module is integrate the LangChain RAG model into our AgentScope package
"""


from typing import Type, Any, Optional

# from pathlib import Path

from langchain_community.document_loaders.base import BaseLoader
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters.base import TextSplitter
from langchain_openai import OpenAIEmbeddings

from agentscope.rag import RAGBase
from agentscope.models import ModelWrapperBase


class LangChainRAG(RAGBase):
    """
    This class is a wrapper around the LangChain RAG.
    TODO: still under construction
    """

    def __init__(
        self,
        model: Optional[ModelWrapperBase],
        emb_model: Optional[ModelWrapperBase],
        loader_type: Type[BaseLoader],
        splitter_type: Type[TextSplitter],
        vector_store_type: Type[VectorStore],
        embedding_model: Type[OpenAIEmbeddings],
        **kwargs: Any,
    ) -> None:
        super().__init__(model, emb_model, **kwargs)
        self.loader_type = loader_type
        self.splitter_type = splitter_type
        self.config = kwargs
        self.vector_store_type = vector_store_type
        self.loader = None
        self.splitter = None
        self.vector_store = None
        self.embedding_model = embedding_model
        self.retriever = None

    def load_data(
        self,
        loader: Any,
        query: Any,
        **kwargs: Any,
    ) -> Any:
        """loading data from a directory"""
        self.loader = loader
        docs = self.loader.load()
        self.splitter = self.splitter_type(**kwargs)
        all_splits = self.splitter.split_documents(docs)
        return all_splits

    def store_and_index(
        self,
        docs: Any,
        vector_store: Any,
        **kwargs: Any,
    ) -> None:
        """indexing the documents and store them into the vector store"""
        self.vector_store = self.vector_store_type.from_documents(
            documents=docs,
            embedding=self.embedding_model(),
        )
        # build retriever
        k = self.config.get("k", 6)
        search_type = self.config.get("search_type", "similarity")
        self.retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k},
        )

    def retrieve(self, query: Any) -> list[Any]:
        """retrieve the documents based on the query"""
        retrieved_docs = self.retriever.invoke(query)
        return retrieved_docs
