# -*- coding: utf-8 -*-
"""Module for code node related functions."""
# pylint: disable=too-many-branches, too-many-statements,
# pylint: disable=too-many-nested-blocks
import re
import time
from typing import Dict, Any, Generator

import json5
from loguru import logger

from sandboxai import Sandbox

from .node import Node
from .utils import NodeType
from ..constant import DO_NOT_INDENT_SIGN
from ...core.utils.misc import find_value_placeholders, format_output
from ...core.constant import PATTERN
from ...core.node_caches.workflow_var import WorkflowVariable, DataType


class ScriptNode(Node):
    """
    Represents a script node capable of executing code in supported script
    types.

    Handles compilation of scripts by generating code execution logic.
    """

    node_type: str = NodeType.SCRIPT.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        node_param = self.sys_args["node_param"]
        script_type = node_param["script_type"]
        script_str = node_param["script_content"]
        input_params = {
            item["key"]: self.build_var_str(item)
            for item in self.sys_args["input_params"]
        }
        input_params_str = format_output(input_params)

        input_dict = {"input": input_params}

        output_params = self.sys_args.get("output_params")
        retry_config = node_param.get("retry_config", {})
        if retry_config.get("retry_enabled"):
            max_retries = retry_config.get("max_retries")
            retry_delay = retry_config.get("retry_interval")
        else:
            max_retries = 1
            retry_delay = 0

        try_catch_config = node_param.get("try_catch_config", {})
        strategy = try_catch_config.get("strategy", "noop")

        if find_value_placeholders(input_params_str, pattern=PATTERN):
            input_params_str = f"params = {{{input_params_str}}}"
        else:
            input_params_str = f"params = {input_params_str}"

        if script_type == "python":
            script_str = script_str.replace("def main():", "def main(params):")

            code_str = f"""{input_params_str}
{script_str}
print(main(params))
"""
        elif script_type == "javascript":
            code_str = f"""{input_params_str}
{script_str}
main();
"""
        else:
            raise ValueError(f"script type {script_type} is not supported")

        attempts = 0
        error = None
        while attempts < max_retries:
            try:
                if script_type == "python":

                    def clean_ansi(text: str) -> str:
                        ansi_escape = re.compile(
                            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])",
                        )
                        return ansi_escape.sub("", text)

                    with Sandbox(embedded=True) as box:
                        # result = json5.loads(
                        #     box.run_ipython_cell(code_str).output,
                        # )
                        output = box.run_ipython_cell(code_str).output
                        cleaned_output = clean_ansi(output)
                        json_pattern = r"({.*})"
                        json_match = re.search(json_pattern, cleaned_output)
                        if json_match:
                            try:
                                result = json5.loads(json_match.group(0))
                            except ValueError as e:
                                logger.error(f"Failed to parse JSON: {e}")

                        else:
                            logger.info("No JSON found in output")
                elif script_type == "javascript":
                    # TODO: user sandbox
                    import pythonmonkey as pm

                    result = pm.eval(code_str)

                node_exec_time = (
                    str(
                        int(time.time() * 1000) - start_time,
                    )
                    + "ms"
                )
                output_var = []
                output = {}
                for output_param in output_params:
                    if output_param["key"] in result:
                        output[output_param["key"]] = result.get(
                            output_param["key"],
                        )
                        output_var.append(
                            WorkflowVariable(
                                name=output_param["key"],
                                content=result.get(output_param["key"]),
                                source=self.node_id,
                                data_type=output_param["type"],
                                input=input_dict,
                                node_type=self.node_type,
                                node_name=self.node_name,
                                node_exec_time=node_exec_time,
                                output=output,
                                output_type="json",
                            ),
                        )
                    yield output_var
                break
            except Exception as e:
                error = e
                self.logger.query_error(
                    request_id=self.request_id,
                    message=f"Failed to execute script: {str(e)}",
                )
                attempts += 1
                time.sleep(retry_delay / 1000)

        if attempts >= max_retries:
            if strategy == "noop":
                raise ValueError(str(error))
            if strategy == "defaultValue":
                output_var = []
                output = {
                    item["key"]: self.build_var_str(item)
                    for item in try_catch_config.get("default_values")
                }
                node_exec_time = (
                    str(int(time.time() * 1000) - start_time) + "ms"
                )

                for default_value in try_catch_config["default_values"]:
                    output_var.append(
                        WorkflowVariable(
                            name=default_value["key"],
                            content=default_value["value"],
                            source=self.node_id,
                            data_type=default_value["type"],
                            input=input_dict,
                            node_type=self.node_type,
                            node_name=self.node_name,
                            output_type="json",
                            output=output,
                            node_exec_time=node_exec_time,
                            try_catch={
                                "happened": True,
                                "strategy": "defaultValue",
                            },
                        ),
                    )
                yield output_var
            elif strategy == "failBranch":
                source_to_target_map = {}
                for _, adjacency in kwargs["graph"].adj.items():
                    for _, edges in adjacency.items():
                        for _, data in edges.items():
                            if data.get("source_handle"):
                                source_handle = data.get("source_handle")
                                target_handle = data.get("target_handle")
                                if source_handle not in source_to_target_map:
                                    source_to_target_map[source_handle] = []
                                source_to_target_map[source_handle].append(
                                    target_handle,
                                )

                targets = source_to_target_map.get(self.node_id + "_fail", [])

                node_exec_time = (
                    str(int(time.time() * 1000) - start_time) + "ms"
                )
                yield [
                    WorkflowVariable(
                        name="output",
                        content=format_output(error),
                        source=self.node_id,
                        targets=targets,
                        data_type=DataType.STRING,
                        input=input_dict,
                        node_type=self.node_type,
                        node_name=self.node_name,
                        node_exec_time=node_exec_time,
                        try_catch={
                            "happened": True,
                            "strategy": "failBranch",
                        },
                    ),
                ]
            else:
                raise ValueError(
                    f"Invalid try_catch_config strategy: {strategy}",
                )

    def _mock_execute(self, **kwargs: Any) -> Generator:
        yield from self._execute(**kwargs)

    def compile(self) -> Dict[str, Any]:
        """
        Compiles the script node into a structured dictionary containing
        imports, initializations, and execution logic for the script.

        Returns:
            A dictionary with sections for imports, inits, and execs.

        Raises:
            ValueError: If the script type is not supported.
            NotImplementedError: For script types not yet implemented.
        """
        node_param = self.sys_args["node_param"]
        script_type = node_param["scriptType"]
        script_str = node_param["scriptContent"]
        input_params = {
            item["key"]: self.build_var_str(item)
            for item in self.sys_args["input_params"]
        }
        input_params_str = format_output(input_params)
        if script_type == "python":
            imports_list = [
                "import json5",
                "from sandboxai import Sandbox",
            ]

            if find_value_placeholders(input_params_str, pattern=PATTERN):
                input_params_str = f"params = {{{input_params_str}}}"
            else:
                input_params_str = f"params = {input_params_str}"

            script_str = script_str.replace("def main():", "def main(params):")
            script_str = self._add_prefix_to_lines(
                script_str,
                prefix=DO_NOT_INDENT_SIGN,
            )
            execs_str = f"""
code_str = \"\"\"{input_params_str}\"\"\" + \
\"\"\"
{script_str}
{DO_NOT_INDENT_SIGN}print(main(params))\"\"\"
with Sandbox(embedded=True) as box:
    {self.build_graph_var_str("result")} = \
json5.loads(box.run_ipython_cell(code_str).output)["result"]
{self.build_node_output_str(self.build_graph_var_str("result"), str)}
"""
        elif script_type == "javascript":
            raise NotImplementedError
        else:
            raise ValueError(f"script type {script_type} is not supported")

        return {
            "imports": imports_list,
            "inits": [],
            "execs": [execs_str],
            "increase_indent": False,
        }
