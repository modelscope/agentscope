# -*- coding: utf-8 -*-
"""Module for Iterator node related functions."""
import time

# mypy: disable-error-code=arg-type
# pylint: disable=too-many-branches, too-many-statements
from collections import OrderedDict
from typing import Dict, Any, Generator

from .workflow import WorkflowNode
from ..utils import NodeType
from ...node_cache import AgentscopeNodeCacheHandler
from ....core.node_caches.workflow_var import WorkflowVariable, DataType
from ....core.node_caches.node_cache_handler import NodeCache
from ....core.utils.misc import (
    replace_placeholders,
    remove_placeholders,
    extract_single_placeholder_fullmatch,
    get_value_from_dict,
)


class IteratorNode(WorkflowNode):
    """
    Represents a node that iterates over input parameters, executing a
    subgraph for each item in the input list. Supports termination conditions
    and output collection.
    """

    node_type: str = NodeType.ITERATOR.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        from ...interface.run import exec_runner
        from ...graph_builder import GraphBuilder

        global_cache = kwargs.get("global_cache", {})
        node_param = self.sys_args["node_param"]

        iterator_type = node_param.get("iterator_type", "byArray")

        # Use raw config to avoid var being replaced
        subgraph_config = self._build_dsl_config(
            self.node_kwargs["config"]["node_param"]["block"],
        )
        node_instance = kwargs.get("graph").node_instance

        # Variable node mapping (only happens iterator node)
        # Since the variable is set by topology, we need to get the topology
        # sorted nodes
        subgraph_builder = GraphBuilder(
            config=self.node_kwargs["config"]["node_param"]["block"],
            params=self.params,
            request_id=self.request_id,
        )
        subgraph = subgraph_builder.get_graph()
        sub_sorted_nodes = subgraph_builder.get_sorted_nodes(
            start_nodes=[],
            stop_nodes=[],
        )

        inter_var_mapping = OrderedDict()
        for node in sub_sorted_nodes:
            if subgraph.nodes[node]["type"] == NodeType.VARIABLE.value:
                for item in subgraph.nodes[node]["config"]["node_param"][
                    "inputs"
                ]:
                    k = extract_single_placeholder_fullmatch(
                        item["left"]["value"],
                    )
                    v = extract_single_placeholder_fullmatch(
                        item["right"]["value"],
                    )
                    if k:
                        inter_var_mapping[k] = v

        # Build additional global cache for iterator node
        additional_global_cache_list = []
        for item in node_param["variable_parameters"]:
            additional_global_cache_list.append(
                WorkflowVariable(
                    name=item["key"],
                    content=item["value"],
                    source=self.node_id,
                    data_type=item["type"],
                ),
            )

        input_values = [x["value"] for x in self.sys_args["input_params"]]
        output_values = [[] for _ in self.sys_args["output_params"]]
        output_var, subgraph_var = [], []
        should_break = False

        old_subgraph_var = []

        if iterator_type == "byArray":
            for iter_index, value_tuple in enumerate(zip(*input_values)):
                current_global_cache_list = additional_global_cache_list[:]

                # Build cur-round global cache with `input_params` (List Value)
                for index, param in enumerate(self.sys_args["input_params"]):
                    current_global_cache_list.append(
                        WorkflowVariable(
                            name=param["key"],
                            content=value_tuple[index],
                            source=self.node_id,
                            data_type=DataType.get_sub_type(param["type"]),
                            is_multi_branch=False,
                            is_batch=False,
                            input={},
                            batches=[],
                            output={},
                            node_name=self.node_name,
                            node_type=self.node_type,
                            output_type="json",
                            sub_sorted_nodes=sub_sorted_nodes,
                        ),
                    )

                # Add index variable to global cache
                current_global_cache_list.append(
                    WorkflowVariable(
                        name="index",
                        content=iter_index,
                        source=self.node_id,
                        data_type=DataType.NUMBER,
                    ),
                )
                updated_global_cache = {
                    **global_cache,
                    self.node_id: NodeCache(
                        results=current_global_cache_list,
                        node_id=self.node_id,
                    ),
                }

                # Build cur-round inter format map for termination conditions
                inter_format_map = (
                    AgentscopeNodeCacheHandler.retrieve_node_input(
                        self.node_id,
                        updated_global_cache,
                    )
                )
                # Check termination conditions
                conditions = replace_placeholders(
                    self.node_kwargs["config"]["node_param"]["terminations"],
                    inter_format_map,
                )
                for condition in conditions:
                    logic = condition.get("logic", "and").lower()
                    sub_conditions = condition.get("conditions", [])

                    if logic == "and":
                        result = all(
                            self._evaluate_condition(
                                sub_cond["left"],
                                sub_cond["operator"],
                                sub_cond.get("right", {}),
                            )
                            for sub_cond in sub_conditions
                        )
                    elif logic == "or":
                        result = any(
                            self._evaluate_condition(
                                sub_cond["left"],
                                sub_cond["operator"],
                                sub_cond.get("right", {}),
                            )
                            for sub_cond in sub_conditions
                        )
                    if result:
                        should_break = True
                        break

                if should_break:
                    break

                # Start iteration and execute subgraph
                for node_instance, messages in exec_runner(
                    params=self.params,
                    dsl_config=subgraph_config,
                    request_id=self.request_id,
                    node_instance=node_instance,
                    disable_pause=True,
                    inter_results=updated_global_cache,
                    subgraph_mode=True,
                ):
                    inter_results = messages[-1]["status"]["inter_results"]
                    format_map = (
                        AgentscopeNodeCacheHandler.retrieve_node_input(
                            self.node_id,
                            inter_results,
                        )
                    )
                    subgraph_var = [
                        WorkflowVariable(
                            name="subgraph",
                            content=inter_results,
                            source=self.node_id,
                            data_type=DataType.OBJECT,
                            is_multi_branch=False,
                            is_batch=False,
                            input={},
                            batches=[],
                            output={},
                            node_name=self.node_name,
                            node_type=self.node_type,
                            output_type="json",
                            sub_sorted_nodes=sub_sorted_nodes,
                        ),
                    ]
                    yield old_subgraph_var + subgraph_var + output_var
                old_subgraph_var += subgraph_var

                # Clear output_var since we reach the end of iteration
                output_var = []

                # Update inter variable with subgraph inter_results
                for workflow_variable_index, item in enumerate(
                    additional_global_cache_list,
                ):
                    if item.key in inter_var_mapping:
                        new_content = get_value_from_dict(
                            format_map,
                            inter_var_mapping[item.key],
                        )

                        if new_content:
                            additional_global_cache_list[
                                workflow_variable_index
                            ] = WorkflowVariable(
                                name=item.name,
                                content=new_content,
                                source=self.node_id,
                                data_type=item.data_type,
                                is_multi_branch=False,
                                is_batch=False,
                                input={},
                                batches=[],
                                output={},
                                node_name=self.node_name,
                                node_type=self.node_type,
                                output_type="json",
                                sub_sorted_nodes=sub_sorted_nodes,
                            )
                            format_map[item.key] = new_content  # type: ignore

                # We do not use `sys_args` here since the placeholder is
                # replaced with None value
                for index, element in enumerate(
                    self.node_kwargs["config"].get("outputParams"),
                ):
                    # Distinguish array results
                    if "[" in element["value"] and "]" in element["value"]:
                        new_value = (
                            element["value"].replace("[", "").replace("]", "")
                        )
                        output_values[index].append(
                            replace_placeholders(
                                new_value,
                                format_map,
                            ),
                        )
                    else:
                        output_values[index] = replace_placeholders(
                            element["value"],
                            format_map,
                        )

                    node_exec_time = (
                        str(int(time.time() * 1000) - start_time) + "ms"
                    )
                    # Replace and remove placeholder
                    output_var = [
                        WorkflowVariable(
                            name=element["key"],
                            content=remove_placeholders(output_values[index]),
                            source=self.node_id,
                            data_type=(
                                f"Array<{element['type']}>"
                                if isinstance(
                                    output_values[index],
                                    list,
                                )
                                else element["type"]
                            ),
                            input=self.sys_args.get("input_params"),
                            node_type=self.node_type,
                            node_name=self.node_name,
                            node_exec_time=node_exec_time,
                            sub_sorted_nodes=sub_sorted_nodes,
                        ),
                    ]
                yield old_subgraph_var + output_var

            # Make sure a return value even if break at first
            yield old_subgraph_var + output_var
        elif iterator_type == "byCount":
            for index in range(
                self.sys_args["node_param"].get(
                    "count_limit",
                    100,
                ),
            ):
                # Copy list structure
                current_global_cache_list = additional_global_cache_list[:]

                # Add index variable to global cache
                current_global_cache_list.append(
                    WorkflowVariable(
                        name="index",
                        content=index,
                        source=self.node_id,
                        data_type=DataType.NUMBER,
                    ),
                )

                updated_global_cache = {
                    **global_cache,
                    self.node_id: NodeCache(
                        results=current_global_cache_list,
                        node_id=self.node_id,
                    ),
                }

                # Build cur-round inter format map for termination conditions
                inter_format_map = (
                    AgentscopeNodeCacheHandler.retrieve_node_input(
                        self.node_id,
                        updated_global_cache,
                    )
                )
                # Check termination conditions
                conditions = replace_placeholders(
                    self.node_kwargs["config"]["node_param"]["terminations"],
                    inter_format_map,
                )
                for condition in conditions:
                    logic = condition.get("logic", "and").lower()
                    sub_conditions = condition.get("conditions", [])
                    if logic == "and":
                        result = all(
                            self._evaluate_condition(
                                sub_cond["left"],
                                sub_cond["operator"],
                                sub_cond.get("right", {}),
                            )
                            for sub_cond in sub_conditions
                        )
                    elif logic == "or":
                        result = any(
                            self._evaluate_condition(
                                sub_cond["left"],
                                sub_cond["operator"],
                                sub_cond.get("right", {}),
                            )
                            for sub_cond in sub_conditions
                        )
                    if result:
                        should_break = True
                        break

                if should_break:
                    break

                # Start iteration and execute subgraph
                for node_instance, messages in exec_runner(
                    params=self.params,
                    dsl_config=subgraph_config,
                    request_id=self.request_id,
                    node_instance=node_instance,
                    disable_pause=True,
                    inter_results=updated_global_cache,
                    subgraph_mode=True,
                ):
                    inter_results = messages[-1]["status"]["inter_results"]
                    format_map = (
                        AgentscopeNodeCacheHandler.retrieve_node_input(
                            self.node_id,
                            inter_results,
                        )
                    )
                    subgraph_var = [
                        WorkflowVariable(
                            name="subgraph",
                            content=inter_results,
                            source=self.node_id,
                            data_type=DataType.OBJECT,
                            sub_sorted_nodes=sub_sorted_nodes,
                            is_multi_branch=False,
                            is_batch=False,
                            input={},
                            batches=[],
                            output={},
                            node_name=self.node_name,
                            node_type=self.node_type,
                            output_type="json",
                        ),
                    ]
                    yield old_subgraph_var + subgraph_var + output_var
                old_subgraph_var += subgraph_var
                # Clear output_var since we reach the end of iteration
                output_var = []

                # Update inter variable with subgraph inter_results
                for workflow_variable_index, item in enumerate(
                    additional_global_cache_list,
                ):
                    if item.key in inter_var_mapping:
                        new_content = get_value_from_dict(
                            format_map,
                            inter_var_mapping[item.key],
                        )

                        if new_content:
                            additional_global_cache_list[
                                workflow_variable_index
                            ] = WorkflowVariable(
                                name=item.name,
                                content=new_content,
                                source=self.node_id,
                                data_type=item.data_type,
                                is_multi_branch=False,
                                is_batch=False,
                                input={},
                                batches=[],
                                output={},
                                node_name=self.node_name,
                                node_type=self.node_type,
                                output_type="json",
                                sub_sorted_nodes=sub_sorted_nodes,
                            )
                            format_map[item.key] = new_content  # type: ignore

                # We do not use `sys_args` here since the placeholder is
                # replaced with None value
                for index, element in enumerate(
                    self.node_kwargs["config"].get("output_params"),
                ):
                    # Distinguish array results
                    if "[" in element["value"] and "]" in element["value"]:
                        new_value = (
                            element["value"]
                            .replace("[", "")
                            .replace(
                                "]",
                                "",
                            )
                        )
                        output_values[index].append(
                            replace_placeholders(
                                new_value,
                                format_map,
                            ),
                        )
                    else:
                        output_values[index] = replace_placeholders(
                            element["value"],
                            format_map,
                        )

                    node_exec_time = (
                        str(
                            int(time.time() * 1000) - start_time,
                        )
                        + "ms"
                    )
                    # Replace and remove placeholder
                    output_var = [
                        WorkflowVariable(
                            name=element["key"],
                            content=remove_placeholders(
                                output_values[index],
                            ),
                            source=self.node_id,
                            data_type=(
                                DataType.ARRAY_OBJECT
                                if isinstance(
                                    output_values[index],
                                    list,
                                )
                                else element["type"]
                            ),
                            is_multi_branch=False,
                            is_batch=False,
                            input={},
                            batches=[],
                            output={
                                "iter_output": remove_placeholders(
                                    output_values[index],
                                ),
                            },
                            node_name=self.node_name,
                            node_type=self.node_type,
                            node_exec_time=node_exec_time,
                            output_type="json",
                            sub_sorted_nodes=sub_sorted_nodes,
                        ),
                    ]

                yield old_subgraph_var + output_var

            # Make sure a return value even if break at first
            yield old_subgraph_var + output_var

    def compile(self) -> Dict[str, Any]:
        """
        Compiles the iterator node into a structured dictionary, setting up
        iteration logic, subgraph execution, and termination conditions.
        """
        from ...interface.compile import compiler

        node_param = self.sys_args["node_param"]

        iterator_type = node_param.get("iteratorType", "byArray")
        if iterator_type == "byCount":
            count_limit = node_param.get("countLimit", 100)
        subgraph_config = node_param["block"]

        # Build statement
        statement = ""
        items = []
        for item_index, item in enumerate(
            self.sys_args["input_params"],
        ):
            statement += (
                f"{self.build_graph_var_str(item['key'])} ="
                f" {self.build_var_str(item)}\n"
            )
            items.append(self.build_graph_var_str(item["key"]))

        item_expr = ",".join(
            [self.build_graph_var_str(f"item_{x}") for x in range(len(items))],
        )

        statement += f"""
for {self.build_graph_var_str("index")}, {item_expr} in \
enumerate(zip({",".join(items)})):
"""
        if iterator_type == "byCount":
            statement += (
                f"    if {self.build_graph_var_str('index')} >="
                f" {count_limit}:\n"
            )
            statement += "        break"

        # Build loop body
        sub_dsl_config = self._build_dsl_config(subgraph_config)

        node_code_block = compiler(
            params=self.params,
            dsl_config=sub_dsl_config,
            subgraph_mode=True,
        )

        # Replace array element to single item in code
        # WARNING: This logic should be pay much attention!!!
        new_execs_node_code_block = []
        for exec_code_str in node_code_block["execs"]:
            for item_index, item_expr in enumerate(items):
                if item_expr in exec_code_str:
                    exec_code_str = exec_code_str.replace(
                        item_expr,
                        f"{self.build_graph_var_str(f'item_{item_index}')}",
                    )
                new_execs_node_code_block.append(exec_code_str)

        loop_body = new_execs_node_code_block
        import_list = node_code_block["imports"]

        # Build inter variable
        inter_var_list = []
        for var in node_param["variableParameters"]:
            var_name = var["key"]
            var_value = var["value"]
            # Can only refer
            inter_var_list.append(
                f"{self.build_graph_var_str(var_name)} = {var_value}",
            )

        # Build output results
        # handle array results with [] format (which means an Array)
        output_statement = ""
        output_execs_str = ""
        for item in self.sys_args["outputParams"]:
            if "[" in item["value"] and "]" in item["value"]:
                new_value = item["value"].replace("[", "").replace("]", "")
                output_statement += (
                    f"{self.build_graph_var_str(item['key'])} = []\n"
                )
                output_execs_str += (
                    f"{self.build_graph_var_str(item['key'])}"
                    f".append({new_value})\n"
                )
            else:
                output_execs_str += (
                    f"{self.build_graph_var_str(item['key'])} = "
                    f"{item['value']}\n"
                )
        statement = output_statement + statement

        # Build terminations
        all_conditions_list = []
        branches = node_param["terminations"]
        for index, branch in enumerate(branches):
            if branch.get("id") == "default":
                continue

            conditions = []
            for condition in branch.get("conditions", []):
                left = condition.get("left", {})
                right = condition.get("right", {})
                compiled_condition = self._compile_condition(
                    left,
                    condition.get("operator"),
                    right,
                )
                if compiled_condition:
                    conditions.append(compiled_condition)

            logic = branch.get("logic", "and").lower()
            condition_expr = f" {logic} ".join(conditions)

            if index == 0:
                exec_line = f"if {condition_expr}:\n    break"
            else:
                exec_line = f"elif {condition_expr}:\n    break"

            all_conditions_list.append(exec_line)

        loop_body = loop_body + [output_execs_str] + all_conditions_list

        # Add indent
        new_body = []
        for body_line in loop_body:
            lines = body_line.split("\n")
            for line in lines:
                new_body.append(f"{'    '}{line}")

        return {
            "imports": import_list,
            "inits": [],
            "execs": inter_var_list + [statement] + new_body,
            "increase_indent": False,
        }
