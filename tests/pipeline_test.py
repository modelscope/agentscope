# -*- coding: utf-8 -*-
"""Unit tests for pipeline classes and functions"""
from typing import Any, Type
from unittest.async_case import IsolatedAsyncioTestCase

from pydantic import BaseModel

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


class TaskResult(BaseModel):
    """Test structured model for pipeline testing."""

    status: str
    task_result: int
    message: str


class StructuredAgent(AgentBase):
    """Agent that supports structured_model parameter."""

    def __init__(self, name: str) -> None:
        """Initialize the agent"""
        super().__init__()
        self.name = name

    async def reply(
        self,
        x: Msg | None,
        structured_model: Type[BaseModel] | None = None,
        **kwargs: Any,
    ) -> Msg | None:
        """Reply function with structured_model support"""
        if x is None:
            return None
        if structured_model is not None:
            # Generate structured output based on the model
            if structured_model == TaskResult:
                structured_data = {
                    "status": "success",
                    "task_result": 100,
                    "message": f"Processed by {self.name}",
                }
                # Store structured data in metadata
                x.metadata.update(structured_data)
                # # Also keep track of which agents processed structured
                # models for testing
                if "structured_agents" not in x.metadata:
                    x.metadata["structured_agents"] = []
                x.metadata["structured_agents"].append(self.name)

        return x

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """Observe function"""

    async def handle_interrupt(self, *args: Any, **kwargs: Any) -> Msg:
        """Handle interrupt"""


