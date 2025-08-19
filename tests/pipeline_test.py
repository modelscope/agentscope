# -*- coding: utf-8 -*-
"""Unit tests for pipeline classes and functions"""
from typing import Any
from unittest.async_case import IsolatedAsyncioTestCase

from agentscope.message import Msg
from agentscope.pipeline import (
    SequentialPipeline,
    sequential_pipeline,
)

from agentscope.agent import AgentBase


class AddAgent(AgentBase):
    """Add agent class."""

    def __init__(self, value: int) -> None:
        """Initialize the agent"""
        super().__init__()
        self.name = "Add"
        self.value = value

    async def reply(self, x: Msg | None) -> Msg | None:
        """Reply function"""
        if x is None:
            return None
        x.metadata["result"] += self.value
        return x

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """Observe function"""

    async def handle_interrupt(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Msg:
        """Handle interrupt"""


class MultAgent(AgentBase):
    """Mult agent class."""

    def __init__(self, value: int) -> None:
        """Initialize the agent"""
        super().__init__()
        self.name = "Mult"
        self.value = value

    async def reply(self, x: Msg | None) -> Msg | None:
        """Reply function"""
        if x is None:
            return None
        x.metadata["result"] *= self.value
        return x

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """Observe function"""

    async def handle_interrupt(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Msg:
        """Handle interrupt"""


class PipelineTest(IsolatedAsyncioTestCase):
    """Test cases for Pipelines"""

    async def test_functional_sequential_pipeline(self) -> None:
        """Test SequentialPipeline executes agents sequentially"""

        add1 = AddAgent(1)
        add2 = AddAgent(2)
        mult3 = MultAgent(3)

        x = Msg("user", "", "user", metadata={"result": 0})
        res = await sequential_pipeline([add1, add2, mult3], x)
        self.assertEqual(9, res.metadata["result"])

        x = Msg("user", "", "user", metadata={"result": 0})
        res = await sequential_pipeline([add1, mult3, add2], x)
        self.assertEqual(5, res.metadata["result"])

        x = Msg("user", "", "user", metadata={"result": 0})
        res = await sequential_pipeline([mult3, add1, add2], x)
        self.assertEqual(3, res.metadata["result"])

    async def test_class_sequential_pipeline(self) -> None:
        """Test SequentialPipeline executes agents sequentially"""

        add1 = AddAgent(1)
        add2 = AddAgent(2)
        mult3 = MultAgent(3)

        x = Msg("user", "", "user", metadata={"result": 0})
        pipeline = SequentialPipeline([add1, add2, mult3])
        res = await pipeline(x)
        self.assertEqual(res.metadata["result"], 9)

        x = Msg("user", "", "user", metadata={"result": 0})
        pipeline = SequentialPipeline([add1, mult3, add2])
        res = await pipeline(x)
        self.assertEqual(res.metadata["result"], 5)

        x = Msg("user", "", "user", metadata={"result": 0})
        pipeline = SequentialPipeline([mult3, add1, add2])
        res = await pipeline(x)
        self.assertEqual(res.metadata["result"], 3)

    async def test_functional_sequential_pipeline_with_none_message(
        self,
    ) -> None:
        """Test functional sequential pipeline with None message input"""

        add1 = AddAgent(1)
        add2 = AddAgent(2)
        mult3 = MultAgent(3)

        # Test with None input
        res = await sequential_pipeline([add1, add2, mult3], None)
        self.assertIsNone(res)
        # Test with empty agent list and None input
        res = await sequential_pipeline([], None)
        self.assertIsNone(res)

    async def test_class_sequential_pipeline_with_none_message(self) -> None:
        """Test class-based sequential pipeline with None message input"""

        add1 = AddAgent(1)
        add2 = AddAgent(2)
        mult3 = MultAgent(3)

        # Test with None input
        pipeline = SequentialPipeline([add1, add2, mult3])
        res = await pipeline(None)
        self.assertIsNone(res)

        # Test with empty agent list and None input
        empty_pipeline = SequentialPipeline([])
        res = await empty_pipeline(None)
        self.assertIsNone(res)

    async def test_empty_agent_list(self) -> None:
        """Test pipeline with empty agent list"""

        x = Msg("user", "", "user", metadata={"result": 42})

        # Functional pipeline
        res = await sequential_pipeline([], x)
        self.assertEqual(res.metadata["result"], 42)
        self.assertEqual(res, x)  # Should return the same message object

        # Class-based pipeline
        pipeline = SequentialPipeline([])
        res = await pipeline(x)
        self.assertEqual(res.metadata["result"], 42)
        self.assertEqual(res, x)  # Should return the same message object

    async def test_single_agent_pipeline(
        self,
    ) -> None:
        """Test pipeline with single agent"""

        add1 = AddAgent(5)

        x = Msg("user", "", "user", metadata={"result": 10})

        # Functional pipeline
        res = await sequential_pipeline([add1], x)
        self.assertEqual(res.metadata["result"], 15)

        # Class-based pipeline
        pipeline = SequentialPipeline([add1])
        x = Msg("user", "", "user", metadata={"result": 10})
        res = await pipeline(x)
        self.assertEqual(res.metadata["result"], 15)

        # Test single agent with None input
        res = await sequential_pipeline([add1], None)
        self.assertIsNone(res)
        res = await pipeline(None)
        self.assertIsNone(res)
