# -*- coding: utf-8 -*-
"""
Knowledge bank for making RAG module easier to use
"""
import copy
from typing import Optional
from loguru import logger
from agentscope.models import load_model_by_config_name
from .llama_index_rag import LlamaIndexRAG

DEFAULT_INDEX_CONFIG = {
    "knowledge_id": "",
    "data_processing": [],
}
DEFAULT_LOADER_CONFIG = {
    "load_data": {
        "loader": {
            "create_object": True,
            "module": "llama_index.core",
            "class": "SimpleDirectoryReader",
            "init_args": {},
        },
    },
}
DEFAULT_INIT_CONFIG = {
    "input_dir": "",
    "recursive": True,
    "required_exts": [],
}


class KnowledgeBank:
    """
    KnowledgeBank enables
    1) provide an easy and fast way to initialize the RAG model;
    2) make RAG model reusable and sharable for multiple agents.
    """

    def __init__(
        self,
        configs: dict,
    ) -> None:
        """initialize the knowledge bank"""
        self.configs = configs
        self.stored_knowledge: dict[str, LlamaIndexRAG] = {}
        self._init_knowledge()

    def _init_knowledge(self) -> None:
        """initialize the knowledge bank"""
        for config in self.configs:
            self.add_data_for_rag(
                knowledge_id=config["knowledge_id"],
                emb_model_name="qwen_emb_config",
                index_config=config,
            )
        logger.info("knowledge bank initialization completed.\n ")

    def add_data_for_rag(
        self,
        knowledge_id: str,
        emb_model_name: str,
        data_dirs_and_types: dict[str, list[str]] = None,
        model_name: Optional[str] = None,
        index_config: Optional[dict] = None,
    ) -> None:
        """
        Transform data in a directory to be ready to work with RAG.
        Args:
            knowledge_id (str):
                user-defined unique id for the knowledge with RAG
            emb_model_name (str):
                name of the embedding model
            model_name (Optional[str]):
                name of the LLM for potential post-processing or query rewrite
            data_dirs_and_types (dict[str, list[str]]):
                dictionary of data paths (keys) to the data types
                (file extensions) for knowledgebase
                (e.g., [".md", ".py", ".html"])
            index_config (optional[dict]):
                complete indexing configuration, used for more advanced
                applications. Users can customize
                - loader,
                - transformations,
                - ...
                Examples can refer to../examples/conversation_with_RAG_agents/

            a simple example of importing data to RAG:
            ''
                knowledge_bank.add_data_for_rag(
                    knowledge_id="agentscope_tutorial_rag",
                    emb_model_name="qwen_emb_config",
                    data_dirs_and_types={
                        "../../docs/sphinx_doc/en/source/tutorial": [".md"],
                    },
                    persist_dir="./rag_storage/tutorial_assist",
                )
            ''
        """
        if knowledge_id in self.stored_knowledge:
            raise ValueError(f"knowledge_id {knowledge_id} already exists.")

        assert data_dirs_and_types is not None or index_config is not None

        if index_config is None:
            index_config = copy.deepcopy(DEFAULT_INDEX_CONFIG)
            for data_dir, types in data_dirs_and_types.items():
                loader_config = copy.deepcopy(DEFAULT_LOADER_CONFIG)
                loader_init = copy.deepcopy(DEFAULT_INIT_CONFIG)
                loader_init["input_dir"] = data_dir
                loader_init["required_exts"] = types
                loader_config["load_data"]["loader"]["init_args"] = loader_init
                index_config["data_processing"].append(loader_config)

        self.stored_knowledge[knowledge_id] = LlamaIndexRAG(
            knowledge_id=knowledge_id,
            emb_model=load_model_by_config_name(emb_model_name),
            model=load_model_by_config_name(model_name)
            if model_name
            else None,
            index_config=index_config,
        )
        logger.info(f"data loaded for knowledge_id = {knowledge_id}.")

    def get_rag(
        self,
        knowledge_id: str,
        duplicate: bool = False,
    ) -> LlamaIndexRAG:
        """
        Get a RAG from the knowledge bank.
        Args:
            knowledge_id (str):
                unique id for the RAG
            duplicate (bool):
                whether return a copy of the RAG.
        Returns:
            LlamaIndexRAG:
                the RAG object defined with Llama-index
        """
        if knowledge_id not in self.stored_knowledge:
            raise ValueError(
                f"{knowledge_id} does not exist in the " f"knowledge bank.",
            )
        rag = self.stored_knowledge[knowledge_id]
        if duplicate:
            rag = copy.deepcopy(rag)
        logger.info(f"knowledge bank loaded: {knowledge_id}.")
        return rag
