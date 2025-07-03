# -*- coding: utf-8 -*-
"""Module for variable assign node related functions."""
import time
from typing import Any, Generator

from .node import Node
from .utils import NodeType
from ...core.node_caches.workflow_var import WorkflowVariable, DataType


class SessionParamsNode(Node):
    """
    Variable assign node
    """

    node_type: str = NodeType.SESSION_PARAMS.value

    def _execute(self, **kwargs: Any) -> Generator:
        """execute"""
        start_time = int(time.time() * 1000)
        variable_config = self.sys_args["variable_config"]
        session_params = variable_config["session_params"]

        node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
        yield [
            WorkflowVariable(
                name=param["key"],
                content=param["default_value"],
                source=self.node_id,
                data_type=DataType.STRING,
                input=None,
                node_type=self.node_type,
                output=param["default_value"],
                node_name=self.node_name,
                node_exec_time=node_exec_time,
            )
            for param in session_params
        ]
