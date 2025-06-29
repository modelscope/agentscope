# -*- coding: utf-8 -*-
"""Module for variable assign node related functions."""
import time
from typing import Any, Generator

from .node import Node
from .utils import NodeType
from ...core.node_caches.workflow_var import WorkflowVariable, DataType


class VariableAssignNode(Node):
    """
    Variable assign node
    """

    node_type: str = NodeType.VARIABLE_ASSIGN.value

    def _execute(self, **kwargs: Any) -> Generator:
        """execute"""
        start_time = int(time.time() * 1000)
        node_param_form = self.node_kwargs.get("config", {}).get(
            "node_param",
        )
        inputs_form = node_param_form.get("inputs", [])

        node_param_value = self.sys_args.get("node_param")
        inputs_value = node_param_value.get("inputs", [])

        node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"

        res = []
        for input_form in inputs_form:
            variable_assign_id = input_form.get("id")
            left = input_form.get("left").get("value")
            name = left[2:-1]
            for input_value in inputs_value:
                if input_value.get("id") == variable_assign_id:
                    output_input = {
                        "left": input_value.get("left").get("value"),
                        "right": input_value.get("right").get("value"),
                    }

                    content = input_value.get("right").get("value")
                    res.append(
                        WorkflowVariable(
                            name=name,
                            content=content,
                            source=None,
                            data_type=DataType.STRING,
                            input=output_input,
                            output={
                                "result": "Assignment successful",
                            },
                            node_type=self.node_type,
                            node_name=self.node_name,
                            node_exec_time=node_exec_time,
                        ),
                    )
                    break
        yield res
