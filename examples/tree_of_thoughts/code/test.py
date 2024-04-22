# -*- coding: utf-8 -*-
"""
This module contains unit tests for the workflow module,
including sequential and parallel workflows.

Classes:
    TestSequentialWorkFlow:
        Unit tests for the SequentialWorkFlow class.
    TestSequentialWorkFlowWhileLoop:
        Unit tests for the SequentialWorkFlow with a loop.
    TestParallelWorkFlow:
        Unit tests for the ParallelWorkFlow class.
    TestComplicatedWorkFlow:
        Unit tests for a complex workflow combining sequential
        and parallel components.
"""

import unittest
from typing import Any, Tuple
from workflow import (
    SequentialWorkFlow,
    ParallelWorkFlow,
    WorkFlowBase,
)


class TestSequentialWorkFlow(unittest.TestCase):
    """Unit tests for the SequentialWorkFlow class."""

    def setUp(self) -> None:
        def start_node(x: int) -> int:
            return x + 1

        def node_positive(x: int) -> int:
            return x + 2

        def node_negative(x: int) -> int:
            return x - 2

        def processor(
            message: Any,
            _workflow: WorkFlowBase,
            *_: Any,
            **__: Any,
        ) -> Tuple[Any, str]:  # noqa
            processed_value = message + 1
            next_node = "positive" if processed_value > 10 else "negative"
            return processed_value, next_node

        self.workflow = SequentialWorkFlow()
        self.workflow.add_node(start_node, "start")
        self.workflow.add_node(node_positive, "positive")
        self.workflow.add_node(node_negative, "negative")
        self.workflow.add_edge("start", processor)
        self.workflow.add_edge("positive", processor)
        self.workflow.set_entry_node("start")
        self.workflow.set_exit_node("negative")

    def test_workflow_execution(self) -> None:
        """Test the execution of the workflow."""
        initial_value = 5
        result = self.workflow(initial_value)
        expected_result = 7 - 2
        self.assertEqual(
            result,
            expected_result,
            f"Expected {expected_result} but got {result}",
        )


class TestSequentialWorkFlowWhileLoop(unittest.TestCase):
    """Unit tests for the SequentialWorkFlow class with a loop"""

    def setUp(self) -> None:
        def start_node(x: int) -> int:
            return x + 1

        def loop_node(x: int) -> int:
            return x - 1

        def exit_node(x: int) -> int:
            return x

        def loop_processor(
            message: Any,
            _workflow: WorkFlowBase,
            *_: Any,
            **__: Any,
        ) -> Tuple[Any, str]:  # noqa
            processed_value = message + 1
            processed_value = message + 1
            next_node = "loop_node" if processed_value < 10 else "exit_node"
            return processed_value, next_node

        self.workflow = SequentialWorkFlow()
        self.workflow.add_node(start_node, "start")
        self.workflow.add_node(loop_node, "loop_node")
        self.workflow.add_node(exit_node, "exit_node")
        self.workflow.add_edge("start", loop_processor)
        self.workflow.add_edge("loop_node", loop_processor)
        self.workflow.set_entry_node("start")
        self.workflow.set_exit_node("exit_node")

    def test_loop_execution(self) -> None:
        """Test the execution of the workflow with a loop."""
        initial_value = 8  # Start at 8, which will cause a loop.
        result = self.workflow(initial_value)
        expected_result = (
            10  # Loop should increment from 8 to 9 to 10 and then exit.
        )
        self.assertEqual(
            result,
            expected_result,
            f"Expected to terminate at {expected_result} but got {result}",
        )


