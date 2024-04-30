# -*- coding: utf-8 -*-
"""
Knowledge bank for making RAG module easier to use
"""
import copy
from typing import Optional

from agentscope.models import load_model_by_config_name
from .rag import RAGBase
from .llama_index_rag import LlamaIndexRAG


DEFAULT_INDEX_CONFIG = {
    "knowledge_id": "",
    "persist_dir": "",
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
    2) make RAG model reusable and sharable for multiple agent.
    """

    def __init__(self) -> None:
        """initialize the knowledge bank"""
        self.stored_knowledge: dict[str, RAGBase] = {}

    def add_data_for_rag(
        self,
        knowledge_id: str,
        emb_model_name: str,
        data_dirs_and_types: dict[str, list[str]] = None,
        model_name: Optional[str] = None,
        persist_dir: Optional[str] = None,
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
            persist_dir (Optional[str]):
                path for storing the embedding and indexing information
            index_config (ptional[dict]):
                complete indexing configuration, used for more advanced
                applications. Users can customize
                - loader,
                - transformations,
                - ...
                Examples can refer to../examples/conversation_with_RAG_agents/
        """
        if knowledge_id in self.stored_knowledge:
            raise ValueError(f"knowledge_id {knowledge_id} already exists.")

        if persist_dir is None:
            persist_dir = "./rag_storage/"

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
            index_config["persist_dir"] = persist_dir

        self.stored_knowledge[knowledge_id] = LlamaIndexRAG(
            knowledge_id=knowledge_id,
            emb_model=load_model_by_config_name(emb_model_name),
            model=load_model_by_config_name(model_name)
            if model_name
            else None,
            index_config=index_config,
        )

    def get_rag(
        self,
        knowledge_id: str,
        duplicate: bool = False,
    ) -> RAGBase:
        """
        Get a RAG from the knowledge bank.
        Args:
            knowledge_id (str):
                unique id for the RAG
            duplicate (bool):
                whether return a copy of of the RAG.

        Returns: RAGBase
            an RAGBase object with built indexing,
            ready to be used by the agent
        """
        if knowledge_id not in self.stored_knowledge:
            raise ValueError(f"{knowledge_id} has not been added yet.")

        rag = self.stored_knowledge[knowledge_id]
        if duplicate:
            rag = copy.deepcopy(rag)

        return rag