class MixedAgent(AgentBase):
    """Agent that supports both calculation and structured_model."""

    def __init__(self, name: str, value: int) -> None:
        """Initialize the agent"""
        super().__init__()
        self.name = name
        self.value = value

    async def reply(
        self,
        x: Msg | None,
        structured_model: Type[BaseModel] | None = None,
        **kwargs: Any,
    ) -> Msg | None:
        """Reply function with both calculation and structured_model support"""
        if x is None:
            return None
        # Do calculation first
        x.metadata["result"] += self.value
        if structured_model is not None:
            # Generate structured output based on the model
            if structured_model == TaskResult:
                structured_data = {
                    "status": "success",
                    "task_result": x.metadata.get("result", 0),
                    "message": f"Processed by {self.name} with calculation",
                }
                # Store structured data in metadata
                x.metadata.update(structured_data)
                # Also keep track of which agents processed structured
                # models for testing
                if "structured_agents" not in x.metadata:
                    x.metadata["structured_agents"] = []
                x.metadata["structured_agents"].append(self.name)

        return x

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """Observe function"""

    async def handle_interrupt(self, *args: Any, **kwargs: Any) -> Msg:
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

    async def test_functional_structured(
        self,
    ) -> None:
        """Test functional sequential pipeline with structured_model
        parameter"""
        agent1 = StructuredAgent("StructuredAgent1")
        agent2 = StructuredAgent("StructuredAgent2")

        x = Msg("user", "", "user", metadata={})
        res = await sequential_pipeline(
            [agent1, agent2],
            x,
            structured_model=TaskResult,
        )
        # Verify structured output in metadata
        self.assertEqual(res.metadata["status"], "success")
        self.assertEqual(res.metadata["task_result"], 100)
        self.assertEqual(
            res.metadata["message"],
            "Processed by StructuredAgent2",
        )  # Last agent wins
        # Verify both agents processed structured models
        self.assertEqual(
            res.metadata["structured_agents"],
            ["StructuredAgent1", "StructuredAgent2"],
        )

    async def test_functional_mixed_agents_structured(
        self,
    ) -> None:
        """Test functional pipeline with mix of agents supporting and not
        supporting structured_model"""
        add1 = AddAgent(1)  # Doesn't support structured_model
        structured_agent = StructuredAgent(
            "StructuredAgent1",
        )  # Supports structured_model
        mult3 = MultAgent(3)  # Doesn't support structured_model

        x = Msg("user", "", "user", metadata={"result": 0})
        res = await sequential_pipeline(
            [add1, structured_agent, mult3],
            x,
            structured_model=TaskResult,
        )
        # Verify calculation still works: (0 + 1) * 3 = 3
        self.assertEqual(res.metadata["result"], 3)
        # Verify structured output from StructuredAgent
        self.assertEqual(res.metadata["status"], "success")
        self.assertEqual(
            res.metadata["task_result"],
            100,
        )  # StructuredAgent's fixed value
        self.assertEqual(
            res.metadata["message"],
            "Processed by StructuredAgent1",
        )
        # Only structured agent should be recorded
        self.assertEqual(
            res.metadata["structured_agents"],
            ["StructuredAgent1"],
        )

    async def test_functional_mixed_calc_structured(
        self,
    ) -> None:
        """Test functional pipeline with agents that support both
        calculation and structured_model"""
        mixed_agent1 = MixedAgent("MixedAgent1", 5)
        mixed_agent2 = MixedAgent("MixedAgent2", 10)

        x = Msg("user", "", "user", metadata={"result": 0})
        res = await sequential_pipeline(
            [mixed_agent1, mixed_agent2],
            x,
            structured_model=TaskResult,
        )
        # Verify calculation: 0 + 5 + 10 = 15
        self.assertEqual(res.metadata["result"], 15)
        # Verify structured output (should use final calc result)
        self.assertEqual(res.metadata["status"], "success")
        self.assertEqual(
            res.metadata["task_result"],
            15,
        )  # Should match final result
        self.assertEqual(
            res.metadata["message"],
            "Processed by MixedAgent2 with calculation",
        )
        # Both agents should be recorded
        self.assertEqual(
            res.metadata["structured_agents"],
            ["MixedAgent1", "MixedAgent2"],
        )

    async def test_functional_without_structured(
        self,
    ) -> None:
        """Test functional pipeline without structured_model (should work
        as before)"""
        agent1 = StructuredAgent("StructuredAgent1")
        agent2 = StructuredAgent("StructuredAgent2")

        x = Msg("user", "", "user", metadata={})
        res = await sequential_pipeline([agent1, agent2], x)
        # No structured output should be generated
        self.assertNotIn("status", res.metadata)
        self.assertNotIn("task_result", res.metadata)
        self.assertNotIn("message", res.metadata)
        self.assertNotIn("structured_agents", res.metadata)

    async def test_class_with_structured(
        self,
    ) -> None:
        """Test class-based sequential pipeline with structured_model
        parameter"""
        agent1 = StructuredAgent("StructuredAgent1")
        agent2 = StructuredAgent("StructuredAgent2")

        x = Msg("user", "", "user", metadata={})
        pipeline = SequentialPipeline([agent1, agent2])
        res = await pipeline(x, structured_model=TaskResult)
        # Verify structured output
        self.assertEqual(res.metadata["status"], "success")
        self.assertEqual(res.metadata["task_result"], 100)
        self.assertEqual(
            res.metadata["message"],
            "Processed by StructuredAgent2",
        )
        # Verify both agents processed structured models
        self.assertEqual(
            res.metadata["structured_agents"],
            ["StructuredAgent1", "StructuredAgent2"],
        )

    async def test_class_mixed_agents_structured(
        self,
    ) -> None:
        """Test class-based pipeline with mix of agents supporting and not
        supporting structured_model"""
        add1 = AddAgent(2)  # Doesn't support structured_model
        mult2 = MultAgent(2)  # Doesn't support structured_model
        structured_agent = StructuredAgent(
            "StructuredAgent1",
        )  # Supports structured_model

        x = Msg("user", "", "user", metadata={"result": 0})
        pipeline = SequentialPipeline([add1, mult2, structured_agent])
        res = await pipeline(x, structured_model=TaskResult)
        print("lalala")
        print(res)
        # Verify calculation is (0 + 2) * 2 = 4, StructuredAgent does not
        # affect "result"
        self.assertEqual(res.metadata["result"], 4)
        # Verify structured output
        self.assertEqual(res.metadata["status"], "success")
        self.assertEqual(
            res.metadata["task_result"],
            100,
        )  # StructuredAgent's fixed value
        self.assertEqual(
            res.metadata["message"],
            "Processed by StructuredAgent1",
        )
        # Only structured agent should be recorded
        self.assertEqual(
            res.metadata["structured_agents"],
            ["StructuredAgent1"],
        )

    async def test_empty_agent_list_structured(self) -> None:
        """Test pipeline with empty agent list and structured_model"""
        x = Msg("user", "", "user", metadata={"result": 42})

        # Functional pipeline
        res = await sequential_pipeline([], x, structured_model=TaskResult)
        self.assertEqual(res.metadata["result"], 42)

        # Class-based pipeline
        pipeline = SequentialPipeline([])
        res = await pipeline(x, structured_model=TaskResult)
        self.assertEqual(res.metadata["result"], 42)

    async def test_none_message_structured(self) -> None:
        """Test pipeline with None message and structured_model"""
        agent = StructuredAgent("StructuredAgent1")

        # Functional pipeline
        res = await sequential_pipeline(
            [agent],
            None,
            structured_model=TaskResult,
        )
        self.assertIsNone(res)

        # Class-based pipeline
        pipeline = SequentialPipeline([agent])
        res = await pipeline(None, structured_model=TaskResult)
        self.assertIsNone(res)
