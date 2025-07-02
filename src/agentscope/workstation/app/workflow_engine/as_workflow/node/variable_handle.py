# -*- coding: utf-8 -*-
"""Module for variable assign node related functions."""
import time
from typing import Any, Generator

from .node import Node
from .utils import NodeType
from ...core.node_caches.workflow_var import WorkflowVariable, DataType


class VariableHandleNode(Node):
    """
    Variable assign node
    """

    node_type: str = NodeType.VARIABLE_HANDLE.value

    def _execute(self, **kwargs: Any) -> Generator:
        """execute"""
        start_time = int(time.time() * 1000)
        node_param = self.sys_args.get("node_param")
        type_ = node_param.get("type")
        if type_ == "template":
            node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
            yield [
                WorkflowVariable(
                    name="output",
                    content=node_param.get("template_content"),
                    source=self.node_id,
                    data_type=DataType.STRING,
                    node_type=self.node_type,
                    node_name=self.node_name,
                    input={"input": {}},
                    output={"output": node_param.get("template_content")},
                    output_type="json",
                    node_exec_time=node_exec_time,
                ),
            ]
        elif type_ == "json":
            json_params = node_param.get("json_params", [])
            node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
            output_var = []
            for item in json_params:
                output_var.append(
                    WorkflowVariable(
                        name=item["key"],
                        content=f'{item["value"]}',
                        source=self.node_id,
                        # data_type=item["type"],
                        data_type=DataType.STRING,
                        input={"input": {}},
                        output={
                            param["key"]: param["value"]
                            for param in json_params
                        },
                        output_type="json",
                        node_type=self.node_type,
                        node_name=self.node_name,
                        node_exec_time=node_exec_time,
                    ),
                )
            yield output_var
        elif type_ == "group":
            group_strategy = self.params.get("group_strategy", "firstNotNull")
            assert group_strategy in [
                "firstNotNull",
                "lastNotNull",
            ], (
                f"group_strategy must be firstNotNull or lastNotNull, "
                f"get {group_strategy}"
            )
            groups = node_param.get("groups", [])
            output = {}
            output_var = []
            for group in groups:
                group_name = group["group_name"]
                variables = [item["value"] for item in group["variables"]]
                variable = None
                if group_strategy == "firstNotNull":
                    variable = next((item for item in variables if item), None)
                    output[group_name] = variable
                elif group_strategy == "lastNotNull":
                    variable = next(
                        (item for item in reversed(variables) if item),
                        None,
                    )
                    output[group_name] = variable
                node_exec_time = (
                    str(int(time.time() * 1000) - start_time) + "ms"
                )
                output_var.append(
                    WorkflowVariable(
                        name=group_name,
                        content=variable,
                        source=self.node_id,
                        data_type=DataType.STRING,
                        input={"input": {}},
                        output=output,
                        output_type="json",
                        node_type=self.node_type,
                        node_name=self.node_name,
                        node_exec_time=node_exec_time,
                    ),
                )
            yield output_var
        else:
            raise ValueError(f"Unsupported type: {type}")
