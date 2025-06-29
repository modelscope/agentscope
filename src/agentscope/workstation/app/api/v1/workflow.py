# -*- coding: utf-8 -*-
"""workflow base related APIs"""
import json
import uuid
import time

from app.utils.constant import MAX_WAIT
from app.utils.misc import get_redis_client
from app.utils.request_context import request_context_var

import redis
from fastapi import APIRouter, Depends
from app.schemas.workflow import (
    TaskRunRequest,
    InputInfo,
    InitQuery,
    TaskGetRequest,
    ResumeTaskQuery,
)
from app.api.deps import SessionDep, CurrentAccount
from app.schemas.response import create_response
from app.services.workflow_service import WorkflowService
from app.tasks.workflow import (
    run_workflow_task,
    save_workflow_result,
    update_workflow_result,
)
from app.models.workflow import TaskPartGraphRequest


router = APIRouter(tags=["workflow"], prefix="/apps/workflow")


@router.post("/debug/run-task")
def run_task(
    current_account: CurrentAccount,
    session: SessionDep,
    request: TaskRunRequest,
    redis_client: redis.Redis = Depends(get_redis_client),
) -> dict:
    """run task"""
    workflow_service = WorkflowService(session)
    if not request.session_id:
        workflow_session_id = str(uuid.uuid4())
    else:
        workflow_session_id = request.session_id

    version = request.version or "latest"

    workflow_config_original = workflow_service.get_workflow_config(
        account_id=current_account.account_id,
        app_id=request.app_id,
        version=version,
    )
    inputs = {"sys": {}, "user": {}}
    for input_info in request.inputs:
        if input_info.value and input_info.source and input_info.key:
            inputs[input_info.source][input_info.key] = input_info.value

    workflow_config = workflow_service.replace_variables(
        workflow_config=workflow_config_original,
        inputs=request.inputs,
    )

    workflow_config["workflow"]["graph"]["global_config"]["inputs"] = inputs

    memory = workflow_service.get_workflow_memory(
        account_id=current_account.account_id,
        app_id=request.app_id,
        workflow_session_id=workflow_session_id,
        version=version,
    )

    task_id = str(uuid.uuid4())

    workflow_task = run_workflow_task.signature(
        kwargs={
            "workflow_config": workflow_config,
            "memory": memory,
            "task_id": task_id,
        },
    )

    # task_id = workflow_task.freeze().id

    save_task = save_workflow_result.signature(
        kwargs={
            "account_id": current_account.account_id,
            "app_id": request.app_id,
            "session_id": workflow_session_id,
            "version": version,
            "task_id": task_id,
            "inputs": [
                input_info.model_dump() for input_info in request.inputs
            ],
        },
    )

    task_chain = workflow_task | save_task
    task_chain.apply_async()
    # task_chain.apply()
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT:
        result_key = f"workflow:task:{task_id}"
        if redis_client.exists(result_key):
            return create_response(
                code="200",
                message="Run task successfully.",
                data={
                    "task_id": task_id,
                    "session_id": workflow_session_id,
                    "request_id": request_context_var.get().request_id,
                },
            )
        else:
            time.sleep(0.01)

    return create_response(
        code="500",
        message="Run task failed.",
        data={
            "task_id": task_id,
            "session_id": workflow_session_id,
            "request_id": request_context_var.get().request_id,
        },
    )


@router.post("/debug/get-task-process")
def get_task_process(
    current_account: CurrentAccount,
    session: SessionDep,
    task_get_request: TaskGetRequest,
    redis_client: redis.Redis = Depends(get_redis_client),
) -> dict:
    """get task process"""

    task_id = task_get_request.task_id
    # result_key = f"celery-task-meta-{task_id}"
    result_key = f"workflow:task:{task_id}"
    data = {}
    # time.sleep(3)
    if redis_client.exists(result_key):
        # result = json.loads(redis_client.get(result_key))
        result_hash = redis_client.hgetall(result_key)
        result = json.loads(result_hash.get("result"))
        data = {
            "task_status": result.get("task_status"),
            "task_id": task_id,
            "node_results": result["node_results"],
            "task_results": result["task_results"],
            "task_exec_time": result.get("task_exec_time"),
            "request_id": request_context_var.get().request_id,
        }
    else:
        return create_response(
            code="500",
            message="Get task process failed.",
            data=data,
        )

    return create_response(
        code="200",
        message="Get task process successfully.",
        data=data,
    )


