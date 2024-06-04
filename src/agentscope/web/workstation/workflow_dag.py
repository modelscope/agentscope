# -*- coding: utf-8 -*-
"""
AgentScope workstation DAG running engine.

This module defines various workflow nodes that can be used to construct
a computational DAG. Each node represents a step in the DAG and
can perform certain actions when called.
"""
import copy
from typing import Any
from loguru import logger

import agentscope
from agentscope.web.workstation.workflow_node import (
    NODE_NAME_MAPPING,
    WorkflowNodeType,
    DEFAULT_FLOW_VAR,
)
from agentscope.web.workstation.workflow_utils import (
    is_callable_expression,
    kwarg_converter,
)

try:
    import networkx as nx
except ImportError:
    nx = None


def remove_duplicates_from_end(lst: list) -> list:
    """remove duplicates element from end on a list"""
    seen = set()
    result = []
    for item in reversed(lst):
        if item not in seen:
            seen.add(item)
            result.append(item)
    result.reverse()
    return result


class ASDiGraph(nx.DiGraph):
    """
    A class that represents a directed graph, extending the functionality of
    networkx's DiGraph to suit specific workflow requirements in AgentScope.

    This graph supports operations such as adding nodes with associated
    computations and executing these computations in a topological order.

    Attributes:
        nodes_not_in_graph (set): A set of nodes that are not included in
        the computation graph.
    """

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """
        Initialize the ASDiGraph instance.
        """
        super().__init__(*args, **kwargs)
        self.nodes_not_in_graph = set()

        # Prepare the header of the file with necessary imports and any
        # global definitions
        self.imports = [
            "import agentscope",
        ]

        self.inits = [
            'agentscope.init(logger_level="DEBUG")',
            f"{DEFAULT_FLOW_VAR} = None",
        ]

        self.execs = ["\n"]

    def run(self) -> None:
        """
        Execute the computations associated with each node in the graph.

        The method initializes AgentScope, performs a topological sort of
        the nodes, and then runs each node's computation sequentially using
        the outputs from its predecessors as inputs.
        """
        agentscope.init(logger_level="DEBUG")
        sorted_nodes = list(nx.topological_sort(self))
        sorted_nodes = [
            node_id
            for node_id in sorted_nodes
            if node_id not in self.nodes_not_in_graph
        ]
        logger.info(f"sorted_nodes: {sorted_nodes}")
        logger.info(f"nodes_not_in_graph: {self.nodes_not_in_graph}")

        # Cache output
        values = {}

        # Run with predecessors outputs
        for node_id in sorted_nodes:
            inputs = [
                values[predecessor]
                for predecessor in self.predecessors(node_id)
            ]
            if not inputs:
                values[node_id] = self.exec_node(node_id)
            elif len(inputs):
                # Note: only support exec with the first predecessor now
                values[node_id] = self.exec_node(node_id, inputs[0])
            else:
                raise ValueError("Too many predecessors!")

    def compile(  # type: ignore[no-untyped-def]
        self,
        compiled_filename: str = "",
        **kwargs,
    ) -> str:
        """Compile DAG to a runnable python code"""

        def format_python_code(code: str) -> str:
            try:
                from black import FileMode, format_str

                logger.debug("Formatting Code with black...")
                return format_str(code, mode=FileMode())
            except Exception:
                return code

        self.inits[
            0
        ] = f'agentscope.init(logger_level="DEBUG", {kwarg_converter(kwargs)})'

        sorted_nodes = list(nx.topological_sort(self))
        sorted_nodes = [
            node_id
            for node_id in sorted_nodes
            if node_id not in self.nodes_not_in_graph
        ]

        for node_id in sorted_nodes:
            node = self.nodes[node_id]
            self.execs.append(node["compile_dict"]["execs"])

        header = "\n".join(self.imports)

        # Remove duplicate import
        new_imports = remove_duplicates_from_end(header.split("\n"))
        header = "\n".join(new_imports)
        body = "\n    ".join(self.inits + self.execs)

        main_body = f"def main():\n    {body}"

        # Combine header and body to form the full script
        script = (
            f"{header}\n\n\n{main_body}\n\nif __name__ == "
            f"'__main__':\n    main()\n"
        )

        formatted_code = format_python_code(script)

        if len(compiled_filename) > 0:
            # Write the script to file
            with open(compiled_filename, "w", encoding="utf-8") as file:
                file.write(formatted_code)
        return formatted_code

    # pylint: disable=R0912
    def add_as_node(
        self,
        node_id: str,
        node_info: dict,
        config: dict,
    ) -> Any:
        """
        Add a node to the graph based on provided node information and
        configuration.

        Args:
            node_id (str): The identifier for the node being added.
            node_info (dict): A dictionary containing information about the
                node.
            config (dict): Configuration information for the node dependencies.

        Returns:
            The computation object associated with the added node.
        """
        node_cls = NODE_NAME_MAPPING[node_info.get("name", "")]
        if node_cls.node_type not in [
            WorkflowNodeType.MODEL,
            WorkflowNodeType.AGENT,
            WorkflowNodeType.MESSAGE,
            WorkflowNodeType.PIPELINE,
            WorkflowNodeType.COPY,
            WorkflowNodeType.SERVICE,
        ]:
            raise NotImplementedError(node_cls)

        if self.has_node(node_id):
            return self.nodes[node_id]["opt"]

        # Init dep nodes
        deps = [str(n) for n in node_info.get("data", {}).get("elements", [])]

        # Exclude for dag when in a Group
        if node_cls.node_type != WorkflowNodeType.COPY:
            self.nodes_not_in_graph = self.nodes_not_in_graph.union(set(deps))

        dep_opts = []
        for dep_node_id in deps:
            if not self.has_node(dep_node_id):
                dep_node_info = config[dep_node_id]
                self.add_as_node(dep_node_id, dep_node_info, config)
            dep_opts.append(self.nodes[dep_node_id]["opt"])

        node_opt = node_cls(
            node_id=node_id,
            opt_kwargs=node_info["data"].get("args", {}),
            source_kwargs=node_info["data"].get("source", {}),
            dep_opts=dep_opts,
        )

        # Add build compiled python code
        compile_dict = node_opt.compile()

        self.add_node(
            node_id,
            opt=node_opt,
            compile_dict=compile_dict,
            **node_info,
        )

        # Insert compile information to imports and inits
        self.imports.append(compile_dict["imports"])

        if node_cls.node_type == WorkflowNodeType.MODEL:
            self.inits.insert(1, compile_dict["inits"])
        else:
            self.inits.append(compile_dict["inits"])
        return node_opt

    def exec_node(self, node_id: str, x_in: Any = None) -> Any:
        """
        Execute the computation associated with a given node in the graph.

        Args:
            node_id (str): The identifier of the node whose computation is
                to be executed.
            x_in: The input to the node's computation. Defaults to None.

        Returns:
            The output of the node's computation.
        """
        logger.debug(
            f"\nnode_id: {node_id}\nin_values:{x_in}",
        )
        opt = self.nodes[node_id]["opt"]
        out_values = opt(x_in)
        logger.debug(
            f"\nnode_id: {node_id}\nout_values:{out_values}",
        )
        return out_values


