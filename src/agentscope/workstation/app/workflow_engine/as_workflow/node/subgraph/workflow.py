# -*- coding: utf-8 -*-
"""Module for Iterator node related functions."""
import time

# mypy: disable-error-code=arg-type
# pylint: disable=too-many-branches, too-many-statements
from typing import Dict, Any, Generator

from ..node import Node
from ..utils import NodeType
from ...node_cache import AgentscopeNodeCacheHandler
from ....core.node_caches.workflow_var import WorkflowVariable, DataType
from ....core.utils.misc import replace_placeholders


class WorkflowNode(Node):
    """
    Represents a node containing a workflow.
    """

    node_type: str = NodeType.WORKFLOW.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        from ...interface.run import exec_runner

        global_cache = kwargs.get("global_cache", {})
        # Use raw config to avoid var being replaced
        subgraph_config = self._build_dsl_config(
            self.node_kwargs["config"]["node_param"]["block"],
        )
        node_instance = kwargs.get("graph").node_instance

        for _, messages in exec_runner(
            params=self.params,
            dsl_config=subgraph_config,
            request_id=self.request_id,
            node_instance=node_instance,
            disable_pause=True,
            inter_results=global_cache,
            subgraph_mode=True,
        ):
            inter_results = messages[-1]["status"]["inter_results"]
            format_map = AgentscopeNodeCacheHandler.retrieve_node_input(
                self.node_id,
                inter_results,
            )

            subgraph_var = WorkflowVariable(
                name="subgraph",
                content=inter_results,
                source=self.node_id,
                data_type=DataType.OBJECT,
            )
            output_var = [subgraph_var]
            yield output_var

        node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
        # We do not use `sys_args` here since the placeholder is
        # replaced with None value
        for element in self.node_kwargs["config"].get("outputParams"):
            output_var.append(
                WorkflowVariable(
                    name=element["key"],
                    content=replace_placeholders(
                        element["value"],
                        format_map,
                    ),
                    source=self.node_id,
                    data_type=element["type"],
                    input=self.sys_args.get("input_params"),
                    node_type=self.node_type,
                    node_name=self.node_name,
                    node_exec_time=node_exec_time,
                ),
            )
        yield output_var

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

    def _build_dsl_config(self, subgraph_config: Dict) -> Dict:
        """
        Constructs a compile request for the given subgraph configuration.

        Args:
            subgraph_config: A dictionary representing the subgraph
                configuration.

        Returns:
            A dictionary formatted as a compile request compatible with
            the compiler interface.
        """
        return {
            "workflow": {
                "graph": subgraph_config,
            },
        }

    def _build_params(self, subgraph_config: Dict) -> Dict:
        """
        Constructs a compile request for the given subgraph configuration.

        Args:
            subgraph_config: A dictionary representing the subgraph
                configuration.

        Returns:
            A dictionary formatted as a compile request compatible with
            the compiler interface.
        """
        return {
            "workflow": {
                "graph": subgraph_config,
            },
        }
