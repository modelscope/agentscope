# -*- coding: utf-8 -*-
"""
Unit tests for knowledge (RAG module in AgentScope)
"""

import os
import unittest
from typing import Any
import shutil

import agentscope
from agentscope.manager import ASManager
from agentscope.models import OpenAIEmbeddingWrapper, ModelResponse


class DummyModel(OpenAIEmbeddingWrapper):
    """
    Dummy model wrapper for testing
    """

    def __init__(self) -> None:
        """dummy init"""

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        """dummy call"""
        return ModelResponse(embedding=[[1.0, 2.0]])


class KnowledgeTest(unittest.TestCase):
    """
    Test cases for TemporaryMemory
    """

    def setUp(self) -> None:
        """set up test data"""
        agentscope.init(disable_saving=True)

        self.data_dir = "tmp_data_dir"
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        self.file_name_1 = "tmp_data_dir/file1.txt"
        self.content = "testing file"
        with open(self.file_name_1, "w", encoding="utf-8") as f:
            f.write(self.content)

    def tearDown(self) -> None:
        """Clean up before & after tests."""
        ASManager.get_instance().flush()
        try:
            if os.path.exists(self.data_dir):
                shutil.rmtree(self.data_dir)
            if os.path.exists("./runs"):
                shutil.rmtree("./runs")
            if os.path.exists("./test_knowledge"):
                shutil.rmtree("./test_knowledge")
        except Exception:
            pass

    def test_llamaindexknowledge(self) -> None:
        """test llamaindexknowledge"""
        from agentscope.rag.llama_index_knowledge import LlamaIndexKnowledge

        dummy_model = DummyModel()

        knowledge_config = {
            "knowledge_id": "",
            "data_processing": [],
        }
        loader_config = {
            "load_data": {
                "loader": {
                    "create_object": True,
                    "module": "llama_index.core",
                    "class": "SimpleDirectoryReader",
                    "init_args": {},
                },
            },
        }
        loader_init = {"input_dir": self.data_dir, "required_exts": ".txt"}

        loader_config["load_data"]["loader"]["init_args"] = loader_init
        knowledge_config["data_processing"].append(loader_config)

        knowledge = LlamaIndexKnowledge(
            knowledge_id="test_knowledge",
            emb_model=dummy_model,
            knowledge_config=knowledge_config,
        )
        retrieved = knowledge.retrieve(
            query="testing",
            similarity_top_k=2,
            to_list_strs=True,
        )
        self.assertEqual(
            retrieved,
            [self.content],
        )


if __name__ == "__main__":
    unittest.main()
