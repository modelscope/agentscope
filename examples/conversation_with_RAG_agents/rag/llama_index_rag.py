# -*- coding: utf-8 -*-
"""
This module is an integration of the Llama index RAG
into AgentScope package
"""

from typing import Any, Optional, List, Union
from loguru import logger

try:
    from llama_index.core.readers.base import BaseReader
    from llama_index.core.base.base_retriever import BaseRetriever
    from llama_index.core.base.embeddings.base import BaseEmbedding, Embedding
    from llama_index.core.ingestion import IngestionPipeline
    from llama_index.core.vector_stores.types import (
        BasePydanticVectorStore,
        VectorStore,
    )
    from llama_index.core.bridge.pydantic import PrivateAttr
    from llama_index.core.node_parser.interface import NodeParser
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.core import (
        VectorStoreIndex,
    )
except ImportError:
    BaseReader, BaseRetriever = None, None
    BaseEmbedding, Embedding = None, None
    IngestionPipeline, BasePydanticVectorStore, VectorStore = None, None, None
    NodeParser, SentenceSplitter = None, None
    VectorStoreIndex = None
    PrivateAttr = None

from rag import RAGBase
from rag.rag import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_TOP_K,
)
from agentscope.models import ModelWrapperBase


class _EmbeddingModel(BaseEmbedding):
    """
    wrapper for ModelWrapperBase to an embedding model can be used
    in Llama Index pipeline.
    """

    _emb_model_wrapper: ModelWrapperBase = PrivateAttr()

    def __init__(
        self,
        emb_model: ModelWrapperBase,
        embed_batch_size: int = 1,
    ) -> None:
        """
        Dummy wrapper to convert a ModelWrapperBase to llama Index
        embedding model

        Args:
            emb_model (ModelWrapperBase): embedding model in ModelWrapperBase
            embed_batch_size (int): batch size, defaults to 1
        """
        super().__init__(
            model_name="Temporary_embedding_wrapper",
            embed_batch_size=embed_batch_size,
        )
        self._emb_model_wrapper = emb_model

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        get embedding for query
        Args:
            query (str): query to be embedded
        """
        # Note: AgentScope embedding model wrapper returns list of embedding
        return list(self._emb_model_wrapper(query).embedding[0])

    def _get_text_embeddings(self, texts: List[str]) -> List[Embedding]:
        """
        get embedding for list of strings
        Args:
             texts ( List[str]): texts to be embedded
        """
        results = [
            list(self._emb_model_wrapper(t).embedding[0]) for t in texts
        ]
        return results

    def _get_text_embedding(self, text: str) -> Embedding:
        """
        get embedding for a single string
        Args:
             text (str): texts to be embedded
        """
        return list(self._emb_model_wrapper(text).embedding[0])

    # TODO: use proper async methods, but depends on model wrapper
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """The asynchronous version of _get_query_embedding."""
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Asynchronously get text embedding."""
        return self._get_text_embedding(text)

    async def _aget_text_embeddings(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """Asynchronously get text embeddings."""
        return self._get_text_embeddings(texts)


class LlamaIndexRAG(RAGBase):
    """
    This class is a wrapper with the llama index RAG.
    """

    def __init__(
        self,
        model: Optional[ModelWrapperBase],
        emb_model: Union[ModelWrapperBase, BaseEmbedding, None] = None,
        config: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        """
        RAG component based on llama index.
        Args:
            model (ModelWrapperBase):
                The language model used for final synthesis
            emb_model (Optional[ModelWrapperBase]):
                The embedding model used for generate embeddings
            config (dict):
                The additional configuration for llama index rag
        """
        super().__init__(model, emb_model, config, **kwargs)
        self.retriever = None
        self.index = None
        self.persist_dir = kwargs.get("persist_dir", "/")
        self.emb_model = emb_model
        print(self.config)

        # ensure the emb_model is compatible with LlamaIndex
        if isinstance(emb_model, ModelWrapperBase):
            self.emb_model = _EmbeddingModel(emb_model)
        elif isinstance(self.emb_model, BaseEmbedding):
            pass
        else:
            raise TypeError(
                f"Embedding model does not support {type(self.emb_model)}.",
            )

    def load_data(
        self,
        loader: BaseReader,
        query: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Accept a loader, loading the desired data (no chunking)
        Args:
            loader (BaseReader):
                object to load data, expected be an instance of class
                inheriting from BaseReader in llama index.
            query (Optional[str]):
                optional, used when the data is in a database.

        Returns:
            Any: loaded documents

        Example 1: use simple directory loader to load general documents,
        including Markdown, PDFs, Word documents, PowerPoint decks, images,
        audio and video.
        ```
            load_data_to_chunks(
                loader=SimpleDirectoryReader("./data")
            )
        ```

        Example 2: use SQL loader
        ```
            load_data_to_chunks(
                DatabaseReader(
                    scheme=os.getenv("DB_SCHEME"),
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASS"),
                    dbname=os.getenv("DB_NAME"),
                ),
                query = "SELECT * FROM users"
            )
        ```
        """
        if query is None:
            documents = loader.load_data()
        else:
            documents = loader.load_data(query)
        logger.info(f"loaded {len(documents)} documents")
        return documents

    def store_and_index(
        self,
        docs: Any,
        vector_store: Union[BasePydanticVectorStore, VectorStore, None] = None,
        retriever: Optional[BaseRetriever] = None,
        transformations: Optional[list[NodeParser]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Preprocessing the loaded documents.
        Args:
            docs (Any):
                documents to be processed, usually expected to be in
                 llama index Documents.
            vector_store (Union[BasePydanticVectorStore, VectorStore, None]):
                vector store in llama index
            retriever (Optional[BaseRetriever]):
                optional, specifies the retriever in llama index to be used
            transformations (Optional[list[NodeParser]]):
                optional, specifies the transformations (operators) to
                process documents (e.g., split the documents into smaller
                chunks)

        Return:
            Any: return the index of the processed document

        In LlamaIndex terms, an Index is a data structure composed
        of Document objects, designed to enable querying by an LLM.
        For example:
        1) preprocessing documents with
        2) generate embedding,
        3) store the embedding-content to vdb
        """
        # build and run preprocessing pipeline
        if transformations is None:
            transformations = [
                SentenceSplitter(
                    chunk_size=self.config.get(
                        "chunk_size",
                        DEFAULT_CHUNK_SIZE,
                    ),
                    chunk_overlap=self.config.get(
                        "chunk_overlap",
                        DEFAULT_CHUNK_OVERLAP,
                    ),
                ),
            ]

        # adding embedding model as the last step of transformation
        # https://docs.llamaindex.ai/en/stable/module_guides/loading/ingestion_pipeline/root.html
        transformations.append(self.emb_model)

        if vector_store is not None:
            pipeline = IngestionPipeline(
                transformations=transformations,
                vector_store=vector_store,
            )
            _ = pipeline.run(docs)
            self.index = VectorStoreIndex.from_vector_store(vector_store)
        else:
            # No vector store is provide, use simple in memory
            pipeline = IngestionPipeline(
                transformations=transformations,
            )
            nodes = pipeline.run(documents=docs)
            self.index = VectorStoreIndex(
                nodes=nodes,
                embed_model=self.emb_model,
            )

        # set the retriever
        if retriever is None:
            logger.info(
                f'{self.config.get("similarity_top_k", DEFAULT_TOP_K)}',
            )
            self.retriever = self.index.as_retriever(
                embed_model=self.emb_model,
                similarity_top_k=self.config.get(
                    "similarity_top_k",
                    DEFAULT_TOP_K,
                ),
                **kwargs,
            )
        else:
            self.retriever = retriever
        return self.index

    def set_retriever(self, retriever: BaseRetriever) -> None:
        """
        Reset the retriever if necessary.
        Args:
            retriever (BaseRetriever): passing a retriever in llama index.
        """
        self.retriever = retriever

    def retrieve(self, query: str, to_list_strs: bool = False) -> list[Any]:
        """
        This is a basic retrieve function
        Args:
            query (str):
                query is expected to be a question in string
            to_list_strs (book):
                whether returns the list of strings;
                if False, return NodeWithScore

        Return:
            list[Any]: list of str or NodeWithScore


        More advanced query processing can refer to
        https://docs.llamaindex.ai/en/stable/examples/query_transformations/query_transform_cookbook.html
        """
        retrieved = self.retriever.retrieve(str(query))
        if to_list_strs:
            results = []
            for node in retrieved:
                results.append(node.get_text())
            return results
        return retrieved
