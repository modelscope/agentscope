# -*- coding: utf-8 -*-
"""The workflow related services"""
import json
import re
from typing import Sequence, Optional, List, Any

from app.services.app_service import AppService
from .base_service import BaseService
from app.dao.workflow_dao import WorkflowDao
from sqlmodel import Session


def get_workflow_node_config(
    nodes: Optional[list[dict]],
    edges: Optional[list[dict]] = None,
) -> dict:
    """build graph config for nodes"""
    assert (
        nodes is not None
        and len(
            nodes,
        )
        > 0
    ), "Nodes list cannot be None or empty"

    # Definition of Start Node
    start_node: dict[str, Any] = {
        "id": "Start_1",
        "name": "开始",
        "config": {
            "input_params": [],
            "output_params": [
                {
                    "key": "start_output",
                    "type": "String",
                    "desc": "",
                    "properties": [],
                },
            ],
            "node_param": {},
        },
        "position": {"x": 100, "y": 100},
        "width": 320,
        "type": "Start",
    }

    # Definition of End Node
    end_node: dict[str, Any] = {
        "id": "End_1",
        "name": "结束",
        "config": {
            "input_params": [],
            "output_params": [],
            "node_param": {
                "output_type": "text",
                "text_template": "",
                "json_params": [
                    {
                        "key": "output",
                        "value_from": "refer",
                        "type": "String",
                    },
                ],
                "stream_switch": True,
            },
        },
        "position": {
            "x": 500,
            "y": 500,
        },  # Sample location, adjustable as needed.
        "width": 320,
        "type": "End",
    }

    # Add start and end nodes to the node list.
    workflow_nodes = [start_node] + [end_node]
    if nodes:
        workflow_nodes.extend(nodes)

    # Build edge list.
    new_edges = [
        {
            "id": f"{start_node['id']}-{nodes[0]['id']}",
            "source": start_node["id"],
            "target": nodes[0]["id"],
            "source_handle": start_node["id"],
            "target_handle": nodes[0]["id"],
        },
        {
            "id": f"{nodes[-1]['id']}-{end_node['id']}",
            "source": nodes[-1]["id"],
            "target": end_node["id"],
            "source_handle": nodes[-1]["id"],
            "target_handle": end_node["id"],
        },
    ]
    if edges:
        new_edges = edges + new_edges

    # Build the final configuration.
    workflow_config = {
        "nodes": workflow_nodes,
        "edges": new_edges,
        "global_config": {
            "history_config": {
                "history_max_round": 5,
                "history_switch": False,
            },
            "variable_config": {
                "session_params": [],
            },
        },
    }

    config = {
        "name": "",
        "type": "",
        "workflow": {
            "graph": workflow_config,
        },
    }

    return config


class WorkflowService(BaseService[WorkflowDao]):
    """Service layer for workflow."""

    _dao_cls = WorkflowDao

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.app_service = AppService(session=session)

    def get_workflow_config(
        self,
        account_id: str,
        app_id: str,
        version: Optional[str] = "latest",
        inputs: Optional[list] = None,
    ) -> dict:
        """get workflow config"""

        config = self.app_service.get_app(
            app_id=app_id,
            workspace_id="1",
        )
        workflow_config = {
            "workflow": {
                "graph": config.config,
            },
        }
        return workflow_config

    def get_workflow_node_config(
        self,
        nodes: Optional[List[dict]] = None,
        edges: Optional[List[dict]] = None,
    ) -> dict:
        """get workflow config"""

        workflow_config = get_workflow_node_config(nodes, edges)
        return workflow_config

    def replace_variables(
        self,
        workflow_config: dict,
        inputs: Optional[list[Any]] = None,
    ) -> dict:
        """replace variables in workflow config"""
        if inputs:
            if isinstance(inputs[0], dict):
                input_map = {
                    (f"{item['source']}." f"{item['key']}"): item["value"]
                    for item in inputs
                }

                user_map = {
                    item["key"]: item["value"]
                    for item in inputs
                    if item["source"] == "user"
                }
            else:
                input_map = {
                    f"{item.source}.{item.key}": item.value for item in inputs
                }

                user_map = {
                    item.key: item.value
                    for item in inputs
                    if item.source == "user"
                }
        else:
            input_map = {}
            user_map = {}
        pattern = re.compile(r"\${([^}]+)}")

        def process_value(value: Any) -> str:
            if not isinstance(value, str):
                return value

            def replace_match(match: re.Match) -> str:
                key = match.group(1)
                if key in input_map:
                    return str(input_map[key])
                if key.startswith("Start_"):
                    parts = key.split(".", 1)
                    if len(parts) == 2 and parts[1] in user_map:
                        return str(user_map[parts[1]])
                return match.group(0)

            return pattern.sub(replace_match, value)

        def process_node(node: Any) -> Any:
            if isinstance(node, dict):
                return {k: process_node(v) for k, v in node.items()}
            elif isinstance(node, list):
                return [process_node(item) for item in node]
            else:
                return process_value(node)

        return process_node(workflow_config)

    def get_workflow_memory(
        self,
        account_id: str,
        app_id: str,
        workflow_session_id: Optional[str],
        version: str = "latest",
        task_id: Optional[str] = None,
    ) -> list:
        """get workflow memory"""
        if not version:
            version = "latest"
        filters = {
            "account_id": account_id,
            "app_id": app_id,
            "version": version,
        }

        if workflow_session_id:
            filters["session_id"] = workflow_session_id
        if task_id:
            filters["task_id"] = task_id

        workflow_runtimes = self.get_all_by_fields(filters=filters)

        if not workflow_runtimes:
            return []
        memory = []
        for workflow_runtime in workflow_runtimes:
            memory.append(workflow_runtime.result)
        return memory

    def get_workflow_resume_inputs(
        self,
        account_id: str,
        app_id: str,
        task_id: str,
    ) -> list:
        """get original inputs to resume the task"""
        filters = {
            "account_id": account_id,
            "app_id": app_id,
            "task_id": task_id,
        }
        workflow_runtimes = self.get_all_by_fields(filters=filters)

        return [
            workflow_runtime.inputs for workflow_runtime in workflow_runtimes
        ]

    def get_workflow_init_parameters(
        self,
        workflow_config: dict,
    ) -> list:
        """Get workflow init parameters."""
        parameters = []

        for node in workflow_config["workflow"]["graph"]["nodes"]:
            if node["type"] != "Start":
                continue
            output_params = node["config"]["output_params"]
            if output_params:
                for output_param in output_params:
                    parameters.append(
                        {
                            "key": output_param["key"],
                            "desc": output_param["desc"],
                            "type": output_param["type"],
                            "source": "user",
                            "required": True,
                        },
                    )
        parameters.append(
            {
                "key": "query",
                "desc": "用户问句",
                "type": "String",
                "source": "sys",
                "required": False,
            },
        )
        return parameters
