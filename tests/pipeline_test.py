# -*- coding: utf-8 -*-
# pylint: disable=signature-differs
"""Unit tests for pipeline classes and functions"""

import unittest

from agentscope.message import Msg
from agentscope.pipelines import (
    SequentialPipeline,
    sequential_pipeline,
)

from agentscope.agents import AgentBase


class AddAgent(AgentBase):
    """Add agent class."""

    def __init__(self, value: int) -> None:
        """Initialize the agent"""
        super().__init__(name="Add")
        self.value = value

    def reply(self, x: Msg) -> Msg:
        """Reply function"""
        x.metadata += self.value
        return x


class MultAgent(AgentBase):
    """Mult agent class."""

    def __init__(self, value: int) -> None:
        """Initialize the agent"""
        super().__init__(name="Mult")
        self.value = value

    def reply(self, x: Msg) -> Msg:
        """Reply function"""
        x.metadata *= self.value
        return x


class PipelineTest(unittest.TestCase):
    """Test cases for Pipelines"""

    def test_functional_sequential_pipeline(self) -> None:
        """Test SequentialPipeline executes agents sequentially"""

        add1 = AddAgent(1)
        add2 = AddAgent(2)
        mult3 = MultAgent(3)

        x = Msg("user", "", "user", metadata=0)
        res = sequential_pipeline([add1, add2, mult3], x)
        self.assertEqual(9, res.metadata)

        x = Msg("user", "", "user", metadata=0)
        res = sequential_pipeline([add1, mult3, add2], x)
        self.assertEqual(5, res.metadata)

        x = Msg("user", "", "user", metadata=0)
        res = sequential_pipeline([mult3, add1, add2], x)
        self.assertEqual(3, res.metadata)

    def test_class_sequential_pipeline(self) -> None:
        """Test SequentialPipeline executes agents sequentially"""

        add1 = AddAgent(1)
        add2 = AddAgent(2)
        mult3 = MultAgent(3)

        x = Msg("user", "", "user", metadata=0)
        pipeline = SequentialPipeline([add1, add2, mult3])
        self.assertEqual(pipeline(x).metadata, 9)

        x = Msg("user", "", "user", metadata=0)
        pipeline = SequentialPipeline([add1, mult3, add2])
        self.assertEqual(pipeline(x).metadata, 5)

        x = Msg("user", "", "user", metadata=0)
        pipeline = SequentialPipeline([mult3, add1, add2])
        self.assertEqual(pipeline(x).metadata, 3)


if __name__ == "__main__":
    unittest.main()
