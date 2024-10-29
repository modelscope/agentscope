# -*- coding: utf-8 -*-
"""
AgentScope workstation DAG running engine.

This module defines various workflow nodes that can be used to construct
a computational DAG. Each node represents a step in the DAG and
can perform certain actions when called.
"""
import copy
from typing import Any, Optional
from loguru import logger

import agentscope
from agentscope.web.workstation.workflow_node import (
    NODE_NAME_MAPPING,
    WorkflowNodeType,
    DEFAULT_FLOW_VAR,
)
from agentscope.web.workstation.workflow_utils import (
    kwarg_converter,
    replace_flow_name,
)

try:
    import networkx as nx
except ImportError:
    nx = None


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

    def __init__(
        self,
        only_compile: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the ASDiGraph instance.
        """
        super().__init__(*args, **kwargs)
        self.only_compile = only_compile
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
        if self.only_compile:
            raise ValueError("Workflow cannot run on compile mode!")

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
            elif len(inputs) == 1:
                # Note: only support exec with the first predecessor now
                values[node_id] = self.exec_node(node_id, inputs[0])
            elif len(inputs) > 1:
                values[node_id] = self.exec_node(node_id, inputs)
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
                import isort

                logger.debug("Formatting Code with black and isort...")
                return isort.code(format_str(code, mode=FileMode()))
            except Exception:
                return code

        self.inits[
            0
        ] = f'agentscope.init(logger_level="DEBUG", {kwarg_converter(kwargs)})'

        self.update_flow_name(place="execs")

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
        only_compile: bool = True,
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
            WorkflowNodeType.TOOL,
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
                self.add_as_node(
                    node_id=dep_node_id,
                    node_info=dep_node_info,
                    config=config,
                    only_compile=only_compile,
                )
            dep_opts.append(self.nodes[dep_node_id]["opt"])

        node_opt = node_cls(
            node_id=node_id,
            opt_kwargs=node_info["data"].get("args", {}),
            source_kwargs=node_info["data"].get("source", {}),
            dep_opts=dep_opts,
            only_compile=only_compile,
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

    def update_flow_name(self, place: str = "") -> None:
        """update flow name"""
        node_mapping = self.sort_parents_in_node_mapping()

        if place:
            for node_id in list(nx.topological_sort(self)):
                node = self.nodes[node_id]
                node["compile_dict"][place] = replace_flow_name(
                    node["compile_dict"][place],
                    node_mapping[node_id][1],
                    node_mapping[node_id][0],
                )

    def get_labels_for_node(self) -> dict:
        """get input and output labels for each node"""
        roots = [node for node in self.nodes() if self.in_degree(node) == 0]

        # Initialize labels dict with empty sets for parent labels
        labels = {node: (set(), "") for node in self.nodes()}

        for idx, root in enumerate(roots):
            # Each root node gets a label starting with its index
            self.label_nodes(root, f"{idx}", labels)

        # Convert parent label sets to sorted lists
        labels = {
            node: (set(sorted(parents)), label)
            for node, (parents, label) in labels.items()
        }
        return labels

    def label_nodes(
        self,
        current: str,
        label: str,
        labels: dict,
        parent: Optional[str] = None,
    ) -> None:
        """recursively label nodes allowing for multiple parents"""
        if parent:
            # Add the parent label to the current node
            labels[current][0].add(parent)

        # If the current node already has a label, it's from a shorter
        # path, so we don't overwrite it
        if not labels[current][1]:
            labels[current] = (labels[current][0], label)

        # Iterate over successors and recursively assign labels
        for i, successor in enumerate(self.successors(current)):
            # Append the index of the successor to the label for branching
            succ_label = f"{label}_{i}"
            self.label_nodes(successor, succ_label, labels, parent=label)

    def predecessor_with_edge_info(self, node_id: str) -> list[str]:
        """
        Get a sorted list of predecessor node IDs for a given node,
            based on edge information.

        Parameters:
        - node_id (str): The ID of the node for which predecessors are to
            be found and sorted.

        Returns:
        - List[str]: A list of predecessor node IDs sorted based on the
            custom sort key derived from the 'input_key' attribute in the edge
            data.
        """

        def sort_key(x: tuple) -> tuple[int, int]:
            input_key_num = int(x[2]["input_key"].split("_")[1])
            node_id_parts = x[0].split("_")
            main_id = int(node_id_parts[0])
            return input_key_num, main_id

        # Get all predecessor inputs via edges with order
        in_edges = self.in_edges(node_id, data=True)
        sorted_in_edge_list = sorted(in_edges, key=sort_key)
        return [x[0] for x in sorted_in_edge_list]

    def sort_parents_in_node_mapping(self) -> dict[str, tuple[list[str], str]]:
        """
        Updates the node mapping with sorted parent labels for each node.

        Returns:
        - Dict[str, Tuple[List[str], str]]:  An updated node mapping where
            each node ID is associated with a tuple of a sorted list of parent
            labels and the node's own label.
        """
        updated_node_mapping = {}

        for node_id in self.nodes():
            sorted_parents_ids = self.predecessor_with_edge_info(node_id)
            _, current_label = self.get_labels_for_node().get(
                node_id,
                (set(), ""),
            )

            sorted_parents_labels = []
            for parent_id in sorted_parents_ids:
                if parent_id in self.get_labels_for_node():
                    parent_label = self.get_labels_for_node()[parent_id][1]
                    sorted_parents_labels.append(parent_label)
            updated_node_mapping[node_id] = (
                sorted_parents_labels,
                current_label,
            )

        return updated_node_mapping


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
    return raw_info


def build_dag(config: dict, only_compile: bool = True) -> ASDiGraph:
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
    dag = ASDiGraph(only_compile=only_compile)

    # for html json file,
    # retrieve the contents of config["drawflow"]["Home"]["data"],
    # and remove the node whose class is "welcome"
    if (
        "drawflow" in config
        and "Home" in config["drawflow"]
        and "data" in config["drawflow"]["Home"]
    ):
        config = config["drawflow"]["Home"]["data"]

        config = {
            k: v
            for k, v in config.items()
            if not ("class" in v and v["class"] == "welcome")
        }

    for node_id, node_info in config.items():
        config[node_id] = sanitize_node_data(node_info)

    # Add and init model nodes first
    for node_id, node_info in config.items():
        if (
            NODE_NAME_MAPPING[node_info["name"]].node_type
            == WorkflowNodeType.MODEL
        ):
            dag.add_as_node(
                node_id,
                node_info,
                config,
                only_compile=only_compile,
            )

    # Add and init non-model nodes
    for node_id, node_info in config.items():
        if (
            NODE_NAME_MAPPING[node_info["name"]].node_type
            != WorkflowNodeType.MODEL
        ):
            dag.add_as_node(
                node_id,
                node_info,
                config,
                only_compile=only_compile,
            )

    # Add edges
    for node_id, node_info in config.items():
        inputs = node_info.get("inputs", {})
        for input_key, input_val in inputs.items():
            connections = input_val.get("connections", [])
            for conn in connections:
                target_node_id = conn.get("node")
                dag.add_edge(target_node_id, node_id, input_key=input_key)

    # Check if the graph is a DAG
    if not nx.is_directed_acyclic_graph(dag):
        raise ValueError("The provided configuration does not form a DAG.")

    return dag
