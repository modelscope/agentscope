# -*- coding: utf-8 -*-
"""
This module is integrate the LangChain RAG model into our AgentScope package
"""


from typing import Any, Optional, Union

try:
    from langchain_core.vectorstores import VectorStore
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings
    from langchain_community.document_loaders.base import BaseLoader
    from langchain_community.vectorstores import Chroma
    from langchain_text_splitters.base import TextSplitter
    from langchain_text_splitters import CharacterTextSplitter
except ImportError:
    VectorStore = None
    Document = None
    Embeddings = None
    BaseLoader = None
    Chroma = None
    TextSplitter = None
    CharacterTextSplitter = None

from examples.conversation_with_RAG_agents.rag import RAGBase
from examples.conversation_with_RAG_agents.rag.rag import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
)
from agentscope.models import ModelWrapperBase


class _LangChainEmbModel(Embeddings):
    """
    Dummy wrapper to convert the ModelWrapperBase embedding model
    to a LanguageChain RAG model
    """

    def __init__(self, emb_model: ModelWrapperBase) -> None:
        """
        Dummy wrapper
        Args:
            emb_model (ModelWrapperBase): embedding model of
                ModelWrapperBase type
        """
        self._emb_model_wrapper = emb_model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Wrapper function for embedding list of documents
        Args:
            texts (list[str]): list of texts to be embedded
        """
        results = [
            list(self._emb_model_wrapper(t).embedding[0]) for t in texts
        ]
        return results

    def embed_query(self, text: str) -> list[float]:
        """
        Wrapper function for embedding a single query
        Args:
            text (str): query to be embedded
        """
        return list(self._emb_model_wrapper(text).embedding[0])


class LangChainRAG(RAGBase):
    """
    This class is a wrapper around the LangChain RAG.
    """

    def __init__(
        self,
        model: Optional[ModelWrapperBase],
        emb_model: Union[ModelWrapperBase, Embeddings, None],
        config: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the LangChainRAG
        Args:
            model (ModelWrapperBase):
                The language model used for final synthesis
            emb_model ( Union[ModelWrapperBase, Embeddings, None]):
                The embedding model used for generate embeddings
            config (dict):
                The additional configuration for llama index rag
        """
        super().__init__(model, emb_model, **kwargs)

        self.loader = None
        self.splitter = None
        self.retriever = None
        self.vector_store = None

        if VectorStore is None:
            raise ImportError(
                "Please install LangChain RAG packages to use LangChain RAG.",
            )

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
        Loading data from a directory
        Args:
            loader (BaseLoader):
                accepting a LangChain loader instance
            query (str):
                accepting a query, LangChain does not rely on this
        Returns:
            list[Document]: a list of documents loaded
        """
        self.loader = loader
        docs = self.loader.load()
        return docs

    def store_and_index(
        self,
        docs: Any,
        vector_store: Optional[VectorStore] = None,
        splitter: Optional[TextSplitter] = None,
        **kwargs: Any,
    ) -> Any:
        # pylint: disable=unused-argument
        """
        Preprocessing the loaded documents.
        Args:
            docs (Any):
                documents to be processed
            vector_store (Optional[VectorStore]):
                vector store in LangChain RAG
            splitter (Optional[TextSplitter]):
                optional, specifies the splitter to preprocess
                the documents

        Returns:
            None

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
        search_type = self.config.get("search_type", "similarity")
        self.retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={
                "k": self.config.get("similarity_top_k", 6),
            },
        )

    def retrieve(self, query: Any, to_list_strs: bool = False) -> list[Any]:
        """
        This is a basic retrieve function with LangChain APIs
        Args:
          query: query is expected to be a question in string

        Returns:
            list of answers

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
