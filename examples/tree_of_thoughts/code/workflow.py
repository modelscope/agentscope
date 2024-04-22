# -*- coding: utf-8 -*-
"""
This module provides implementations for workflow management,
including sequential and parallel workflows.

Classes:
    WorkFlowBase:
        Base class for workflows.
        It contains the logic for processing nodes and edges in a workflow.
    Processor:
        Protocol for defining processors used in workflows.
    SequentialWorkFlow:
        Implementation of a sequential workflow.
    AggregationCallable:
        Protocol for aggregation functions used in workflows.
    ParallelWorkFlow:
        Implementation of a parallel workflow.
"""
from concurrent.futures import ThreadPoolExecutor
from typing import (
    Callable,
    Dict,
    Tuple,
    Any,
    Protocol,
    Optional,
    Literal,
    runtime_checkable,
)
from abc import ABC, abstractmethod


class WorkFlowBase(ABC):
    """
    Base class for workflows.
    It contains the logic for processing nodes and edges in a workflow.
    """

    def __init__(self) -> None:
        """
        Initializes the WorkFlowBase object.

        Returns:
            None
        """
        self.contexts: Dict[str, Any] = {}

    def register_contexts(self, contexts: Dict[str, Any]) -> None:
        """
        Registers the contexts for the workflow.

        Args:
            contexts (Dict[str, Any]):
                A dictionary containing context information.

        Returns:
            None
        """
        self.contexts = contexts

    @abstractmethod
    def __call__(
        self,
        initial_messages: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Executes the workflow.

        This method is abstract and must be implemented by subclasses.

        Args:
            initial_messages (Any): Initial input messages.
            *args (Any): Additional arguments.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            Any: Output of the workflow execution.
        """


@runtime_checkable
class Processor(Protocol):
    """
    Protocol for defining processors.
    """

    def __call__(
        self,
        message: Any,
        workflow: WorkFlowBase,
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[Any, str]:
        """
        Process the message.

        Args:
            message (Any): Input message.
            workflow (WorkFlowBase): Workflow instance.
            *args (Any): Additional arguments.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            Tuple[Any, str]: Processed message and next node.
        """
        return message, "EXIT"


class SequentialWorkFlow(WorkFlowBase):
    """
    Sequential workflow implementation.
    """

    def __init__(self) -> None:
        """
        Initializes the SequentialWorkFlow object.

        Returns:
            None
        """
        super().__init__()
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, Processor] = {}
        self.entry_node = None
        self.exit_node = None

    def add_node(self, agent: Callable, name: str) -> None:
        """
        Adds a node to the workflow.

        Args:
            agent (Callable): Callable representing the node.
            name (str): Name of the node.

        Returns:
            None
        """
        if name in self.nodes:
            raise ValueError(f"Node {name} already exists.")
        self.nodes[name] = agent

    def add_edge(self, src_node: str, processor_or_dst_node: Any) -> None:
        """
        Adds an edge to the workflow.

        Args:
            src_node (str): Name of the source node.
            processor_or_dst_node (Any): Processor or destination node.

        Returns:
            None
        """
        if src_node not in self.nodes:
            raise ValueError(f"Node {src_node} does not exist.")
        if isinstance(processor_or_dst_node, Processor):
            self.edges[src_node] = processor_or_dst_node
        elif isinstance(processor_or_dst_node, str):
            dst_node = processor_or_dst_node
            if dst_node not in self.nodes:
                raise ValueError(
                    f"Destination node {dst_node} does not exist.",
                )

            def default_processor(
                message: Any,
                workflow: WorkFlowBase,
                *args: Any,
                **kwargs: Any,
            ) -> Tuple[Any, str]:  # pylint: disable=unused-argument
                # Default processor that
                # forwards the message to the destination node.
                # does not use the workflow, args, or kwargs.
                _ = workflow, args, kwargs
                return message, dst_node

            if src_node in self.edges:
                raise ValueError(
                    f"Edge already exists from {src_node}."
                    + "To overwrite, remove the existing edge first.",
                )
            self.edges[src_node] = default_processor
        else:
            raise TypeError(
                "processor_or_dst_node must be either a Processor"
                + "instance or a string representing a node name.",
            )

    def set_entry_node(self, node: str) -> None:
        """
        Sets the entry node of the workflow.

        Args:
            node (str): Name of the entry node.

        Returns:
            None
        """
        assert node in self.nodes, f"Node {node} does not exist."
        self.entry_node = node

    def set_exit_node(self, node: str) -> None:
        """
        Sets the exit node of the workflow.

        Args:
            node (str): Name of the exit node.

        Returns:
            None
        """
        assert node in self.nodes, f"Node {node} does not exist."
        self.exit_node = node

    def __call__(
        self,
        initial_messages: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Executes the workflow.

        Args:
            initial_message (Any): Initial message.
            *args (Any): Additional arguments.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            Any: Output of the workflow execution.
        """
        if self.entry_node is None or self.exit_node is None:
            raise ValueError("Entry or exit node not set.")
        current_node = self.entry_node
        current_message = self.nodes[current_node](
            initial_messages,
            *args,
            **kwargs,
        )
        while current_node != self.exit_node:
            processor = self.edges[current_node]
            current_message, next_node = processor(
                current_message,
                self,
                *args,
                **kwargs,
            )
            current_node = next_node
            if current_node in self.nodes:
                current_message = self.nodes[current_node](
                    current_message,
                    *args,
                    **kwargs,
                )
            else:
                break
        return current_message


class AggregationCallable(Protocol):
    """
    Protocol for aggregation functions used in workflows.
    """

    def __call__(self, results: Dict[str, Any]) -> Any:
        """
        Defines the call signature for aggregation functions.

        Args:
            results (Dict[str, Any]):
                Dictionary containing results from different workflows.

        Returns:
            Any: Aggregated result.
        """


class ParallelWorkFlow(WorkFlowBase):
    """
    Parallel workflow implementation.
    """

    def __init__(
        self,
        workflows: Optional[Dict[str, SequentialWorkFlow]] = None,
        aggregation_fn: Optional[AggregationCallable] = None,
        executor_type: Literal["threadpool"] = "threadpool",
    ) -> None:
        """
        Initializes the ParallelWorkFlow object.

        Args:
            workflows (Optional[Dict[str, SequentialWorkFlow]]):
                Dictionary containing workflows.
            aggregation_fn (Optional[AggregationCallable]):
                Function for aggregating results.
            executor_type (Literal["threadpool"], optional):
                Type of executor. Defaults to "threadpool".

        Returns:
            None
        """
        super().__init__()
        self.workflows = workflows if workflows else {}
        self.aggregation_fn = aggregation_fn
        self.executor_type = executor_type

    def add_workflow(self, name: str, workflow: SequentialWorkFlow) -> None:
        """
        Adds a workflow to the parallel workflow.

        Args:
            name (str): Name of the workflow.
            workflow (SequentialWorkFlow): Sequential workflow object.

        Returns:
            None
        """
        if name in self.workflows:
            raise ValueError(f"Workflow {name} already exists.")
        self.workflows[name] = workflow

    def __call__(
        self,
        initial_messages: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Executes the parallel workflow.

        Args:
            initial_message (Any): Initial message.
            *args (Any): Additional arguments.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            Any: Output of the parallel workflow execution.
        """
        assert self.workflows, "No workflows added."
        results = {}
        if self.executor_type == "threadpool":
            with ThreadPoolExecutor() as executor:
                futures = {
                    name: executor.submit(
                        workflow,
                        initial_messages,
                        *args,
                        **kwargs,
                    )
                    for name, workflow in self.workflows.items()
                }
                for name, future in futures.items():
                    results[name] = future.result()
        if self.aggregation_fn:
            final_result = self.aggregation_fn(results)
        else:
            final_result = results
        return final_result