class TestParallelWorkFlow(unittest.TestCase):
    """Unit tests for the ParallelWorkFlow class."""

    def setUp(self) -> None:
        # Define simple workflows for testing
        def simple_workflow_a(x: int) -> int:
            return x + 1

        def simple_workflow_b(x: int) -> int:
            return x + 2

        def sum_aggregation(results: dict) -> int:
            return sum(results.values())

        # Create workflow instances
        self.workflow_a = SequentialWorkFlow()
        self.workflow_a.add_node(simple_workflow_a, "node_a")
        self.workflow_a.set_entry_node("node_a")
        self.workflow_a.set_exit_node("node_a")

        self.workflow_b = SequentialWorkFlow()
        self.workflow_b.add_node(simple_workflow_b, "node_b")
        self.workflow_b.set_entry_node("node_b")
        self.workflow_b.set_exit_node("node_b")

        # Create Parallel Workflow
        self.parallel_workflow = ParallelWorkFlow(
            workflows={
                "workflow_a": self.workflow_a,
                "workflow_b": self.workflow_b,
            },
            aggregation_fn=sum_aggregation,
            executor_type="threadpool",
        )

    def test_parallel_execution(self) -> None:
        """Test the execution of the parallel workflow."""
        initial_value = 10
        result = self.parallel_workflow(initial_value)
        expected_result = (10 + 1) + (
            10 + 2
        )  # Sum of results from workflow_a and workflow_b
        self.assertEqual(
            result,
            expected_result,
            f"Expected result to be {expected_result} but got {result}",
        )


class TestComplicatedWorkFlow(unittest.TestCase):
    """Unit tests for a complex workflow combining
    sequential and parallel components."""

    def setUp(self) -> None:
        def start_node(x: int) -> int:
            return x + 1

        def loop_node(x: int) -> int:
            return x + 1

        def exit_node(x: int) -> int:
            return x

        def loop_processor(
            message: Any,
            _workflow: WorkFlowBase,
            *_: Any,
            **__: Any,
        ) -> Tuple[Any, str]:
            next_node = "loop_node" if message < 10 else "exit_node"
            return message, next_node

        def node_positive(x: int) -> int:
            return x + 2

        def node_negative(x: int) -> int:
            return x - 2

        def branching_processor(
            message: Any,
            _workflow: WorkFlowBase,
            *_: Any,
            **__: Any,
        ) -> Tuple[Any, str]:  # noqa
            processed_value = message + 1
            next_node = "positive" if processed_value > 10 else "negative"
            return processed_value, next_node

        def sum_aggregation(results: dict) -> int:
            return sum(results.values())

        def setup_parallel_workflow() -> ParallelWorkFlow:
            parallel_workflow = ParallelWorkFlow(executor_type="threadpool")
            while_loop_workflow = SequentialWorkFlow()
            while_loop_workflow.add_node(loop_node, "loop_node")
            while_loop_workflow.add_node(exit_node, "exit_node")
            while_loop_workflow.add_edge("loop_node", loop_processor)
            while_loop_workflow.set_entry_node("loop_node")
            while_loop_workflow.set_exit_node("exit_node")

            branching_workflow = SequentialWorkFlow()
            branching_workflow.add_node(node_positive, "positive")
            branching_workflow.add_node(node_negative, "negative")
            branching_workflow.add_edge("positive", branching_processor)
            branching_workflow.add_edge("negative", branching_processor)
            branching_workflow.set_entry_node("positive")
            branching_workflow.set_exit_node("negative")

            parallel_workflow.add_workflow("while_loop", while_loop_workflow)
            parallel_workflow.add_workflow("branching", branching_workflow)
            parallel_workflow.aggregation_fn = sum_aggregation

            return parallel_workflow

        def final_processing(x: int) -> int:
            return x + 100

        self.large_workflow = SequentialWorkFlow()
        self.large_workflow.add_node(start_node, "start")
        self.large_workflow.add_node(setup_parallel_workflow(), "parallel")
        self.large_workflow.add_node(final_processing, "final")
        self.large_workflow.add_edge("start", "parallel")
        self.large_workflow.add_edge("parallel", "final")
        self.large_workflow.set_entry_node("start")
        self.large_workflow.set_exit_node("final")

    def test_complicated_workflow(self) -> None:
        """Test the execution of the complicated workflow."""
        initial_value = 5
        result = self.large_workflow(initial_value)
        expected_result = 117
        self.assertEqual(
            result,
            expected_result,
            "The workflow did not produce the expected output.",
        )


if __name__ == "__main__":
    unittest.main()
