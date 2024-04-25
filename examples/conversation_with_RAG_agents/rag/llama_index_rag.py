# -*- coding: utf-8 -*-
"""
This module is an integration of the Llama index RAG
into AgentScope package
"""

from typing import Any, Optional, List, Union
from loguru import logger
import importlib
import os.path

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
        StorageContext,
        load_index_from_storage,
    )
except ImportError:
    BaseReader, BaseRetriever = None, None
    BaseEmbedding, Embedding = None, None
    IngestionPipeline, BasePydanticVectorStore, VectorStore = None, None, None
    NodeParser, SentenceSplitter = None, None
    VectorStoreIndex, StorageContext = None, None
    load_index_from_storage = None
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
            rag_config: Optional[dict] = None,
            index_config: Optional[dict] = None,
            **kwargs: Any,
    ) -> None:
        """
        RAG component based on llama index.
        Args:
            model (ModelWrapperBase):
                The language model used for final synthesis
            emb_model (Optional[ModelWrapperBase]):
                The embedding model used for generate embeddings
            rag_config (dict):
                The configuration for llama index rag
            index_config (dict):
                The configuration for caculating the index
        """
        super().__init__(model, emb_model, rag_config, **kwargs)
        self.retriever = None
        self.index = None
        self.persist_dir = rag_config.get("persist_dir", "/")
        self.emb_model = emb_model
        self.rag_config = rag_config
        self.index_config = index_config

        # ensure the emb_model is compatible with LlamaIndex
        if isinstance(emb_model, ModelWrapperBase):
            self.emb_model = _EmbeddingModel(emb_model)
        elif isinstance(self.emb_model, BaseEmbedding):
            pass
        else:
            raise TypeError(
                f"Embedding model does not support {type(self.emb_model)}.",
            )
        self.init_rag()

    def init_rag(self) -> None:
        """
        Initialize the RAG.
        """
        # initiate the loaded document/store_and_index arguments list,
        docs_list, store_and_index_args_list = [], []

        # NOTE: as each selected file type may need to use a different loader
        # and transformations, the length of the list depends on
        # the total count of loaded data.
        for index_config_i in range(len(self.index_config)):
            docs = self.load_docs(
                index_config=self.index_config[index_config_i])
            docs_list.append(docs)

            # store and indexing for each file type
            if "store_and_index" in self.index_config[index_config_i]:
                store_and_index_args = self._prepare_args_from_config(
                    self.index_config[index_config_i]["store_and_index"],
                )
            else:
                store_and_index_args = {"transformations": None}
            store_and_index_args_list.append(store_and_index_args)

        # display the arguments for store_and_index_list
        logger.info(f"store_and_index_args args: {store_and_index_args_list}")

        # pass the loaded documents and arguments to store_and_index
        self.store_and_index(
            docs_list=docs_list,
            store_and_index_args_list=store_and_index_args_list
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
            docs_list: Any,
            retriever: Optional[BaseRetriever] = None,
            transformations: Optional[list[NodeParser]] = None,
            store_and_index_args_list: Optional[list] = None,
            **kwargs: Any,
    ) -> Any:
        """
        Preprocessing the loaded documents.
        Args:
            docs_list (Any):
                documents to be processed, usually expected to be in
                 llama index Documents.
            retriever (Optional[BaseRetriever]):
                optional, specifies the retriever in llama index to be used
            transformations (Optional[list[NodeParser]]):
                optional, specifies the transformations (operators) to
                process documents (e.g., split the documents into smaller
                chunks)
            store_and_index_args_list (Optional[list]):
                optional, specifies the indexing configurations in llama
                index for each document type

        Return:
            Any: return the index of the processed document

        In LlamaIndex terms, an Index is a data structure composed
        of Document objects, designed to enable querying by an LLM.
        For example:
        1) preprocessing documents with data loaders
        2) generate embedding by configuring pipline with embedding models
        3) store the embedding-content to vector database
        """

        # if persist_dir does not exist, calculate the index
        if not os.path.exists(self.persist_dir):
            # nodes, or called chunks, is a presentation of the documents
            nodes = []
            # we build nodes by using the IngestionPipeline for each document
            for i in range(len(docs_list)):
                nodes = nodes + self.docs_to_nodes(
                    docs=docs_list[i],
                    transformations=store_and_index_args_list[i].get(
                        "transformations", None)
                )

            # feed all the nodes to embedding model to calculate index
            self.index = VectorStoreIndex(
                nodes=nodes,
                embed_model=self.emb_model,
            )
            # persist the calculated index
            self.persist_to_dir()
        else:
            # load the storage_context
            storage_context = StorageContext.from_defaults(
                persist_dir=self.persist_dir,
            )
            # construct index from
            self.index = load_index_from_storage(
                storage_context=storage_context,
                embed_model=self.emb_model,
            )

        # set the retriever
        if retriever is None:
            logger.info(
                f'{self.rag_config.get("similarity_top_k", DEFAULT_TOP_K)}',
            )
            self.retriever = self.index.as_retriever(
                embed_model=self.emb_model,
                similarity_top_k=self.rag_config.get(
                    "similarity_top_k",
                    DEFAULT_TOP_K,
                ),
                **kwargs,
            )
        else:
            self.retriever = retriever
        return self.index

    def persist_to_dir(self):
        """
        Persist the index to the directory.
        """
        self.index.storage_context.persist(persist_dir=self.persist_dir)

    def load_docs(self, index_config: dict) -> Any:
        """
        Load the documents by configurations.
        Args:
            index_config (dict):
                the index configuration
        Return:
            Any: the loaded documents
        """

        if "load_data" in index_config:
            load_data_args = self._prepare_args_from_config(
                index_config["load_data"],
            )
        else:
            try:
                from llama_index.core import SimpleDirectoryReader
            except ImportError as exc_inner:
                raise ImportError(
                    " LlamaIndexAgent requires llama-index to be install."
                    "Please run `pip install llama-index`",
                ) from exc_inner
            load_data_args = {
                "loader": SimpleDirectoryReader(
                    index_config["set_default_data_path"]),
            }
        logger.info(f"rag.load_data args: {load_data_args}")
        docs = self.load_data(**load_data_args)
        return docs

    def docs_to_nodes(
            self,
            docs: Any,
            transformations: Optional[list[NodeParser]] = None
    ) -> Any:
        """
        Convert the documents to nodes.
        Args:
            docs (Any):
                documents to be processed, usually expected to be in
                 llama index Documents.
            transformations (list[NodeParser]):
                specifies the transformations (operators) to
                process documents (e.g., split the documents into smaller
                chunks)
        Return:
            Any: return the index of the processed document
        """
        # if it is not specified, use the default configuration
        if transformations is None:
            transformations = [
                SentenceSplitter(
                    chunk_size=self.rag_config.get(
                        "chunk_size",
                        DEFAULT_CHUNK_SIZE,
                    ),
                    chunk_overlap=self.rag_config.get(
                        "chunk_overlap",
                        DEFAULT_CHUNK_OVERLAP,
                    ),
                ),
            ]
        # adding embedding model as the last step of transformation
        # https://docs.llamaindex.ai/en/stable/module_guides/loading/ingestion_pipeline/root.html
        transformations.append(self.emb_model)

        # use in memory to construct an index
        pipeline = IngestionPipeline(
            transformations=transformations,
        )
        # stack up the nodes from the pipline
        nodes = pipeline.run(documents=docs)
        return nodes

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

    def _prepare_args_from_config(
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
                init_args = self._prepare_args_from_config(init_args)
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
                            self._prepare_args_from_config(c),
                        )
                elif isinstance(value, dict):
                    prepared_args[key] = self._prepare_args_from_config(value)
                else:
                    prepared_args[key] = value
            return prepared_args
