# -*- coding: utf-8 -*-
"""
Unit tests for pipeline classes and functions
"""

import unittest
import random

from agentscope.pipelines import (
    SequentialPipeline,
    IfElsePipeline,
    SwitchPipeline,
    ForLoopPipeline,
    WhileLoopPipeline,
    sequentialpipeline,
    ifelsepipeline,
)

from agentscope.agents import AgentBase


class Add(AgentBase):
    """Operator for adding a value"""

    def __init__(self, name: str, value: int) -> None:
        self.name = name
        self.value = value
        super().__init__(name=name)

    def __call__(self, x: dict = None) -> dict:
        x["value"] += self.value
        return x


class Mult(AgentBase):
    """Operator for multiplying a value"""

    def __init__(self, name: str, value: int) -> None:
        self.name = name
        self.value = value
        super().__init__(name=name)

    def __call__(self, x: dict = None) -> dict:
        x["value"] *= self.value
        return x


class If_agent(AgentBase):
    """Operator for If condition"""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name=name)

    def __call__(self, _: dict = None) -> dict:
        return {"operation": "A"}


class Else_agent(AgentBase):
    """Operator for Else condition"""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name=name)

    def __call__(self, _: dict = None) -> dict:
        return {"operation": "B"}


class Case_agent(AgentBase):
    """Operator for Switch condition"""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name=name)

    def __call__(self, x: dict = None) -> dict:
        return {"operation": x["text"].strip()}


class Default_agent(AgentBase):
    """Operator for Switch default condition"""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name=name)

    def __call__(self, x: dict = None) -> dict:
        return {"operation": "IDLE"}


class Loop_for_agent(AgentBase):
    """Operator for Loop condition"""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name=name)

    def __call__(self, x: dict = None) -> dict:
        x["value"] += 1
        return x


class Loop_while_agent(AgentBase):
    """Operator for Loop condition"""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name=name)

    def __call__(self, x: dict = None) -> dict:
        x["token_num"] += random.randint(1, 100)
        x["round"] += 1
        return x


class BasicPipelineTest(unittest.TestCase):
    """Test cases for Basic Pipelines"""

    def test_sequential_pipeline(self) -> None:
        """Test SequentialPipeline executes agents sequentially"""

        add1 = Add("add1", 1)
        add2 = Add("add2", 2)
        mult3 = Mult("mult3", 3)

        x = {"value": 0}
        pipeline = SequentialPipeline([add1, add2, mult3])
        self.assertEqual(pipeline(x)["value"], 9)
        x = {"value": 0}
        pipeline = SequentialPipeline([add1, mult3, add2])
        self.assertEqual(pipeline(x)["value"], 5)
        x = {"value": 0}
        pipeline = SequentialPipeline([mult3, add1, add2])
        self.assertEqual(pipeline(x)["value"], 3)

    def test_if_else_pipeline(self) -> None:
        """Test IfElsePipeline executes if or else agent based on condition"""
        if_x = {"text": "xxxx [PASS]"}
        else_x = {"text": "xxxx"}

        if_agent = If_agent("if_agent")
        else_agent = Else_agent("else_agent")

        p = IfElsePipeline(
            condition_func=lambda x: "[PASS]" in x["text"],
            if_body_operators=if_agent,
            else_body_operators=else_agent,
        )
        x = p(if_x)
        self.assertEqual(x["operation"], "A")
        x = p(else_x)
        self.assertEqual(x["operation"], "B")

    def test_switch_pipeline(self) -> None:
        """Test SwitchPipeline executes one of the case agents or the default
        agent
        """
        tool_types = ["A", "B", "C", "D"]

        case_agent = Case_agent(name="case_agent")

        default_agent = Default_agent("default_agent")

        case_agents = {k: case_agent for k in tool_types}

        p = SwitchPipeline(
            condition_func=lambda x: x["text"].strip(),
            case_operators=case_agents,
            default_operators=default_agent,
        )
        for tool in tool_types:
            x = {"text": f"\n\n{tool}\n\n"}
            x = p(x)
            self.assertEqual(x["operation"], tool)
        x = p({"text": "hello"})
        self.assertEqual(x["operation"], "IDLE")

    def test_for_pipeline(self) -> None:
        """Test ForLoopPipeline"""

        loop_agent = Loop_for_agent("loop_agent")

        # test max loop
        x = {"value": 0}
        p = ForLoopPipeline(loop_body_operators=loop_agent, max_loop=10)
        x = p(x)
        self.assertEqual(x["value"], 10)

        x = {"value": 0}
        p = ForLoopPipeline(
            loop_body_operators=loop_agent,
            max_loop=10,
            break_func=lambda x: x["value"] > 5,
        )
        x = p(x)
        self.assertEqual(x["value"], 6)

    def test_while_pipeline(self) -> None:
        """Test WhileLoopPipeline"""

        loop_agent = Loop_while_agent("loop_agent")

        p = WhileLoopPipeline(
            loop_body_operators=loop_agent,
            condition_func=lambda i, x: i < 10 and not x["token_num"] > 500,
        )
        for _ in range(50):
            x = {"token_num": 0, "round": 0}
            x = p(x)
            self.assertTrue(x["round"] >= 10 or x["token_num"] > 500)


class FunctionalPipelineTest(unittest.TestCase):
    """Test cases for Functional Pipelines"""

    def test_sequential_pipeline(self) -> None:
        """Test SequentialPipeline executes agents sequentially"""

        add1 = Add("add1", 1)
        add2 = Add("add2", 2)
        mult3 = Mult("mult3", 3)

        x = {"value": 0}
        x = sequentialpipeline(x=x, operators=[add1, add2, mult3])
        self.assertEqual(x["value"], 9)
        x = {"value": 0}
        x = sequentialpipeline(x=x, operators=[add1, mult3, add2])
        self.assertEqual(x["value"], 5)
        x = {"value": 0}
        x = sequentialpipeline(x=x, operators=[mult3, add1, add2])
        self.assertEqual(x["value"], 3)

    def test_if_else_pipeline(self) -> None:
        """Test ifelsepipeline executes if or else agent based on condition"""
        if_x = {"text": "xxxx [PASS]"}
        else_x = {"text": "xxxx"}

        if_agent = If_agent("if_agent")
        else_agent = Else_agent("else_agent")

        if_x = ifelsepipeline(
            x=if_x,
            condition_func=lambda x: "[PASS]" in x["text"],
            if_body_operators=if_agent,
            else_body_operators=else_agent,
        )
        else_x = ifelsepipeline(
            x=else_x,
            condition_func=lambda x: "[PASS]" in x["text"],
            if_body_operators=if_agent,
            else_body_operators=else_agent,
        )
        self.assertEqual(if_x["operation"], "A")
        self.assertEqual(else_x["operation"], "B")


if __name__ == "__main__":
    unittest.main()
