# -*- coding: utf-8 -*-
"""Build graph for workflow"""
# pylint: disable=too-many-branches, too-many-statements
from collections import defaultdict
from typing import Any, Set, Optional, List, Dict, Union

import networkx as nx
from .constant import (
    VAR_INIT_PLACEHOLDER_SIGN,
)
from .utils.misc import (
    create_variable_mapping,
    add_indentation_to_code_lines,
    clear_script,
)
from .node import get_node_class, NodeType
from ..core.constant import PATTERN
from ..core.graph_builder import BaseGraphBuilder
from ..core.utils.error import WorkflowGraphError
from ..core.utils.misc import (
    find_value_placeholders,
    replace_placeholders,
    convert_to_fstring_format,
)
from ..core.utils.thread_safe_dict import WriteThreadSafeDict


class GraphBuilder(BaseGraphBuilder):
    """Build graph for agentscope workflow"""

    def __init__(
        self,
        config: Dict,
        params: Dict,
        logger: Any = None,
        request_id: Optional[str] = None,
        node_instance: Optional[WriteThreadSafeDict] = None,
    ) -> None:
        if node_instance is None:
            node_instance = WriteThreadSafeDict()
        self.node_instance = node_instance
        self.params = params
        self.glb_custom_args = config.get("global_config", {})

        super().__init__(
            config,
            logger,
            request_id,
            self.params.get("mock", False),
        )
        self.graph.node_instance = self.node_instance

    def _add_nodes(self) -> None:
        """Add nodes to the graph based on the configuration."""
        for node_info in self.config["nodes"]:
            node_id = node_info.get("id")
            ref_node_id = node_info.get("refId")
            node_cls = get_node_class(node_info.get("type", ""))

            if node_cls is None:
                raise WorkflowGraphError(
                    f"Node type of {node_id} not found:"
                    f" {node_info.get('type', '')}.",
                )
            node_opt_kwargs = {
                "node_id": node_id,
                "node_kwargs": node_info,
                "params": self.params,
                "glb_custom_args": self.glb_custom_args,
                "request_id": self.request_id,
                "mock": self.mock,
            }
            node_key = ref_node_id if ref_node_id else node_id
            if node_key in self.node_instance:
                node_opt = node_cls(
                    **node_opt_kwargs,
                    persistent_instance=self.node_instance[node_key],
                )
            else:
                node_opt = node_cls(**node_opt_kwargs)
                self.node_instance[node_key] = node_opt.persistent_instance
            self.graph.add_node(node_id, opt=node_opt, **node_info)
        session_params = (
            self.config.get("global_config", {})
            .get(
                "variable_config",
                {},
            )
            .get("session_params")
        )
        if session_params:
            node_opt_kwargs = {
                "node_id": "session",
                "node_kwargs": {
                    "id": "session",
                    "name": "session",
                    "type": "SessionParams",
                    "config": {
                        "variable_config": session_params,
                    },
                },
                "params": {
                    "stream": self.params.get("stream", False),
                    "parameters": session_params,
                },
                "glb_custom_args": self.glb_custom_args,
                "request_id": self.request_id,
                "mock": self.mock,
            }
            node_cls = get_node_class("SessionParams")
            node_opt = node_cls(**node_opt_kwargs)
            self.graph.add_node(
                "session",
                opt=node_opt,
                node_info=session_params,
            )

    def _add_edges(self) -> None:
        """Add edges between nodes as specified in the config."""
        # Use multi-digraph for the case that one if connects to over one node
        for edge in self.config.get("edges", []):
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                **edge,
            )

    def _verify_graph(self) -> None:
        """Verify the constructed graph for validity."""
        super()._verify_graph()
        # Verify the constructed graph for validity of copy nodes.
        for node_id, node_info in self.graph.nodes(data=True):
            ref_id = node_info.get("config", {}).get("refId")

            # Only check if there is a parent specified
            if ref_id is None:
                continue

            if not (
                nx.has_path(self.graph, node_id, ref_id)
                or nx.has_path(self.graph, ref_id, node_id)
            ):
                # TODO: should check subgraph
                raise WorkflowGraphError(
                    f"Invalid configuration: Node '{node_id}' is marked as a "
                    f"ref from node '{ref_id}', but they are not in a "
                    f"valid upstream-downstream relationship.",
                )

    def get_default_start_node_ids(self) -> List:
        """Return the node_ids of the start node."""
        if "session" in self.graph.nodes:
            node_ids = ["session"]
        else:
            node_ids = []
        for node_id, node_info in self.graph.nodes(data=True):
            if node_info.get("type") in [
                NodeType.START.value,
                NodeType.WORKFLOW_START.value,
                NodeType.ITERATOR_START.value,
                NodeType.PARALLEL_START.value,
            ]:
                node_ids.append(node_id)
        if "session" in self.graph.nodes:
            return node_ids
        if len(node_ids) == 1:
            return node_ids
        raise WorkflowGraphError(
            "Start node not found or more than one in the configuration.",
        )

    def get_default_end_node_ids(self) -> List:
        """Return the node_id of the end node."""
        node_ids = []
        for node_id, node_info in self.graph.nodes(data=True):
            if node_info.get("type") in [
                NodeType.END.value,
                NodeType.WORKFLOW_END.value,
                NodeType.ITERATOR_END.value,
                NodeType.PARALLEL_END.value,
            ]:
                node_ids.append(node_id)
        if len(node_ids) == 1:
            return node_ids
        raise WorkflowGraphError(
            "End node not found or more than one in the configuration.",
        )

    def get_pause_nodes_by_level(
        self,
        start_nodes: List[str],
    ) -> List[str]:
        """
        Return the first-level node_ids of the pause node from start nodes.
        """
        # Create a set for quick lookup of pause nodes
        pause_nodes = set()

        def dfs(node: str, visited: Set[str]) -> None:
            if node in visited:
                return

            visited.add(node)
            for neighbor in self.graph.successors(node):
                if (
                    self.graph.nodes[neighbor].get("type")
                    == NodeType.PAUSE.value
                    or self.graph.nodes[neighbor].get("type")
                    == NodeType.INPUT.value
                ):
                    pause_nodes.add(neighbor)
                    return
                dfs(neighbor, visited)

        for start_node in start_nodes:
            dfs(start_node, set())

        return list(pause_nodes)

    def get_sorted_nodes(
        self,
        start_nodes: List[str],
        stop_nodes: List[str],
        pause_nodes: Optional[List[str]] = None,
        run_mode: str = "complete",
    ) -> List[str]:
        """
        Sort nodes based on the graph's topology and run_mode and return
        sorted running nodes.
        """
        if not start_nodes:
            start_nodes = self.get_default_start_node_ids()

        all_descendant_nodes = []
        for start_node in start_nodes:
            descendant_nodes = nx.descendants(self.graph, start_node)
            descendant_nodes.add(start_node)
            all_descendant_nodes += descendant_nodes

        sorted_nodes = list(
            nx.topological_sort(
                self.graph.subgraph(set(all_descendant_nodes)),
            ),
        )

        all_stop_descendant_nodes = []
        if pause_nodes:
            cur_stop_nodes = stop_nodes + pause_nodes
        else:
            cur_stop_nodes = stop_nodes

        for stop_node in cur_stop_nodes:
            descendant_nodes = nx.descendants(self.graph, stop_node)
            descendant_nodes.add(stop_node)
            all_stop_descendant_nodes += descendant_nodes

        sorted_nodes = [
            node
            for node in sorted_nodes
            if node not in all_stop_descendant_nodes
        ]

        if run_mode == "single":
            sorted_nodes = start_nodes

        return sorted_nodes

    def build_condition_mapping(self) -> Dict:
        """
        Build a mapping of each node's condition predecessors.

        :return: A dictionary representing condition mappings.
        """
        condition_mapping = defaultdict(set)

        def broadcast(n_id: str, current_path: List) -> None:
            """
            Helper function to broadcast node ID and condition path to
            successors.
            """

            successors = self.graph.successors(n_id)

            for successor_id in successors:
                # Fetch edge data to get condition path or relevant information

                # Since we are using networkx.DiGraph, which can't contain
                # multiple edges between two nodes, we get edge_data from
                # config

                edge_datas = list(
                    self.graph.get_edge_data(
                        n_id,
                        successor_id,
                    ).values(),
                )

                for edge_data in edge_datas:
                    # We only pass the condition part for classifier and judge
                    if self.graph.nodes[n_id].get("type") in [
                        NodeType.CLASSIFIER.value,
                        NodeType.JUDGE.value,
                        NodeType.DECISION.value,
                    ]:
                        condition_part = edge_data.get("sourceHandle").split(
                            "_",
                        )[-1]
                    else:
                        condition_part = None

                    # Construct the new path, appending the current node's
                    # condition
                    new_path = (
                        current_path + [f"{n_id}.{condition_part}"]
                        if condition_part
                        else current_path
                    )

                    # Add this successor information to the mapping
                    condition_mapping[successor_id].add(tuple(new_path))

                    # Recursively broadcast to further successors
                    broadcast(successor_id, new_path)

        def build_condition_node_size_mapping() -> Dict:
            condition_node_branch_size_mapping = {}
            for node, attrs in self.graph.nodes(data=True):
                if attrs["type"] == NodeType.JUDGE.value:
                    condition_node_branch_size_mapping[node] = len(
                        attrs["config"]["node_param"]["branches"],
                    )
                elif attrs["type"] in [
                    NodeType.CLASSIFIER.value,
                    NodeType.DECISION.value,
                ]:
                    condition_node_branch_size_mapping[node] = len(
                        attrs["config"]["node_param"]["conditions"],
                    )
            return condition_node_branch_size_mapping

        def fold_conditions(
            condition_paths: Set,
            condition_size_map: Dict,
        ) -> Set:
            def fold_recursive(paths: Set) -> Set:
                # Group paths by their prefixes
                prefix_map = defaultdict(list)

                if tuple([]) in paths:
                    return set([()])

                for path in paths:
                    prefix, last = path[:-1], path[-1]
                    prefix_map[prefix].append(last)

                new_paths = set()
                for prefix, lasts in prefix_map.items():
                    # Create a map for counting occurrences of each category
                    category_set_mapping = defaultdict(set)
                    for last in lasts:
                        category, element = last.split(".")
                        category_set_mapping[category].add(element)

                    # Check and fold for each category independently
                    folded = False
                    for category, category_set in category_set_mapping.items():
                        if len(category_set) == condition_size_map.get(
                            category,
                            0,
                        ):
                            # We can fold this category
                            folded = True

                    if folded:
                        # Add the folded prefix
                        new_paths.add(prefix)
                    else:
                        for last in lasts:
                            new_paths.add(prefix + (last,))

                new_paths = remove_subpaths(new_paths)

                # If we folded something, we should recursively check again
                if len(new_paths) < len(paths):
                    return fold_recursive(new_paths)

                return new_paths

            def remove_subpaths(paths: Set) -> Set:
                # Check for the empty path and remove longer subpaths
                paths_list = list(paths)
                paths_list.sort(key=len)  # Sort paths by length
                compact_paths = set(paths_list)

                for i, path in enumerate(paths_list):
                    for longer_path in paths_list[i + 1 :]:
                        if longer_path[: len(path)] == path:
                            compact_paths.discard(longer_path)

                return compact_paths

            # Start folding from the root
            return fold_recursive(condition_paths)

        # Init the start node
        condition_mapping[self.get_default_start_node_ids()[0]].add(tuple([]))

        # Start broadcasting for start node
        broadcast(self.get_default_start_node_ids()[0], [])

        # Fold condition path mapping
        condition_size_mapping = build_condition_node_size_mapping()
        for key, value in condition_mapping.items():
            condition_mapping[key] = fold_conditions(
                value,
                condition_size_mapping,
            )

        return condition_mapping

    # TODO: not support copy node yet
    def compile(self, subgraph_mode: bool = False) -> Union[Dict, List]:
        """
        Convert graph to an executable Python code using DFS to handle tab
        indentations.
        """
        imports = [
            "import agentscope",
            'agentscope.init(logger_level="INFO")',
        ]
        execs = []
        dependency = []
        visited_mapping = defaultdict(bool)
        condition_mapping = self.build_condition_mapping()

        def format_python_code(code: str) -> str:
            try:
                from isort import code as isort_code
                from black import FileMode, format_str

                code = isort_code(code)
                return format_str(code, mode=FileMode())
            except Exception:
                return code

        def format_dependency(dep: Dict) -> Dict:
            """Formats a single dependency script."""
            return {
                **dep,
                "script": format_python_code(dep["script"]),
            }

        # Helper function for DFS
        def dfs(
            n_id: str,
            from_node: Optional[str] = None,
            indent_level: int = 0,
        ) -> None:
            # Visited, return
            if visited_mapping.get(n_id, False):
                return

            # Check whether all predecessors visited
            predecessors = self.graph.predecessors(n_id)
            for predecessor_id in predecessors:
                if not visited_mapping.get(predecessor_id, False):
                    return

            # Build `condition_predecessors`, which will be used to build
            # condition statement
            condition_predecessors = set()
            for condition_path in condition_mapping[n_id]:
                for condition_id in condition_path:
                    condition_predecessors.add(condition_id)

            # Check whether all condition predecessors visited,
            for condition_id in condition_predecessors:
                condition_node_id = condition_id.split(".")[0]
                if not visited_mapping.get(condition_node_id, False):
                    return

            # We decide to visit `n_id`
            visited_mapping[n_id] = True

            # Build condition statement
            if tuple([]) in condition_mapping[n_id]:
                condition_statement = ""
                increase_indent = False

            elif condition_mapping[n_id] == condition_mapping[from_node]:
                condition_statement = ""
                increase_indent = True

            elif condition_predecessors:
                condition_statement = "if"
                for index, condition_path in enumerate(
                    condition_mapping[n_id],
                ):
                    condition_var_path = [
                        (
                            f"${{"
                            f"{x.split('.')[0]}.condition_"
                            f"{x.split('.')[1]}}}"
                        )
                        for x in condition_path
                    ]
                    sub_condition_statement = (
                        f"{' and'.join(condition_var_path)}"
                    )

                    if index == len(condition_mapping[n_id]) - 1:
                        condition_statement += f" ({sub_condition_statement}):"
                    else:
                        condition_statement += (
                            f" ({sub_condition_statement}) or"
                        )
                increase_indent = True
            else:
                condition_statement = ""
                increase_indent = False

            node_opt = self.graph.nodes[n_id].get("opt")

            # Call the node's compile method
            node_code = node_opt.compile()

            # Extend imports, inits, and execs with node-specific code
            imports.extend(node_code["imports"])
            successors = self.graph.successors(n_id)

            # Add indent to execs
            if condition_statement:
                add_indentation_to_code_lines(
                    [condition_statement],
                    indent_level,
                    execs,
                )
            add_indentation_to_code_lines(
                node_code["inits"],
                indent_level + 1 if increase_indent else indent_level,
                execs,
            )
            add_indentation_to_code_lines(
                node_code["execs"],
                indent_level + 1 if increase_indent else indent_level,
                execs,
            )

            # Add dependency
            dependency.extend(node_code.get("dependency", []))

            # Visit each child node
            for successor in successors:
                if successor:
                    dfs(
                        successor,
                        from_node=n_id,
                        indent_level=(
                            indent_level + 1
                            if node_code.get("increase_indent", False)
                            else indent_level
                        ),
                    )

        # Start DFS from each start node
        start_nodes = self.get_default_start_node_ids()
        for node_id in start_nodes:
            dfs(node_id)

        header = "\n".join(list(imports))
        body = "\n".join(execs)
        # Combine header and body to form the full script
        script = (
            "# -*- coding: utf-8 -*-\n"
            f"{header}\n\n\n"
            f"{body}\n\n"
            f"if __name__ == '__main__':\n"
            f"""   try:
                        for result in agentscope_pipeline():
                            print(f"Result: {{result}}")
                    except Exception as e:
                        print(f"An error occurred: {{e}}")\n"""
        )

        if subgraph_mode:
            # Still keep the DO_NOT_INDENT_SIGN in the script
            # Still keep the placeholder in the script
            return {
                "imports": imports[2:],  # Remove agentscope.init
                "inits": [],
                "execs": [body],
                "increase_indent": False,
                "dependency": dependency,
            }

        script = convert_to_fstring_format(script, pattern=PATTERN)

        # Translate the placeholders in into runnable variable names
        placeholders = find_value_placeholders(
            element=script,
            pattern=PATTERN,
        )

        mapping = create_variable_mapping(placeholders)

        # Replace VAR_INIT_PLACEHOLDER_SIGN from the script
        start_nodes = self.get_default_start_node_ids()
        skip_args = ["${sys.imageList}", "${sys.query}", "${sys.historyList}"]
        for start_node in start_nodes:
            for item in self.graph.nodes[start_node]["opt"].node_kwargs[
                "config"
            ]["outputParams"]:
                skip_args.append(
                    self.graph.nodes[start_node]["opt"].build_graph_var_str(
                        item["key"],
                    ),
                )
        var_inits = []
        for key in mapping:
            if f"${{{key}}}" not in skip_args and key.count(".") <= 1:
                var_inits.append(f"${{{key}}}")
        result = (
            ", ".join(var_inits) + " = " + ", ".join(["None"] * len(var_inits))
        )
        script = script.replace(VAR_INIT_PLACEHOLDER_SIGN, result)

        # Replace placeholders in the script
        script = replace_placeholders(
            script,
            format_map=mapping,
            pattern=PATTERN,
        )

        # Remove DO_NOT_INDENT_SIGN from the script
        script = clear_script(script)

        # Format the main script
        formatted_code = format_python_code(script)

        # Format the dependency script
        formatted_dependency = [format_dependency(dep) for dep in dependency]

        return [
            {"name": "main", "path": ".", "script": formatted_code},
            *formatted_dependency,
        ]
