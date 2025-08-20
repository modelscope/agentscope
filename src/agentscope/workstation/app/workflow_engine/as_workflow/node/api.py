# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches, too-many-statements
"""Module for API node related functions."""
import json
import time
from typing import Dict, Any, Generator

from .node import Node
from .utils import NodeType

from .common.make_request import make_request, AuthTypeEnum, BearerAuth
from ..utils.misc import get_module_source_content
from ...core.node_caches.workflow_var import WorkflowVariable, DataType
from ...core.utils.misc import format_output


class APINode(Node):
    """Class for API node related functions."""

    node_type: str = NodeType.API.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        node_param = self.sys_args["node_param"]
        authorization = node_param.get("authorization", {})
        auth_type = authorization.get("auth_type")
        if auth_type == AuthTypeEnum.BASIC_AUTH.value:
            auth_config = authorization["auth_config"]
            auth = (
                auth_config["username"],
                auth_config["password"],
            )
        elif auth_type == AuthTypeEnum.BEARER_AUTH.value:
            auth_config = authorization["auth_config"]
            auth = BearerAuth(auth_config["value"])
        else:
            auth = None

        timeout = node_param.get("timeout", {})
        timeout_config = {
            "connect": timeout.get("connect"),
            "read": timeout.get("read"),
            "write": timeout.get("write"),
        }

        retry_config = node_param.get("retry_config", {})
        if retry_config.get("retry_enabled"):
            max_retries = retry_config.get("max_retries")
            retry_delay = retry_config.get("retry_interval")
        else:
            max_retries = 1
            retry_delay = 0

        try_catch_config = node_param.get("try_catch_config", {})
        strategy = try_catch_config.get("strategy", "noop")

        headers = {
            item["key"]: item["value"] for item in node_param["headers"]
        }
        params = {item["key"]: item["value"] for item in node_param["params"]}
        body = node_param["body"]
        body_type = body["type"]
        if body_type is None:
            body_data = None
        elif body_type == "form-data":
            body_data = {
                item["key"]: item["value"]
                for item in body["data"]
                if "key" in item and "value" in item
            }
            if body_data:
                body_type = "data"
            else:
                body_type = "none"
                body_data = ""
        else:
            body_data = body["data"]

        output_type = self.sys_args["output_params"][0].get("type", "String")
        output_type_mapping = {
            "String": DataType.STRING,
            "Object": DataType.OBJECT,
        }
        assert output_type in output_type_mapping, "Invalid output type."

        try:
            response = make_request(
                url=node_param["url"],
                method=node_param.get("method", "post"),
                auth=auth,
                headers=headers,
                params=params,
                body_type=body_type,
                body=body_data,
                timeout_config=timeout_config,
                max_retries=max_retries,
                retry_delay=retry_delay,
            )
            if output_type == "Object":
                response = json.loads(response)
            node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
            yield [
                WorkflowVariable(
                    name="output",
                    content=response,
                    source=self.node_id,
                    data_type=output_type_mapping[output_type],
                    input=self.sys_args.get("input_params"),
                    output=response,
                    output_type=output_type,
                    node_type=self.node_type,
                    node_name=self.node_name,
                    node_exec_time=node_exec_time,
                ),
            ]
        except Exception as e:
            if strategy == "noop":
                raise e
            if strategy == "defaultValue":
                response = {
                    item["key"]: self.build_var_str(item)
                    for item in try_catch_config.get("default_values")
                }
                node_exec_time = (
                    str(int(time.time() * 1000) - start_time) + "ms"
                )
                output_var = []
                for key, value in response.items():
                    output_var.append(
                        WorkflowVariable(
                            name=key,
                            content=value,
                            source=self.node_id,
                            data_type=DataType.STRING,
                            input=self.sys_args.get("input_params"),
                            output=response,
                            output_type="json",
                            node_type=self.node_type,
                            node_name=self.node_name,
                            node_exec_time=node_exec_time,
                            try_catch={
                                "happened": True,
                                "strategy": "defaultValue",
                            },
                        ),
                    )
                yield output_var
            elif strategy == "failBranch":
                targets = []
                for source, adjacency in kwargs["graph"].adj.items():
                    if source != self.node_id:
                        continue
                    for target, edges in adjacency.items():
                        for _, data in edges.items():
                            source_handle = self.node_id + "_fail"
                            if data.get("source_handle") != source_handle:
                                continue
                            target = data.get("target")
                            targets.append(target)
                node_exec_time = (
                    str(int(time.time() * 1000) - start_time) + "ms"
                )
                yield [
                    WorkflowVariable(
                        name="output",
                        content=format_output(e),
                        source=self.node_id,
                        targets=targets,
                        data_type=DataType.STRING,
                        input=self.sys_args.get("input_params"),
                        node_type=self.node_type,
                        node_name=self.node_name,
                        node_exec_time=node_exec_time,
                        output=format_output(e),
                        output_type="text",
                        try_catch={
                            "happened": True,
                            "strategy": "failBranch",
                        },
                    ),
                ]
            else:
                raise ValueError(
                    f"Invalid try_catch_config strategy: {strategy}",
                ) from e

    def _mock_execute(self, **kwargs: Any) -> Generator:
        yield [
            WorkflowVariable(
                name="output",
                content=f"This is a mock result of {self.node_type} node.",
                source=self.node_id,
                data_type=DataType.STRING,
                input=self.sys_args.get("input_params"),
                node_type=self.node_type,
                node_name=self.node_name,
            ),
        ]

    def compile(self) -> Dict[str, Any]:
        tool_str = self.build_graph_var_str("post_tool")
        node_param = self.sys_args["node_param"]
        authorization = node_param.get("authorization", {})
        auth_type = authorization.get("authType")
        if auth_type == AuthTypeEnum.BASIC_AUTH.value:
            auth_config = authorization["authConfig"]
            auth = f"""(
                {auth_config["username"]},
                {auth_config["password"]},
            )"""
        elif auth_type == AuthTypeEnum.BEARER_AUTH.value:
            auth_config = authorization["authConfig"]
            auth = f"""BearerAuth('{auth_config["token"]}')"""
        else:
            auth = None

        timeout = node_param.get("timeout", {})
        timeout_config = {
            "connect": timeout.get("connect"),
            "read": timeout.get("read"),
            "write": timeout.get("write"),
        }

        retry_config = node_param.get("retryConfig", {})
        if retry_config.get("enabled"):
            max_retries = retry_config.get("maxRetries")
            retry_delay = retry_config.get("retryDelay")
        else:
            max_retries = 1
            retry_delay = 0

        try_catch_config = node_param.get("tryCatchConfig", {})
        strategy = try_catch_config.get("strategy", "noop")

        headers = {
            item["key"]: item["value"] for item in node_param["headers"]
        }
        params = {item["key"]: item["value"] for item in node_param["params"]}
        body = node_param["body"]
        body_type = body["type"]
        if body_type is None:
            body_data = None
        elif body_type == "form-data":
            body_data = {
                item["key"]: item["value"]
                for item in body["data"]
                if "key" in item and "value" in item
            }
            if body_data:
                body_type = "data"
            else:
                body_type = "none"
                body_data = ""
        else:
            body_data = body["data"]

        init_str = f"""
{tool_str} = partial(
    make_request,
    url="{node_param['url']}",
    method="{node_param.get('method', "post")}",
    auth={auth},
    headers={headers},
    params={params},
    body_type="{body_type}",
    body=\"\"\"{body_data}\"\"\",
    timeout_config={timeout_config},
    max_retries={max_retries},
    retry_delay={retry_delay},
)
"""
        # TODO: add retry and tryCatchConfig
        if strategy == "noop":
            execs_str = f"""{self.build_graph_var_str("result")} = {tool_str}()
{self.build_node_output_str(self.build_graph_var_str("result"), str)}
"""
        elif strategy == "defaultValue":
            response = {
                item["key"]: self.build_var_str(item)
                for item in try_catch_config.get("defaultValue")
            }
            execs_str = f"""try:
    {self.build_graph_var_str("result")} = {tool_str}()
except Exception as e:
    {self.build_graph_var_str("result")} = {response}
"""
        else:
            # TODO: fail branch
            pass

        current_module = __name__.rsplit(".", 1)[0]

        make_request_module_name = f"{current_module}.common.make_request"
        make_request_contents = get_module_source_content(
            make_request_module_name,
        )

        return {
            "imports": ["from functools import partial"],
            "inits": [init_str],
            "execs": [execs_str],
            "increase_indent": False,
            "dependency": [
                {
                    "name": "make_request",
                    "path": ".",
                    "script": make_request_contents,
                },
            ],
        }
