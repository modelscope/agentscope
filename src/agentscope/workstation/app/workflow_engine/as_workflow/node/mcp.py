# -*- coding: utf-8 -*-
"""mcp node"""
import json
import time
from typing import Dict, Any, Generator
from sqlmodel import select, Session
from app.models.engine import engine
from app.models.mcp import MCP
from agentscope.service.mcp_manager import MCPSessionHandler, sync_exec
from .node import Node
from .utils import NodeType
from ...core.node_caches.workflow_var import WorkflowVariable, DataType


class MCPNode(Node):
    """Class for MCP node related functions."""

    node_type: str = NodeType.MCP.value

    def _execute(self, **kwargs: Any) -> Generator:
        """Execute MCP node.

        Args:
            kwargs: Execution arguments

        Yields:
            Generator: WorkflowVariable containing the result
        """
        start_time = int(time.time() * 1000)
        node_param = self.sys_args["node_param"]
        input_params = self.sys_args["input_params"]
        params = {param["key"]: param["value"] for param in input_params}
        tool_name = node_param["tool_name"]

        output_type = self.sys_args["output_params"][0].get("type", "String")
        output_type_mapping = {
            "String": DataType.STRING,
            "Object": DataType.OBJECT,
        }
        assert output_type in output_type_mapping, "Invalid output type."

        with Session(engine) as session:
            query = select(MCP).where(
                MCP.server_code == node_param["server_code"],
            )
            mcp = session.exec(query).first()
            if mcp:
                config = json.loads(mcp.deploy_config)
                local_configs = json.loads(config["install_config"])
        new_servers = [
            MCPSessionHandler(name, config)
            for name, config in local_configs["mcpServers"].items()
        ]
        for server in new_servers:
            tool_names = [tool.name for tool in sync_exec(server.list_tools)]
            if tool_name in tool_names:
                res = sync_exec(
                    server.execute_tool,
                    tool_name,
                    **params,
                )
                node_exec_time = (
                    str(int(time.time() * 1000) - start_time) + "ms"
                )
                yield [
                    WorkflowVariable(
                        name="output",
                        content=json.dumps(res, ensure_ascii=False, indent=4),
                        source=self.node_id,
                        data_type=output_type_mapping[output_type],
                        input=params,
                        node_type=self.node_type,
                        node_name=self.node_name,
                        output={"output": res},
                        output_type="json",
                        node_exec_time=node_exec_time,
                    ),
                ]
                break

    def _mock_execute(self, **kwargs: Any) -> Generator:
        yield [
            WorkflowVariable(
                name="result",
                content=f"This is a mock result of {self.node_type} node.",
                source=self.node_id,
                data_type=DataType.STRING,
            ),
        ]

    def compile(self) -> Dict[str, Any]:
        node_param = self.sys_args["nodeParam"]
        input_params = self.sys_args["inputParams"]

        params = {item["key"]: item["value"] for item in input_params}
        import_list = [
            "from agentscope.service.mcp_manager import MCPSessionHandler",
            "from agentscope.service.mcp_manager import sync_exec",
        ]
        url = "https://mcp.amap.com/sse?key="
        local_configs = {
            "mcpServers": {
                "amap-amap-sse": {
                    "url": url,
                },
            },
        }
        with Session(engine) as session:
            query = select(MCP).where(
                MCP.server_code == node_param["serverCode"],
            )
            mcp = session.exec(query).first()
            if mcp:
                config = json.loads(mcp.deploy_config)
                local_configs = json.loads(config["install_config"])

        # TODO get mcp config from system variable
        init_str = f"""local_configs = {local_configs}
        new_servers = [
            MCPSessionHandler(name, config)
            for name, config in local_configs["mcpServers"].items()
        ]
        for server in new_servers:
            tool_name = [tool.name for tool in sync_exec(server.list_tools)]
            if "{node_param["toolName"]}" in tool_name:
                result = sync_exec(
                    server.execute_tool,
                    "{node_param["toolName"]}",
                    **{params},
                )
                yield result
                break
"""
        node_param["textTemplate"] = {
            "result": ["res"],
            "isError": False,
        }

        return {
            "imports": import_list,
            "inits": [init_str],
            "execs": [],
            "increase_indent": False,
        }
