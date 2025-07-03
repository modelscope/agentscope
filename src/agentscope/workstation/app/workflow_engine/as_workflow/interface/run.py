# -*- coding: utf-8 -*-
"""Interface for running workflow."""
# pylint: disable=too-many-branches
import copy
import time
import logging as logger
from typing import Generator, Any, Dict, List

from ..node_cache import AgentscopeNodeCacheHandler
from ..graph_builder import GraphBuilder
from ...core.engine import ParallelExecutionEngine
from ...core.utils.error import (
    UNKNOWN_ERROR_CODE,
    SUCCESS_CODE,
    CANCEL_OPERATION_CODE,
)
from ...core.status import Status
from ...core.event import SuccessEvent


def format_inter_results(
    inter_results: Dict[str, Dict[str, Any]],
    run_nodes: List[str],
    pause_nodes: List[str],
    stop_sign: Any,
) -> Dict[str, Any]:
    """
    Formats intermediate results from workflow nodes, determining overall
    task status.
    """
    formatted_results = {
        "task_status": Status.RUNNING.value,
        "run_nodes": run_nodes,
        "inter_results": inter_results,
    }

    if pause_nodes:
        formatted_results["pause_nodes"] = pause_nodes

    if isinstance(stop_sign, SuccessEvent):
        formatted_results["task_status"] = Status.SUCCEEDED.value
        formatted_results["workflow_code"] = SUCCESS_CODE
        return formatted_results

    is_any_node_running = False
    for node_id in run_nodes:
        if node_id not in inter_results:
            # Some nodes do not start, so status is running
            is_any_node_running = True
        else:
            node_status = inter_results[node_id].status
            if node_status == Status.FAILED.value:
                formatted_results["task_status"] = Status.FAILED.value
                error = stop_sign.context.get("error")
                if isinstance(error, Exception) and hasattr(error, "code"):
                    error_code = error.code
                else:
                    error_code = UNKNOWN_ERROR_CODE
                formatted_results["workflow_code"] = error_code
                return formatted_results
            elif node_status == Status.CANCELED.value:
                formatted_results["task_status"] = Status.CANCELED.value
                formatted_results["workflow_code"] = CANCEL_OPERATION_CODE
                return formatted_results
            elif node_status == Status.RUNNING.value:
                is_any_node_running = True

    # Now that we've checked all nodes, set status accordingly
    if is_any_node_running:
        formatted_results["task_status"] = Status.RUNNING.value
    else:
        formatted_results["task_status"] = Status.SUCCEEDED.value
        formatted_results["workflow_code"] = SUCCESS_CODE
    return formatted_results


# pylint: disable=unused-argument
def exec_runner(
    params: dict,
    dsl_config: dict,
    subgraph_mode: bool = False,
    **kwargs: Any,
) -> Generator:
    """
    A generator function for running workflow config.
    """
    request_id = kwargs.get("request_id", "")
    dsl_config = copy.deepcopy(dsl_config)
    workflow_config = dsl_config["workflow"]["graph"]
    node_instance = kwargs.get("node_instance", {})
    memory = kwargs.get("memory", [])

    graph_builder = GraphBuilder(
        config=workflow_config,
        params=params,
        logger=logger,
        request_id=request_id,
        node_instance=node_instance,
    )

    dag = graph_builder.get_graph()

    start_nodes = params.get("start_nodes", [])
    # Filter out nodes not in graph
    start_nodes = [x for x in start_nodes if x in dag.nodes]
    if not start_nodes:
        start_nodes = graph_builder.get_default_start_node_ids()

    stop_nodes = params.get("stop_nodes", [])
    # Filter out nodes not in graph
    stop_nodes = [x for x in stop_nodes if x in dag.nodes]

    pause_nodes = graph_builder.get_pause_nodes_by_level(start_nodes)
    disable_pause = params.get("disable_pause")

    run_nodes = graph_builder.get_sorted_nodes(
        start_nodes=start_nodes,
        stop_nodes=stop_nodes,
        pause_nodes=pause_nodes if not disable_pause else [],
    )

    # Gather inter_results
    inter_results = kwargs.get("inter_results", {})
    messages = params.get("messages", [])
    if not inter_results:
        for idx in range(len(messages) - 1, -1, -1):
            if messages[idx]["role"] == "system":
                inter_results = messages[idx]["status"]["inter_results"]
                break

    inter_results = copy.deepcopy(inter_results)
    inter_results["memory"] = memory

    # Clear cache in the inter_results
    for running_node in run_nodes:
        if running_node in inter_results.keys():
            del inter_results[running_node]

    # TODO: support single mode
    engine = ParallelExecutionEngine(
        dag,
        node_cache_handler=AgentscopeNodeCacheHandler(),
        logger=logger,
        request_id=request_id,
    )
    # Used for gather output
    end_node_id = graph_builder.get_default_end_node_ids()[0]

    current_timestamp = str(int(time.time_ns()))

    for (
        node_id,
        _,
        result,
        stop_sign,
    ) in engine.run(
        sorted_nodes=run_nodes,
        messages=params["messages"],
        run_mode=params.get("run_mode", "complete"),
        inter_results=inter_results,
    ):
        inter_results[node_id] = result

        formatted_inter_results = format_inter_results(
            inter_results,
            run_nodes,
            pause_nodes,
            stop_sign,
        )

        # Make end node output to content
        end_output = (
            formatted_inter_results["inter_results"]
            .get(
                end_node_id,
                {},
            )
            .get("results")
        )
        if isinstance(end_output, list):
            if not dag.nodes[end_node_id]["config"]["node_param"].get(
                "output_type",
            ):
                content = None
            elif (
                dag.nodes[end_node_id]["config"]["node_param"]["output_type"]
                == "text"
            ):
                content = end_output[0].content
            else:
                content = {x.name: x.content for x in end_output}
        else:
            content = None

        output_messages = [
            {
                "role": "system",
                "content": content,
                "status": formatted_inter_results,
                "msg_id": current_timestamp,
            },
        ]
        if subgraph_mode:
            # To keep the same state between graph and subgraph
            yield dag.node_instance, output_messages
        else:
            yield output_messages
