# -*- coding: utf-8 -*-
"""
This module is integrate the LangChain RAG model into our AgentScope package
"""


from typing import Any, Optional

# from pathlib import Path

from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders.base import BaseLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters.base import TextSplitter

# from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import CharacterTextSplitter

from agentscope.rag import RAGBase
from agentscope.rag.rag import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from agentscope.models import ModelWrapperBase


class _LangChainEmbModel(Embeddings):
    def __init__(self, emb_model: ModelWrapperBase):
        self._emb_model_wrapper = emb_model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Wrapper function for embedding list of documents
        """
        results = [
            list(self._emb_model_wrapper(t).embedding[0]) for t in texts
        ]
        return results

    def embed_query(self, text: str) -> list[float]:
        """
        Wrapper function for embedding a single query
        """
        return list(self._emb_model_wrapper(text).embedding[0])


class LangChainRAG(RAGBase):
    """
    This class is a wrapper around the LangChain RAG.
    TODO: still under construction
    """

    def __init__(
        self,
        model: Optional[ModelWrapperBase],
        emb_model: Optional[ModelWrapperBase],
        config: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model, emb_model, **kwargs)

        self.loader = None
        self.splitter = None
        self.retriever = None
        self.vector_store = None

        self.config = config or {}
        if isinstance(emb_model, ModelWrapperBase):
            self.emb_model = _LangChainEmbModel(emb_model)
        elif isinstance(emb_model, Embeddings):
            self.emb_model = emb_model
        else:
            raise TypeError(
                f"Embedding model does not support {type(self.emb_model)}.",
            )

    def load_data(
        self,
        loader: BaseLoader,
        query: Optional[Any] = None,
        **kwargs: Any,
    ) -> list[Document]:
        # pylint: disable=unused-argument
        """
        loading data from a directory
        :param loader: accepting a LangChain loader instance, default is a
        :param _: accepting a query, LangChain does not rely on this
        :param kwargs: other parameters for loader and splitter
        :return: a list of documents

        Notice: currently LangChain supports
        """
        self.loader = loader
        docs = self.loader.load()
        # self.splitter = self.splitter_type(**kwargs)
        # all_splits = self.splitter.split_documents(docs)
        return docs

    def store_and_index(
        self,
        docs: Any,
        vector_store: Optional[VectorStore] = None,
        splitter: Optional[TextSplitter] = None,
        **kwargs: Any,
    ) -> None:
        """
        Preprocessing the loaded documents.
        :param docs: documents to be processed
        :param vector_store: vector store
        :param retriever: optional, specifies the retriever to use
        :param splitter: optional, specifies the splitter to preprocess
            the documents
        :param kwargs:

        In LlamaIndex terms, an Index is a data structure composed
        of Document objects, designed to enable querying by an LLM.
        For example:
        1) preprocessing documents with
        2) generate embedding,
        3) store the embedding-content to vdb
        """
        self.splitter = splitter or CharacterTextSplitter(
            chunk_size=self.config.get("chunk_size", DEFAULT_CHUNK_SIZE),
            chunk_overlap=self.config.get(
                "chunk_overlap",
                DEFAULT_CHUNK_OVERLAP,
            ),
        )
        all_splits = self.splitter.split_documents(docs)

        # indexing the chunks and store them into the vector store
        if vector_store is None:
            vector_store = Chroma()
        self.vector_store = vector_store.from_documents(
            documents=all_splits,
            embedding=self.emb_model,
        )

        # build retriever
        k = self.config.get("k", 6)
        search_type = self.config.get("search_type", "similarity")
        self.retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k},
        )

    def retrieve(self, query: Any, to_list_strs: bool = False) -> list[Any]:
        """
        This is a basic retrieve function with LangChain APIs
        :param query: query is expected to be a question in string

        More advanced retriever can refer to
        https://python.langchain.com/docs/modules/data_connection/retrievers/
        """

        retrieved_docs = self.retriever.invoke(query)
        if to_list_strs:
            results = []
            for doc in retrieved_docs:
                results.append(doc.page_content)
            return results
        return retrieved_docs
