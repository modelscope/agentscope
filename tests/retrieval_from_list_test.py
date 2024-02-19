# -*- coding: utf-8 -*-
""" Python web search test."""
from datetime import datetime
import unittest
from typing import Any

from agentscope.service import retrieve_from_list, cos_sim
from agentscope.service.service_status import ServiceExecStatus
from agentscope.message import MessageBase, Msg, Tht
from agentscope.memory.temporary_memory import TemporaryMemory
from agentscope.models import OpenAIEmbeddingWrapper, ModelResponse


class TestRetrieval(unittest.TestCase):
    """TestMemRetrieval for memory retrieval unit test."""

    def test_retrieval_from_list(self) -> None:
        """test memory retrieval"""

        class DummyModel(OpenAIEmbeddingWrapper):
            """
            Dummy model wrapper for testing
            """

            def __init__(self) -> None:
                pass

            def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
                print(*args, **kwargs)
                return ModelResponse(raw={})

        dummy_model = DummyModel()

        query = Msg(name="Lora", content="test query")
        query.embedding = [0, 1]
        query.timestamp = "2023-12-18 21:40:59"
        m1 = Msg(name="env", content="test")
        m1.embedding = [1, 0]
        m1.timestamp = "2023-12-18 21:45:59"
        m2 = Msg(name="env", content="test2")
        m2.embedding = [0.5, 0.5]
        m2.timestamp = "2023-12-18 21:50:59"
        m3 = Tht(content="test3")
        m3.embedding = [0.2, 0.8]
        m3.timestamp = "2023-12-18 21:42:59"
        memory = TemporaryMemory(config={}, embedding_model=dummy_model)
        memory.add(m1)
        memory.add(m2)
        memory.add(m3)

        def score_func(m1: MessageBase, m2: MessageBase) -> float:
            relevance = cos_sim(m1.embedding, m2.embedding).content
            time_gap = (
                datetime.strptime(m1.timestamp, "%Y-%m-%d %H:%M:%S")
                - datetime.strptime(m2.timestamp, "%Y-%m-%d %H:%M:%S")
            ).total_seconds() / 60
            recency = 0.99**time_gap
            return recency + relevance

        retrieved = retrieve_from_list(
            query,
            list(memory.get_memory()),
            score_func,
            embedding_model=dummy_model,
            preserve_order=False,
        )
        self.assertEqual(retrieved.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(retrieved.content[0][2], m3)
        self.assertEqual(retrieved.content[1][2], m2)
        self.assertEqual(retrieved.content[2][2], m1)

        retrieved = retrieve_from_list(
            query,
            list(memory.get_memory(recent_n=2)),
            score_func,
            top_k=2,
            embedding_model=None,
            preserve_order=True,
        )
        self.assertEqual(retrieved.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(retrieved.content[0][2], m2)
        self.assertEqual(retrieved.content[1][2], m3)


# This allows the tests to be run from the command line
if __name__ == "__main__":
    unittest.main()
