# -*- coding: utf-8 -*-
"""Module for Iterator node related functions."""
import json
import time
from concurrent.futures import ThreadPoolExecutor

# mypy: disable-error-code=arg-type
# pylint: disable=too-many-branches, too-many-statements
from typing import Dict, Any, Generator
from collections import OrderedDict

from . import WorkflowNode
from ..utils import NodeType
from ...node_cache import AgentscopeNodeCacheHandler
from ....core.node_caches.node_cache_handler import NodeCache
from ....core.node_caches.workflow_var import WorkflowVariable, DataType
from ....core.utils.misc import (
    replace_placeholders,
    extract_single_placeholder_fullmatch,
    remove_placeholders,
)


class ParallelNode(WorkflowNode):
    """
    Represents a node containing a workflow.
    """

    node_type: str = NodeType.PARALLEL.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        from ...interface.run import exec_runner
        from ...graph_builder import GraphBuilder
        import threading

        global_cache = kwargs.get("global_cache", {})
        subgraph_config = self._build_dsl_config(
            self.node_kwargs["config"]["node_param"]["block"],
        )
        node_instance = kwargs.get("graph").node_instance

        node_param = self.sys_args["node_param"]
        batch_size = node_param["batch_size"]
        concurrent_size = node_param.get("concurrent_size", 1)

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

        input_values = [
            json.loads(x["value"])[:batch_size]
            for x in self.sys_args["input_params"]
        ]
        output_values = [[] for _ in self.sys_args["output_params"]]
        # Store the results of the parallel execution with thread id,
        # result, timestamp, etc.
        parallel_results = {}
        results_lock = threading.Lock()

        # Functions that handle a single iteration
        def process_iteration(
            iter_index: int,
            value_tuple: tuple,
            thread_id: int,
        ) -> None:
            """Function for processing a single iteration"""
            result = {
                "thread_id": thread_id,
                "iter_index": iter_index,
                "timestamp": int(time.time() * 1000),
                "status": "running",
                "subgraph_var": [],
                "output_var": [],
            }

            # Build a global cache for the current iteration
            with results_lock:
                parallel_results[thread_id] = result.copy()

            try:
                # Build the global cache for the current iteration
                current_global_cache_list = []
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

                # Add index variable
                current_global_cache_list.append(
                    WorkflowVariable(
                        name="index",
                        content=iter_index,
                        source=self.node_id,
                        data_type=DataType.NUMBER,
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

                updated_global_cache = {
                    **global_cache,
                    self.node_id: NodeCache(
                        results=current_global_cache_list,
                        node_id=self.node_id,
                    ),
                }

                # execute subgraph
                format_map = None
                for _, messages in exec_runner(
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
                    sg_var = [
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

                    # Update thread result status
                    with results_lock:
                        parallel_results[thread_id]["timestamp"] = int(
                            time.time() * 1000,
                        )
                        parallel_results[thread_id]["subgraph_var"] = sg_var
                        parallel_results[thread_id]["format_map"] = format_map

                # Processing output
                out_vars = []
                local_output_values = []
                for index, element in enumerate(
                    self.node_kwargs["config"].get("output_params"),
                ):
                    if "[" in element["value"] and "]" in element["value"]:
                        new_value = (
                            element["value"]
                            .replace("[", "")
                            .replace(
                                "]",
                                "",
                            )
                        )
                        result = replace_placeholders(new_value, format_map)
                    else:
                        result = replace_placeholders(
                            element["value"],
                            format_map,
                        )
                    if result is None:
                        result = "" if "String" in element["type"] else None

                    local_output_values.append(result)
                    node_exec_time = (
                        str(
                            int(time.time() * 1000) - start_time,
                        )
                        + "ms"
                    )

                    # Create output variables
                    thread_output_type = element["type"]
                    if "Array" in thread_output_type:
                        # If it is an array type, we only use the element
                        # type at the thread level.
                        thread_output_type = thread_output_type.replace(
                            "Array<",
                            "",
                        ).replace(">", "")
                        out_vars.append(
                            WorkflowVariable(
                                name=element["key"],
                                content=remove_placeholders(result),
                                # Use original values
                                source=self.node_id,
                                data_type=thread_output_type,  # Use
                                # element types instead of array types
                                output={
                                    "p_output": remove_placeholders(
                                        result,
                                    ),
                                },
                                output_type="json",
                                input=self.sys_args.get("input_params"),
                                node_type=self.node_type,
                                node_name=self.node_name,
                                node_exec_time=node_exec_time,
                                sub_sorted_nodes=sub_sorted_nodes,
                            ),
                        )

                # Update thread results
                with results_lock:
                    parallel_results[thread_id]["timestamp"] = int(
                        time.time() * 1000,
                    )
                    parallel_results[thread_id]["status"] = "completed"
                    parallel_results[thread_id]["output_var"] = out_vars
                    parallel_results[thread_id][
                        "output_values"
                    ] = local_output_values
            except Exception as e:
                # Record error
                import traceback

                error_info = {
                    "message": str(e),
                    "thread_id": thread_id,
                    "iter_index": iter_index,
                    "traceback": traceback.format_exc(),
                }
                with results_lock:
                    parallel_results[thread_id]["timestamp"] = int(
                        time.time() * 1000,
                    )
                    parallel_results[thread_id]["status"] = "error"
                    parallel_results[thread_id]["error"] = str(e)
                    parallel_results[thread_id]["error_details"] = error_info

        # Create a task list
        tasks = list(enumerate(zip(*input_values)))

        # Initialize result tracking variables
        old_subgraph_var = []  # Processed subgraph variables
        output_var = []  # Output var
        last_check_time = time.time()
        last_yield_timestamps = {}  # Last yield timestamp for each thread
        # Use thread pool for parallel execution of tasks
        with ThreadPoolExecutor(max_workers=concurrent_size) as executor:
            # Submit all tasks to the thread pool
            for idx, val in tasks:
                thread_id = f"thread_{idx}"
                executor.submit(process_iteration, idx, val, thread_id)
            # Monitor task progress and results
            running = True
            while running:
                current_time = time.time()
                # Check for result updates at regular intervals
                if current_time - last_check_time >= 0.05:  # Check every 50ms
                    last_check_time = current_time

                with results_lock:
                    # Check if all tasks are completed
                    completed_count = sum(
                        1
                        for r in parallel_results.values()
                        if r.get("status") in ["completed", "error"]
                    )
                    if completed_count == len(tasks):
                        running = False

                    # Check for result updates from each thread
                    updated_subgraph_vars = []
                    updated_output_vars = []
                    updated = False
                    for thread_id, result in parallel_results.items():
                        timestamp_value = result.get("timestamp", 0)
                        last_timestamp_value = last_yield_timestamps.get(
                            thread_id,
                            0,
                        )
                        try:
                            if isinstance(timestamp_value, (int, float)):
                                timestamp = int(timestamp_value)
                            elif isinstance(timestamp_value, str):
                                timestamp = int(float(timestamp_value))
                            else:
                                self.logger.query_info(
                                    request_id=self.request_id,
                                    message=f"Warning: Type of timestamp"
                                    f"  in Thread {thread_id} is "
                                    f"{type(timestamp_value)}, use default "
                                    f"value.",
                                )

                            if isinstance(last_timestamp_value, (int, float)):
                                last_timestamp = int(last_timestamp_value)
                            elif isinstance(last_timestamp_value, str):
                                last_timestamp = int(
                                    float(last_timestamp_value),
                                )
                            else:
                                last_timestamp = 0
                        except Exception as e:
                            self.logger.query_error(
                                request_id=self.request_id,
                                message=f"Error info: {e}",
                            )

                        # Check if this thread has updates
                        if timestamp > last_timestamp:
                            updated = True
                            last_yield_timestamps[thread_id] = timestamp

                            # Add subgraph variables
                            if result.get("subgraph_var"):
                                for var in result["subgraph_var"]:
                                    if (
                                        var not in old_subgraph_var
                                        and var not in updated_subgraph_vars
                                    ):
                                        updated_subgraph_vars.append(var)
                                    # If task is completed, add output
                                    # variables
                            if result.get(
                                "status",
                            ) == "completed" and result.get("output_var"):
                                for var in result["output_var"]:
                                    if (
                                        var not in output_var
                                        and var not in updated_output_vars
                                    ):
                                        updated_output_vars.append(var)
                        # Update total output values
                        for i, output_val in enumerate(
                            result.get(
                                "output_values",
                                [],
                            ),
                        ):
                            if i < len(output_values):
                                if isinstance(output_values[i], list):
                                    if isinstance(output_val, list):
                                        output_values[i].extend(output_val)
                                    else:
                                        output_values[i].append(output_val)
                                else:
                                    output_values[i] = output_val
                # If there are updates, yield results
                if updated and (updated_subgraph_vars or updated_output_vars):
                    combined_vars = (
                        old_subgraph_var
                        + updated_subgraph_vars
                        + output_var
                        + updated_output_vars
                    )
                    if combined_vars:
                        yield combined_vars  # Update processed variables
                    old_subgraph_var.extend(updated_subgraph_vars)
                    output_var.extend(updated_output_vars)
                # Small pause to avoid high CPU usage
                time.sleep(0.01)

        # Ensure the last yield contains all results
        # Create an array to store merged results
        merged_outputs = [
            [] for _ in self.node_kwargs["config"].get("output_params", [])
        ]
        with results_lock:
            # Sort output results by original task order
            ordered_results = sorted(
                [
                    (int(thread_id.split("_")[1]), result)
                    for thread_id, result in parallel_results.items()
                ],
                key=lambda x: x[0],
            )
            for _, result in ordered_results:
                if result.get("status") == "completed" and result.get(
                    "output_var",
                ):
                    # Add each thread's output to the corresponding merged
                    # result
                    for i, output_val in enumerate(
                        result.get("output_values", []),
                    ):
                        if i < len(merged_outputs):
                            if output_val is not None:
                                merged_outputs[i].append(
                                    output_val,
                                )  # Add to result array

        final_vars = []
        for index, element in enumerate(
            self.node_kwargs["config"].get("output_params"),
        ):
            if index < len(merged_outputs):
                final_vars.append(
                    WorkflowVariable(
                        name=element["key"],
                        content=merged_outputs[index],  # Use the merged array
                        source=self.node_id,
                        data_type=element["type"],
                        # Use original type declaration (Array<String>)
                        output={element["key"]: merged_outputs[index]},
                        output_type="json",
                        input=self.sys_args.get("input_params"),
                        node_type=self.node_type,
                        node_name=self.node_name,
                        node_exec_time=str(
                            int(time.time() * 1000) - start_time,
                        )
                        + "ms",
                        sub_sorted_nodes=sub_sorted_nodes,
                    ),
                )

        # Final yield
        yield old_subgraph_var + final_vars

    def compile(self) -> Dict[str, Any]:
        """
        Compiles the workflow node into a structured dictionary.
        """
        from ...interface.compile import compiler

        node_param = self.sys_args["node_param"]
        subgraph_config = node_param["block"]

        statement = ""
        for item in self.sys_args["input_params"]:
            statement += (
                f"{self.build_graph_var_str(item['key'])} ="
                f" {self.build_var_str(item)}\n"
            )

        # Build body
        sub_dsl_config = self._build_dsl_config(subgraph_config)

        node_code_block = compiler(
            params=self.params,
            dsl_config=sub_dsl_config,
            subgraph_mode=True,
        )

        return {
            "imports": node_code_block["imports"],
            "inits": [],
            "execs": [statement] + node_code_block["execs"],
            "increase_indent": False,
        }
