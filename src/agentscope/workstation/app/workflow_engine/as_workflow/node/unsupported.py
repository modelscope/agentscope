# -*- coding: utf-8 -*-
"""Module for unsupported node related functions."""
from typing import Dict, Any, Optional, Generator

from .node import Node
from .utils import NodeType
from ...core.utils.misc import find_value_placeholders, format_output
from ...core.utils.error import ApiError
from ...core.constant import PATTERN


class UnsupportedNode(Node):
    """
    Represents an unsupported node type within the workflow engine.

    Provides functionality to compile a dummy representation
    suggesting manual implementation or substitution with supported nodes.
    """

    node_type = "unsupported"

    def _execute(self, **kwargs: Any) -> Generator:
        raise ApiError("Unsupported node type")

    def compile(self) -> Dict[str, Any]:
        """
        Compiles a dummy representation of the unsupported node.

        Returns:
            A dictionary with sections for imports, inits, and execs containing
            instructions for handling unsupported node types.
        """
        return self._build_dummy_compiled_dict(var_name="tool")

    def _build_dummy_compiled_dict(
        self,
        var_name: str,
        ref_url: Optional[str] = None,
        extra_comment: str = "",
    ) -> Dict[str, Any]:
        ref_url = ref_url or "https://doc.agentscope.io"
        comment = f"""
## Node type ###{self.node_kwargs.get("type", "unknown")}### is unsupported.
## Please use a replacement in AgentScope package or implement by yourself.
## {extra_comment}
## Reference: {ref_url}
## Node Parameters: {self.sys_args.get("node_param")}
## Example code:
"""

        var_str = self.build_graph_var_str(var_name)

        input_params = {
            item["key"]: self.build_var_str(item)
            for item in self.sys_args["input_params"]
        }

        input_params_str = format_output(input_params)

        if find_value_placeholders(input_params_str, pattern=PATTERN):
            input_params_str = f"params = {{{input_params_str}}}"
        else:
            input_params_str = f"params = {input_params_str}"

        exec_str = f"""
# {self.build_graph_var_str("param")} = {input_params_str}
# {self.build_graph_var_str("result")} = \
{var_str}(**{self.build_graph_var_str("param")})
"""
        return {
            "imports": [],
            "inits": [],
            "execs": [
                comment,
                exec_str,
            ],
            "increase_indent": False,
        }


class PluginNode(UnsupportedNode):
    """
    Represents a plugin node type, inheriting from UnsupportedNode.

    Provides specific compilation instructions for plugin nodes.
    """

    node_type: str = NodeType.PLUGIN.value

    def compile(self) -> Dict[str, Any]:
        """
        Compiles a representation of a plugin node.

        Returns:
            A dictionary with structured code snippets for plugin nodes.
        """
        var_name = (
            self.sys_args["node_param"].get(
                "toolName",
                "tool",
            )
            + "_tool"
        )
        ref_url = "https://doc.agentscope.io/build_tutorial/tool.html"
        return self._build_dummy_compiled_dict(
            var_name=var_name,
            ref_url=ref_url,
        )


class FCNode(UnsupportedNode):
    """
    Represents a Function Compute (FC) node type, inheriting from
    UnsupportedNode.

    Provides specific compilation instructions for FC nodes.
    """

    node_type: str = NodeType.FC.value

    def compile(self) -> Dict[str, Any]:
        """
        Compiles a representation of FC node.

        Returns:
            A dictionary with structured code snippets for FC nodes.
        """

        var_name = "fc_tool"
        ref_url = "https://www.aliyun.com/product/fc"
        return self._build_dummy_compiled_dict(
            var_name=var_name,
            ref_url=ref_url,
        )


class AppFlowNode(UnsupportedNode):
    """
    Represents an AppFlow node type, inheriting from UnsupportedNode.

    Provides specific compilation instructions for AppFlow nodes.
    """

    node_type: str = NodeType.APPFLOW.value

    def compile(self) -> Dict[str, Any]:
        """
        Compiles a representation of an AppFlow node.

        Returns:
            A dictionary with structured code snippets for AppFlow nodes.
        """
        var_name = "app_flow_tool"
        ref_url = "https://www.aliyun.com/product/computenest"
        return self._build_dummy_compiled_dict(
            var_name=var_name,
            ref_url=ref_url,
        )