def sanitize_node_data(raw_info: dict) -> dict:
    """
    Clean and validate node data, evaluating callable expressions where
    necessary.

    Processes the raw node information, removes empty arguments, and evaluates
    any callable expressions provided as string literals.

    Args:
        raw_info (dict): The raw node information dictionary that may contain
            callable expressions as strings.

    Returns:
        dict: The sanitized node information with callable expressions
            evaluated.
    """

    copied_info = copy.deepcopy(raw_info)
    raw_info["data"]["source"] = copy.deepcopy(
        copied_info["data"].get(
            "args",
            {},
        ),
    )
    for key, value in copied_info["data"].get("args", {}).items():
        if value == "":
            raw_info["data"]["args"].pop(key)
            raw_info["data"]["source"].pop(key)
        elif is_callable_expression(value):
            raw_info["data"]["args"][key] = eval(value)
    return raw_info


def build_dag(config: dict) -> ASDiGraph:
    """
    Construct a Directed Acyclic Graph (DAG) from the provided configuration.

    Initializes the graph nodes based on the configuration, adds model nodes
    first, then non-model nodes, and finally adds edges between the nodes.

    Args:
        config (dict): The configuration to build the graph from, containing
            node info such as name, type, arguments, and connections.

    Returns:
        ASDiGraph: The constructed directed acyclic graph.

    Raises:
        ValueError: If the resulting graph is not acyclic.
    """
    dag = ASDiGraph()

    for node_id, node_info in config.items():
        config[node_id] = sanitize_node_data(node_info)

    # Add and init model nodes first
    for node_id, node_info in config.items():
        if (
            NODE_NAME_MAPPING[node_info["name"]].node_type
            == WorkflowNodeType.MODEL
        ):
            dag.add_as_node(node_id, node_info, config)

    # Add and init non-model nodes
    for node_id, node_info in config.items():
        if (
            NODE_NAME_MAPPING[node_info["name"]].node_type
            != WorkflowNodeType.MODEL
        ):
            dag.add_as_node(node_id, node_info, config)

    # Add edges
    for node_id, node_info in config.items():
        outputs = node_info.get("outputs", {})
        for output_key, output_val in outputs.items():
            connections = output_val.get("connections", [])
            for conn in connections:
                target_node_id = conn.get("node")
                # Here it is assumed that the output of the connection is
                # only connected to one of the inputs. If there are more
                # complex connections, modify the logic accordingly
                dag.add_edge(node_id, target_node_id, output_key=output_key)

    # Check if the graph is a DAG
    if not nx.is_directed_acyclic_graph(dag):
        raise ValueError("The provided configuration does not form a DAG.")

    return dag
