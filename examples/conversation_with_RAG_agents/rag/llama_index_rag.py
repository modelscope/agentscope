# -*- coding: utf-8 -*-
"""
This module is an integration of the Llama index RAG
into AgentScope package
"""

import importlib
import os.path
from typing import Any, Optional, List, Union
from loguru import logger

try:
    from llama_index.core.base.base_retriever import BaseRetriever
    from llama_index.core.base.embeddings.base import (
        BaseEmbedding,
        Embedding,
    )
    from llama_index.core.ingestion import IngestionPipeline

    from llama_index.core.bridge.pydantic import PrivateAttr
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.core import (
        VectorStoreIndex,
        StorageContext,
        load_index_from_storage,
    )
    from llama_index.core.schema import (
        Document,
        TransformComponent,
    )
except ImportError:
    BaseRetriever = None
    BaseEmbedding, Embedding = None, None
    IngestionPipeline = None
    SentenceSplitter = None
    VectorStoreIndex, StorageContext = None, None
    load_index_from_storage = None
    PrivateAttr = None
    Document, TransformComponent = None, None

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
        rag_config: dict = None,
        index_config: dict = None,
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
                The configuration to generate the index
        """
        super().__init__(model, emb_model, rag_config, **kwargs)
        self.retriever = None
        self.index = None
        self.persist_dir = rag_config.get("persist_dir", "/")
        self.emb_model = emb_model
        self.rag_config = rag_config
        self.index_config = index_config
        self.override_existing_index = False
        # ensure the emb_model is compatible with LlamaIndex
        if isinstance(emb_model, ModelWrapperBase):
            self.emb_model = _EmbeddingModel(emb_model)
        elif isinstance(self.emb_model, BaseEmbedding):
            pass
        else:
            raise TypeError(
                f"Embedding model does not support {type(self.emb_model)}.",
            )
        self._init_rag()

    def _init_rag(self) -> None:
        """
        Initialize the RAG.
        """
        if os.path.exists(self.persist_dir):
            self._load_index()
            logger.info(f"index loaded from {self.persist_dir}")
            self.refresh_index()
        else:
            self._data_to_index()
        self._set_retriever()

    def _load_index(self) -> None:
        """
        Load the index from persist_dir.
        """
        # load the storage_context
        storage_context = StorageContext.from_defaults(
            persist_dir=self.persist_dir,
        )
        # construct index from
        self.index = load_index_from_storage(
            storage_context=storage_context,
            embed_model=self.emb_model,
        )

    def _data_to_index(self) -> None:
        """
        Convert the data to index by configs.
        """
        # NOTE: as each selected file type may need to use a different loader
        # and transformations, the length of the list depends on
        # the total count of loaded data.
        nodes = []
        for config in self.index_config:
            documents = self._data_to_docs(config=config)
            # # store and indexing for each file type
            transformations = self._set_transformations(config=config).get(
                "transformations",
            )
            nodes_docs = self._docs_to_nodes(
                documents=documents,
                transformations=transformations,
            )
            nodes = nodes + nodes_docs
        # convert nodes to index
        self.index = VectorStoreIndex(
            nodes=nodes,
            embed_model=self.emb_model,
        )
        logger.info("index calculation completed.")
        # persist the calculated index
        self.index.storage_context.persist(persist_dir=self.persist_dir)
        logger.info("index persisted.")

    def _data_to_docs(
        self,
        query: Optional[str] = None,
        config: dict = None,
    ) -> Any:
        """
        Accept a loader, loading the desired data (no chunking)
        Args:
            query (Optional[str]):
                optional, used when the data is in a database.
            config (dict):
                optional, used when the loader config is in a config file.
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
        loader = self._set_loader(config=config).get("loader")
        # let the doc_id be the filename for each document
        loader.filename_as_id = True
        if query is None:
            documents = loader.load_data()
        else:
            # this is for querying a database,
            # does not work for loading a document directory
            documents = loader.load_data(query)
        logger.info(f"loaded {len(documents)} documents")
        return documents

    @staticmethod
    def _docs_to_nodes(
        documents: List[Document],
        transformations: Optional[list[TransformComponent]] = None,
    ) -> Any:
        """
        Preprocessing the loaded documents.
        Args:
            documents (List[Document]):
                documents to be processed, usually expected to be in
                 llama index Documents.
            transformations (Optional[list[TransformComponent]]):
                optional, specifies the transformations (operators) to
                process documents (e.g., split the documents into smaller
                chunks)

        Return:
            Any: return the index of the processed document

        In LlamaIndex terms, an Index is a data structure composed
        of Document objects, designed to enable querying by an LLM.
        For example:
        1) preprocessing documents with data loaders
        2) generate embedding by configuring pipline with embedding models
        3) store the embedding-content to vector database
        """
        # nodes, or called chunks, is a presentation of the documents
        # we build nodes by using the IngestionPipeline
        # for each document with corresponding transformations
        pipeline = IngestionPipeline(
            transformations=transformations,
        )
        # stack up the nodes from the pipline
        nodes = pipeline.run(
            documents=documents,
            show_progress=True,
        )
        logger.info("nodes generated.")
        return nodes

    def _set_loader(self, config: dict) -> Any:
        """
        set the loader as needed, or just use the default setting.
        Args:
            config (dict): a dictionary containing configurations
        """
        if "load_data" in config:
            # we prepare the loader from the configs
            loader = self._prepare_args_from_config(
                config=config.get("load_data", {}),
            )
        else:
            # we prepare the loader by default
            try:
                from llama_index.core import SimpleDirectoryReader
            except ImportError as exc_inner:
                raise ImportError(
                    " LlamaIndexAgent requires llama-index to be install."
                    "Please run `pip install llama-index`",
                ) from exc_inner
            loader = {
                "loader": SimpleDirectoryReader(
                    input_dir="set_default_data_path",
                ),
            }
        logger.info("loaders ready.")
        return loader

    def _set_transformations(self, config: dict) -> Any:
        """
        set the transformations as needed, or just use the default setting.
        Args:
            config (dict): a dictionary containing configurations
        """
        if "store_and_index" in config:
            temp = self._prepare_args_from_config(
                config=config.get("store_and_index", {}),
            )
            transformations = temp.get("transformations")
        else:
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
        logger.info("transformations ready.")
        # as the last step, we need to repackage the transformations in dict
        transformations = {"transformations": transformations}
        return transformations

    def _set_retriever(
        self,
        retriever: Optional[BaseRetriever] = None,
        **kwargs: Any,
    ) -> None:
        """
        set the retriever as needed, or just use the default setting.
        Args:
            retriever (Optional[BaseRetriever]): passing a retriever in llama
            index.
        """
        # set the retriever
        if retriever is None:
            logger.info(
                f"similarity_top_k"
                f'={self.rag_config.get("similarity_top_k", DEFAULT_TOP_K)}',
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
        logger.info("retrievers ready.")

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

    def _prepare_args_from_config(self, config: dict) -> Any:
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

    def refresh_index(self) -> None:
        """
        Refresh the index.
        """
        for config in self.index_config:
            documents = self._data_to_docs(config=config)
            # store and indexing for each file type
            transformations = self._set_transformations(config=config).get(
                "transformations",
            )
            self._insert_docs_to_index(
                documents=documents,
                transformations=transformations,
            )

    def _insert_docs_to_index(
        self,
        documents: List[Document],
        transformations: TransformComponent,
    ) -> None:
        """
        Add documents to the index.
        Args:
            documents (List[Document]): list of documents to be added.
            transformations (TransformComponent): transformations that
            convert the documents into nodes.
        """
        pipeline = IngestionPipeline(
            transformations=transformations,
        )
        insert_docs_list = []
        for doc in documents:
            if doc.doc_id not in self.index.ref_doc_info.keys():
                insert_docs_list.append(doc)
                # stack up the nodes from the pipline
                logger.info(f"add doc_id={doc.doc_id}")
            else:
                if self.override_existing_index:
                    self.index.delete_ref_doc(
                        ref_doc_id=doc.doc_id,
                        delete_from_docstore=True,
                    )
                    insert_docs_list.append(doc)
                    logger.info(f"replace current doc_id={doc.doc_id}")
        nodes = pipeline.run(
            documents=insert_docs_list,
            show_progress=True,
        )
        self.index.insert_nodes(nodes=nodes)
        logger.info("nodes added to index.")

    def _delete_docs_from_index(
        self,
        documents: List[Document],
    ) -> None:
        """
        Delete the nodes that are associated with documents.
        Args:
            documents (List[Document]): list of documents to be deleted.
        """
        doc_id_list = [doc.doc_id for doc in documents]
        logger.info(f"doc_id_list={doc_id_list}\n")
        for key in self.index.ref_doc_info.keys():
            if key in doc_id_list:
                self.index.delete_ref_doc(
                    ref_doc_id=key,
                    delete_from_docstore=True,
                )
                logger.info(f"removed docs deleted doc_id={key}")
