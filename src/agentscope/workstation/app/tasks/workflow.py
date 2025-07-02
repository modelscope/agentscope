# -*- coding: utf-8 -*-
"""Module for workflow node related functions."""
# pylint: disable=too-many-nested-blocks, too-many-nested-blocks,
# too-many-branches, too-many-statements
import json
import time
import re
from datetime import datetime
from typing import Union, Optional, Any

from app.celery_app import celery_app
from app.utils.misc import get_redis_client

from app.workflow_engine.as_workflow.pipeline_utils import workflow_pipeline
from app.db.init_db import get_session

from app.services.workflow_service import WorkflowService
from app.models.workflow import WorkflowRuntime
from app.workflow_engine.core.node_caches.node_cache_handler import NodeCache
from loguru import logger

WORKFLOW_PAYLOAD: dict[str, Any] = {
    "payload": {
        "input": {
            "messages": [],
        },
        "parameters": {
            "custom": {
                "scene": "run",
                "params": {
                    "stream": False,
                    "parameters": [],
                },
                "dsl_config": {},
            },
        },
    },
}


@celery_app.task
def run_workflow_task(
    workflow_config: dict,
    task_id: str,
    memory: Optional[list] = None,
    resume_node_id: Optional[Union[str, list]] = None,
) -> dict:
    """run workflow task"""
    # Placeholder for your workflow task logic
    start_time = int(time.time() * 1000)

    request_payload = WORKFLOW_PAYLOAD
    request_payload["payload"]["parameters"]["custom"][
        "dsl_config"
    ] = workflow_config
    if (
        "start_nodes"
        in request_payload["payload"]["parameters"]["custom"]["params"]
    ):
        request_payload["payload"]["parameters"]["custom"]["params"][
            "start_nodes"
        ] = []
    if resume_node_id:
        if isinstance(resume_node_id, str):
            resume_node_id = [resume_node_id]
        request_payload["payload"]["parameters"]["custom"]["params"][
            "start_nodes"
        ] = resume_node_id

    stime = time.time()
    package = {}

    redis_client = None
    for client in get_redis_client():
        redis_client = client
        break
    try:
        for pack_idx, package in enumerate(
            workflow_pipeline(
                request_payload["payload"],
                request_id=request_payload.get("header", {}).get("request_id"),
                memory=memory,
            ),
        ):
            package = transfer_package(package, memory)

            logger.info(
                f"------Package {pack_idx}, cost time "
                f"{time.time() - stime}------",
            )
            logger.info(
                json.dumps(
                    package,
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            if redis_client:
                current_time = datetime.now().isoformat()
                redis_key = f"workflow:task:{task_id}"
                redis_client.hset(
                    redis_key,
                    mapping={
                        "result": json.dumps(package, ensure_ascii=False),
                        "status": "processing",
                        "create_time": current_time,
                        "step": str(pack_idx),
                        "task_id": task_id,
                        "elapsed_time_ms": str(
                            int((time.time() - stime) * 1000),
                        ),
                    },
                )
                redis_client.expire(redis_key, 3600)

    except Exception as e:
        logger.error(str(e))
        if redis_client:
            redis_client.set(f"workflow:task:{task_id}:error", str(e))

    task_exec_time = int(time.time() * 1000) - start_time
    logger.info(
        f"------Total cost time {task_exec_time}------",
    )

    package["task_exec_time"] = str(task_exec_time) + "ms"

    if redis_client:
        current_time = datetime.now().isoformat()
        latest_key = f"workflow:task:{task_id}"
        redis_client.hset(
            latest_key,
            mapping={
                "result": json.dumps(package, ensure_ascii=False),
                "status": "processing",
                "create_time": current_time,
                "step": "final",
                "task_id": task_id,
                "elapsed_time_ms": str(
                    int((time.time() - stime) * 1000),
                ),
            },
        )
        redis_client.expire(latest_key, 3600)

    return package


def transfer_group_node(node_id: str, results: NodeCache) -> list:
    """transfer group node"""
    try:
        inter_results = results.results
        if not inter_results:
            return []
        middle_results = inter_results
        iter_result = inter_results[-1]
        sub_sorted_nodes = iter_result.sub_sorted_nodes
        batches_dict = {}
        batches_node_dict = {}
        usage_dict = {}
        for index, middle_results_results in enumerate(middle_results):
            if not batches_dict:
                batches_dict = {
                    node_name: []
                    for node_name in middle_results_results.sub_sorted_nodes
                }
            if not batches_node_dict:
                batches_node_dict = {
                    node_name: {}
                    for node_name in middle_results_results.sub_sorted_nodes
                }
            if not usage_dict:
                usage_dict = {
                    node_name: []
                    for node_name in middle_results_results.sub_sorted_nodes
                }
            for node_name in sub_sorted_nodes:
                if node_name not in middle_results_results["content"]:
                    continue
                content = middle_results_results["content"][node_name]
                item_results = content["results"][0]
                batches_dict[node_name].append(
                    {
                        "input": json.dumps(
                            item_results.input,
                            ensure_ascii=False,
                        ),
                        "output": json.dumps(
                            item_results.output,
                            ensure_ascii=False,
                        ),
                        "batches": item_results.batches,
                        "index": index,
                        "is_multi_branch": item_results.is_multi_branch,
                        "node_id": content.node_id,
                        "node_name": item_results.node_name,
                        "node_type": item_results.node_type,
                        "node_status": content.status,
                        "node_exec_time": item_results.node_exec_time,
                        "output_type": item_results.output_type,
                        "is_batch": item_results.is_batch,
                    },
                )
                batches_node_dict[node_name] = {
                    "is_multi_branch": item_results.is_multi_branch,
                    "node_id": content.node_id,
                    "node_name": item_results.node_name,
                    "node_type": item_results.node_type,
                    "node_status": content.status,
                    "node_exec_time": item_results.node_exec_time,
                    "output_type": item_results.output_type,
                    "parent_node_id": item_results.source,
                    "is_batch": item_results.is_batch,
                }
                if item_results.usages:
                    if node_name not in usage_dict:
                        usage_dict[node_name] = []
                    else:
                        usage_dict[node_name].extend(item_results.usages)
                else:
                    usage_dict[node_name] = []

        node_results = [
            {
                "input": json.dumps(
                    iter_result.input,
                    ensure_ascii=False,
                ),
                "output": json.dumps(
                    iter_result.output,
                    ensure_ascii=False,
                ),
                "batches": iter_result.batches,
                "is_multi_branch": iter_result.is_multi_branch,
                "node_id": node_id,
                "node_name": iter_result.node_name,
                "node_type": iter_result.node_type,
                "node_status": results.status,
                "output_type": iter_result.output_type,
                "is_batch": iter_result.is_batch,
                "node_exec_time": iter_result.node_exec_time,
            },
        ]
        node_results += [
            batches_node_dict[node_name]
            | {
                k: v
                for k, v in {
                    "batches": batches_dict[node_name],
                    "usages": usage_dict[node_name],
                }.items()
                if v
            }
            for node_name in sub_sorted_nodes
        ]

        return node_results
    except Exception as e:
        logger.error(e)
        return []


def transfer_normal_node(node_id: str, results: Any) -> dict:
    """transfer normal node"""
    output = (results.get("results") or [{}])[-1].get(
        "output",
    )
    if not isinstance(output, str):
        output = json.dumps(
            output,
            ensure_ascii=False,
        )
    node_result = {
        "node_id": node_id,
        "node_name": (results.get("results") or [{}])[-1].get(
            "node_name",
        ),
        "node_status": results.get("status"),
        "node_type": (results.get("results") or [{}])[-1].get(
            "node_type",
        ),
        "output_type": (results.get("results") or [{}])[-1].get(
            "output_type",
        ),
        "output": output,
        # "output": (value.get("results") or [{}])[-1].get(
        #     "output"),
        "node_exec_time": (results.get("results") or [{}])[-1].get(
            "node_exec_time",
        ),
        "error_info": results.get("message"),
        "error_code": results.get("workflow_code"),
        "batches": [],
        "is_multi_branch": (results.get("results") or [{}])[-1].get(
            "is_multi_branch",
            False,
        ),
        "is_batch": (results.get("results") or [{}])[-1].get(
            "is_batch",
            False,
        ),
    }
    multi_branch_results = (results.get("results") or [{}])[-1].get(
        "multi_branch_results",
    )
    if multi_branch_results:
        node_result["multi_branch_results"] = multi_branch_results

    usages = (results.get("results") or [{}])[-1].get(
        "usages",
    )
    if usages:
        node_result["usages"] = usages

    try_catch = (results.get("results") or [{}])[-1].get(
        "try_catch",
    )
    if try_catch:
        node_result["try_catch"] = try_catch

    node_input = (results.get("results") or [{}])[-1].get("input")
    if node_input:
        node_result["input"] = json.dumps(
            node_input,
            ensure_ascii=False,
        )
    return node_result


# pylint: disable=too-many-branches, too-many-statements
def transfer_package(package: dict, memory: Optional[list] = None) -> dict:
    """transfer package"""
    message = package["output"]["choices"][0]["messages"][0]
    status = message["status"]
    inter_results = status.get("inter_results")

    task_status = status.get("task_status")
    if memory:
        node_results = memory[-1].get("node_results", [])
        task_results = memory[-1].get("task_results", [])
    else:
        node_results = []
        task_results = []
    pause_nodes = status.get("pause_nodes")
    existent_node_ids = [node.get("node_id") for node in node_results]
    existent_task_ids = [task.get("node_id") for task in task_results]
    for key, value in inter_results.items():
        if key == "memory":
            continue
        if key.startswith("Iterator_") or key.startswith("Parallel_"):
            node_results.extend(transfer_group_node(key, value))
        else:
            # handle node results
            node_result = transfer_normal_node(key, value)
            if key not in existent_node_ids:
                node_results.append(node_result)
            elif key.startswith("Input"):
                existing_index = next(
                    (
                        i
                        for i, nr in enumerate(node_results)
                        if nr.get("node_id") == key
                    ),
                    None,
                )
                if existing_index is not None:
                    node_results[existing_index] = node_result
                else:
                    node_results.append(node_result)
            else:
                existing_index = next(
                    (
                        i
                        for i, nr in enumerate(node_results)
                        if nr.get("node_id") == key
                    ),
                    None,
                )
                if existing_index is not None:
                    node_results[existing_index] = node_result
                else:
                    node_results.append(node_result)

            # handle task results
            if key.startswith("End") or key.startswith("Output"):
                task_results = [
                    task_result
                    for task_result in task_results
                    if task_result.get("node_id") != key
                ]
                try:
                    node_res = json.loads(node_result["output"])
                    if isinstance(node_res, str):
                        node_result["node_content"] = node_res
                    else:
                        node_result["node_content"] = node_result["output"]
                    # node_result["node_content"] = json.loads(
                    #     node_result["output"],
                    # )
                except Exception as e:
                    logger.error(str(e))
                    node_result["node_content"] = node_result["output"]
                task_results.append(node_result)
            elif key.startswith("Input"):
                if not pause_nodes or key not in pause_nodes:
                    try:
                        input_list = json.loads(node_result["input"])
                        output_dict = json.loads(node_result["output"])
                        for item in input_list:
                            key = item["key"]
                            if key in output_dict:
                                item["value"] = output_dict[key]
                        # node_content = json.dumps(input_list)
                        node_result["node_content"] = input_list
                        existing_index = next(
                            (
                                i
                                for i, nr in enumerate(task_results)
                                if nr.get("node_id") == key
                            ),
                            None,
                        )
                        if existing_index is not None:
                            task_results[existing_index] = node_result
                        else:
                            task_results.append(node_result)
                    except Exception:
                        pass
            if pause_nodes:
                if key in pause_nodes:
                    if key not in existent_task_ids:
                        node_result["node_content"] = (
                            value.get("results") or [{}]
                        )[-1].get("input")
                        node_result["node_status"] = "pause"
                        node_result["is_batch"] = False
                        node_result["batches"] = []
                        node_result["is_multi_branch"] = False
                        node_result["output_type"] = "json"
                        task_results.append(node_result)
                        task_status = "pause"

    def filter_last_by_node_id(results: list) -> list:
        """filter last by node id"""
        node_dict = {}
        for task in results:
            node_dict[task["node_id"]] = task

        return list(node_dict.values())

    task_results = filter_last_by_node_id(task_results)
    node_results = [
        _ for _ in node_results if _ and _.get("error_info") != "Skip"
    ]
    for node_result in node_results:
        if node_result.get("error_info"):
            error_context = extract_context(node_result.get("error_info", ""))
            node_result["node_name"] = error_context.get("node_name")
            node_result["error_code"] = "Workflow Error"
            node_result["node_type"] = error_context.get("node_type")

    def sort_nodes(node_list: list) -> list:
        """sort nodes"""

        def sort_key(node: dict) -> int:
            """put end node end"""
            return 1 if node.get("node_type") == "End" else 0

        return sorted(node_list, key=sort_key)

    node_results = sort_nodes(node_results)
    data = {
        "task_status": task_status,
        "node_results": node_results,
        "task_results": task_results,
        "task_exec_time": package.get("task_exec_time"),
    }

    return data


def extract_context(error_info: str) -> Optional[dict]:
    """extract context"""
    match = re.search(r"Context: \{(.*?)\}", error_info, re.DOTALL)
    if not match:
        return None

    context_str = "{" + match.group(1) + "}"
    context_str = re.sub(r"(\w+):", r'"\1":', context_str)

    context_str = re.sub(r': ([^",{}\s][^,}]*)', r': "\1"', context_str)

    try:
        return json.loads(context_str)
    except json.JSONDecodeError:
        result = {}
        pairs = re.findall(r'"(\w+)": "([^"]*)"', context_str)
        for key, value in pairs:
            result[key] = value
        return result


@celery_app.task
def save_workflow_result(
    result: dict,
    account_id: str,
    app_id: str,
    session_id: Optional[str] = None,  # pylint: disable=unused-argument
    version: str = "latest",
    task_id: Optional[str] = None,
    inputs: Optional[list] = None,
) -> None:
    """save workflow result"""
    for session in get_session():
        try:
            workflow_service = WorkflowService(session)
            workflow_runtime = WorkflowRuntime(
                app_id=app_id,
                version=version,
                result=result,
                account_id=account_id,
                gmt_create=datetime.now(),
                gmt_modified=datetime.now(),
                task_id=task_id,
                inputs=inputs,
            )
            workflow_service.create(
                workflow_runtime,
            )
            session.commit()
            break
        except Exception as e:
            logger.info(str(e))
            session.rollback()
        finally:
            session.close()


@celery_app.task
def update_workflow_result(
    result: dict,
    account_id: str,
    app_id: str,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> None:
    """update workflow result"""
    for session in get_session():
        try:
            workflow_service = WorkflowService(session)

            filters = {
                "app_id": app_id,
            }
            if session_id:
                filters["session_id"] = session_id
            if task_id:
                filters["task_id"] = task_id
            latest_workflow_runtime = workflow_service.get_last_by_fields(
                filters=filters,
            )
            if latest_workflow_runtime:
                workflow_service.update(
                    latest_workflow_runtime.id,
                    {"result": result},
                )
                session.commit()
                logger.info(
                    f"Successfully updated WorkflowRuntime records: "
                    f"app_id={app_id}, session_id={session_id}",
                )
                break
            logger.info(
                f"No matching records found: app_id={app_id}, "
                f"session_id={session_id}",
            )
            if session_id:
                workflow_runtime = WorkflowRuntime(
                    app_id=app_id,
                    result=result,
                    account_id=account_id,
                    gmt_create=datetime.now(),
                    gmt_modified=datetime.now(),
                    task_id=task_id,
                )
            else:
                workflow_runtime = WorkflowRuntime(
                    app_id=app_id,
                    result=result,
                    account_id=account_id,
                    gmt_create=datetime.now(),
                    gmt_modified=datetime.now(),
                    task_id=task_id,
                )
            workflow_service.create(
                workflow_runtime,
            )
            session.commit()
        except Exception as e:
            logger.error(f"Update failed: {e}")
            session.rollback()
        finally:
            session.close()