@router.post("/debug/init")
def get_init_parameters(
    current_account: CurrentAccount,
    session: SessionDep,
    init_query: InitQuery,
) -> dict:
    """get init parameters"""

    workflow_service = WorkflowService(session)

    workflow_config_original = workflow_service.get_workflow_config(
        account_id=current_account.account_id,
        app_id=init_query.app_id,
        version=init_query.version,
    )

    parameters = workflow_service.get_workflow_init_parameters(
        workflow_config_original,
    )

    return create_response(
        code="200",
        message="Get init parameters successfully.",
        data=parameters,
    )


@router.post("/debug/resume-task")
def resume_task(
    current_account: CurrentAccount,
    session: SessionDep,
    resume_task_query: ResumeTaskQuery,
) -> dict:
    """resume task"""
    workflow_service = WorkflowService(session)

    # TODO: from app service get config
    workflow_config_original = workflow_service.get_workflow_config(
        account_id=current_account.account_id,
        app_id=resume_task_query.app_id,
    )

    inputs_list = workflow_service.get_workflow_resume_inputs(
        account_id=current_account.account_id,
        app_id=resume_task_query.app_id,
        task_id=resume_task_query.task_id,
    )
    if inputs_list:
        for inputs in inputs_list:
            workflow_config_original = workflow_service.replace_variables(
                workflow_config=workflow_config_original,
                inputs=inputs,
            )

    input_params = resume_task_query.input_params
    for input_param in input_params:
        input_param["source"] = resume_task_query.resume_node_id

    workflow_config = workflow_service.replace_variables(
        workflow_config=workflow_config_original,
        inputs=input_params,
    )

    memory = workflow_service.get_workflow_memory(
        account_id=current_account.account_id,
        workflow_session_id=resume_task_query.session_id,
        app_id=resume_task_query.app_id,
        task_id=resume_task_query.task_id,
    )
    workflow_config["workflow"]["graph"]["global_config"][
        "input_params"
    ] = input_params

    workflow_task = run_workflow_task.signature(
        kwargs={
            "workflow_config": workflow_config,
            "memory": memory,
            "resume_node_id": resume_task_query.resume_node_id,
            "task_id": resume_task_query.task_id,
        },
    )

    # task_id = workflow_task.freeze().id

    save_task = update_workflow_result.signature(
        kwargs={
            "account_id": current_account.account_id,
            "app_id": resume_task_query.app_id,
            # 'session_id': resume_task_query.session_id,
            "task_id": resume_task_query.task_id,
        },
    )

    task_chain = workflow_task | save_task
    result = task_chain.apply_async()
    # result = task_chain.apply()

    return create_response(
        code="200",
        message="Resume task successfully.",
        data={
            "task_id": result.parent.id,
            "request_id": request_context_var.get().request_id,
        },
    )


@router.post("/debug/part-graph/run-task")
def part_graph_run_task(
    current_account: CurrentAccount,
    session: SessionDep,
    request: TaskPartGraphRequest,
) -> dict:
    workflow_service = WorkflowService(session)

    # Check if nodes are provided
    if not request.nodes:
        raise ValueError("Nodes must be provided for part graph run.")

    # Generate or use existing session ID
    # workflow_session_id = request.session_id or str(uuid.uuid4())

    # Default version to "latest" if not specified
    workflow_session_id = str(uuid.uuid4())

    # Retrieve and configure the workflow
    workflow_config_original = workflow_service.get_workflow_node_config(
        nodes=request.nodes,
        edges=request.edges,
    )

    input_params = request.input_params
    for input_param in input_params:
        input_param["source"], input_param["key"] = input_param["key"].split(
            ".",
        )

    workflow_config = workflow_service.replace_variables(
        workflow_config=workflow_config_original,
        inputs=input_params,
    )

    task_id = str(uuid.uuid4())

    workflow_task = run_workflow_task.signature(
        kwargs={
            "workflow_config": workflow_config,
            "task_id": task_id,
        },
    )
    workflow_task.apply_async()
    # run_workflow_task.delay(
    #     workflow_config=workflow_config,
    #     task_id=str(uuid.uuid4()),
    # )

    # Create and return the response
    return create_response(
        code="200",
        message="Run task successfully.",
        data={
            "task_id": task_id,  # Assuming result has an 'id' attribute
            "session_id": workflow_session_id,
            "request_id": request_context_var.get().request_id,
        },
    )
