# -*- coding: utf-8 -*-
"""Module for dummy node related functions."""
import json
import time
from typing import Dict, Any, Generator

from .node import Node
from .utils import NodeType
from ..constant import VAR_INIT_PLACEHOLDER_SIGN
from ...core.node_caches.workflow_var import WorkflowVariable, DataType


class StartNode(Node):
    """
    A node that initializes the pipeline, defining input parameters for the
    workflow with type annotations.
    """

    node_type: str = NodeType.START.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        output_var = []
        element = self.glb_custom_args.get("inputs", {})
        node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
        for k1, v1 in element.items():
            if v1:
                for k2, v2 in v1.items():
                    output_var.append(
                        WorkflowVariable(
                            name=k2,
                            content=v2,
                            source=self.node_id,
                            data_type=DataType.STRING,
                            input=element,
                            output=element,
                            output_type="json",
                            node_type=self.node_type,
                            node_name=self.node_name,
                            node_exec_time=node_exec_time,
                        ),
                    )
        if not output_var:
            output_var.append(
                WorkflowVariable(
                    name="output",
                    content="Success",
                    source=self.node_id,
                    data_type=DataType.STRING,
                    input=element,
                    node_type=self.node_type,
                    node_name=self.node_name,
                    node_exec_time=node_exec_time,
                ),
            )
        yield output_var

    def _mock_execute(self, *args: Any, **kwargs: Any) -> Generator:
        yield from self._execute(**kwargs)

    def compile(self) -> Dict[str, Any]:
        raw_args = [
            {
                "key": "${sys.query}",
                "type": "String",
            },
            {
                "key": "${sys.historyList}",
                "type": "Array<String>",
            },
            {
                "key": "${sys.imageList}",
                "type": "Array<String>",
            },
        ]

        imports_list = ["from typing import Generator"]
        arg_str = ""
        for item in raw_args + self.sys_args["outputParams"]:
            if item not in raw_args:
                var = self.build_graph_var_str(item["key"])
            else:
                var = item["key"]
            if item["type"] == "String":
                arg_str += f"{var}: str = None, "
            elif item["type"] == "Number":
                imports_list.append("from numbers import Number")
                arg_str += f"{var}: Number = None, "
            elif item["type"] == "Boolean":
                arg_str += f"{var}: bool = None, "
            elif item["type"] == "Object":
                arg_str += f"{var}: dict = None, "
            elif "Array" in item["type"]:
                arg_str += f"{var}: list = None, "
            else:
                arg_str += f"{var} = None, "

        return {
            "imports": imports_list,
            "inits": [],
            "execs": [
                f"def agentscope_pipeline({arg_str}) -> Generator:\n    "
                f"{VAR_INIT_PLACEHOLDER_SIGN}",
            ],
            "increase_indent": True,
        }


class WorkflowStartNode(Node):
    """
    A node that marks the beginning of a workflow block in a workflow.
    """

    node_type: str = NodeType.WORKFLOW_START.value


class WorkflowEndNode(Node):
    """
    A node that marks the end of a workflow block in a workflow.
    """

    node_type: str = NodeType.WORKFLOW_END.value


class IteratorStartNode(Node):
    """
    A node that marks the beginning of an iteration block in a workflow.
    """

    node_type: str = NodeType.ITERATOR_START.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        yield [
            WorkflowVariable(
                name="output",
                content="Success",
                source=self.node_id,
                data_type=DataType.STRING,
                input={"result": "success"},
                output={"result": "success"},
                output_type="json",
                node_type=self.node_type,
                node_name=self.node_name,
                is_batch=False,
                batches=[],
                is_multi_branch=False,
                node_exec_time=str(int(time.time() * 1000) - start_time)
                + "ms",
            ),
        ]


class IteratorEndNode(Node):
    """
    A node that marks the end of an iteration block in a workflow.
    """

    node_type: str = NodeType.ITERATOR_END.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        yield [
            WorkflowVariable(
                name="output",
                content="Success",
                source=self.node_id,
                data_type=DataType.STRING,
                input={"result": "success"},
                output={"result": "success"},
                output_type="json",
                node_type=self.node_type,
                node_name=self.node_name,
                is_batch=False,
                batches=[],
                is_multi_branch=False,
                node_exec_time=str(int(time.time() * 1000) - start_time)
                + "ms",
            ),
        ]


class ParallelStartNode(Node):
    """
    A node that marks the beginning of a parallel block in a workflow.
    """

    node_type: str = NodeType.PARALLEL_START.value

    def _execute(self, *args: Any, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        yield [
            WorkflowVariable(
                name="output",
                content="Success",
                source=self.node_id,
                data_type=DataType.STRING,
                input={"result": "success"},
                output={"result": "success"},
                output_type="json",
                node_type=self.node_type,
                node_name=self.node_name,
                is_batch=False,
                batches=[],
                is_multi_branch=False,
                node_exec_time=str(int(time.time() * 1000) - start_time)
                + "ms",
            ),
        ]


class ParallelEndNode(Node):
    """
    A node that marks the end of a parallel block in a workflow.
    """

    node_type: str = NodeType.PARALLEL_END.value

    def _execute(self, *args: Any, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        yield [
            WorkflowVariable(
                name="output",
                content="Success",
                source=self.node_id,
                data_type=DataType.STRING,
                input={"result": "success"},
                output={"result": "success"},
                output_type="json",
                node_type=self.node_type,
                node_name=self.node_name,
                is_batch=False,
                batches=[],
                is_multi_branch=False,
                node_exec_time=str(int(time.time() * 1000) - start_time)
                + "ms",
            ),
        ]


class VariableNode(Node):
    """
    A node that assigns values to variables based on input configurations.
    """

    node_type: str = NodeType.VARIABLE.value

    def _execute(self, **kwargs: Any) -> Generator:
        yield [
            WorkflowVariable(
                name="output",
                content="Success",
                source=self.node_id,
                data_type=DataType.STRING,
                input=self.sys_args.get("input_params"),
                node_type=self.node_type,
                node_name=self.node_name,
            ),
        ]

    def compile(self) -> Dict[str, Any]:
        """
        Compiles the variable node into an execution block that initializes
        variables.
        """
        exec_str = ""
        node_param = self.sys_args["node_param"]
        for x in node_param["inputs"]:
            exec_str += f"{x['left']['value']} = {x['right']['value']}\n"

        return {
            "imports": [],
            "inits": [],
            "execs": [exec_str],
        }


class EndNode(Node):
    """
    A node that finalizes the pipeline, producing output in text or JSON
    format.
    """

    node_type: str = NodeType.END.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        node_param = self.sys_args["node_param"]
        if node_param["output_type"] == "text":
            node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
            yield [
                WorkflowVariable(
                    name="output",
                    content=f'{self.sys_args["node_param"]["text_template"]}',
                    source=self.node_id,
                    data_type=DataType.STRING,
                    # input=self.sys_args.get("input_params"),
                    output=f'{self.sys_args["node_param"]["text_template"]}',
                    node_type=self.node_type,
                    node_name=self.node_name,
                    node_exec_time=node_exec_time,
                    output_type="text",
                ),
            ]
        elif node_param["output_type"] == "json":
            result = {}
            output_var = []
            for element in node_param.get("json_params", []):
                result[element["key"]] = element["value"]
            node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
            for element in node_param.get("json_params", []):
                output_var.append(
                    WorkflowVariable(
                        name=element["key"],
                        content=element["value"],
                        source=self.node_id,
                        data_type=element["type"],
                        input=self.sys_args.get("input_params"),
                        output=result,
                        node_type=self.node_type,
                        node_name=self.node_name,
                        node_exec_time=node_exec_time,
                        output_type="json",
                    ),
                )
            yield output_var

        else:
            raise ValueError("Invalid output type")

    def _mock_execute(self, *args: Any, **kwargs: Any) -> Generator:
        yield from self._execute(**kwargs)

    def compile(self) -> Dict[str, Any]:
        """
        Compiles the end node into an execution block that outputs the result
        according to the specified output type.
        """
        node_param = self.sys_args["node_param"]
        if node_param["outputType"] == "text":
            content = node_param["textTemplate"]
            exec_str = f"""
{self.build_graph_var_str("result")} = \
\"\"\"{self._add_prefix_to_lines(content)}\"\"\"
{self.build_node_output_str(self.build_graph_var_str("result"), str)}
"""
        elif node_param["outputType"] == "json":
            content = {
                item["key"]: item["value"] for item in node_param["jsonParams"]
            }
            exec_str = f"""
{self.build_graph_var_str("result")} = {content}
{self.build_node_output_str(self.build_graph_var_str("result"), str)}
"""

        return {
            "imports": [],
            "inits": [],
            "execs": [exec_str],
        }


class TextConverterNode(Node):
    """
    A node that converts text content into a specified format, such as JSON.
    """

    node_type: str = NodeType.TEXT_CONVERTER.value

    def _execute(self, **kwargs: Any) -> Generator:
        node_param = self.sys_args["node_param"]
        if node_param["type"] == "template":
            yield [
                WorkflowVariable(
                    name="output",
                    content=self.sys_args["node_param"]["templateContent"],
                    source=self.node_id,
                    data_type=DataType.STRING,
                    input=self.sys_args.get("input_params"),
                    node_type=self.node_type,
                    node_name=self.node_name,
                ),
            ]
        elif node_param["type"] == "json":
            result = {}
            for element in node_param.get("jsonParams", []):
                result[element["key"]] = element["value"]
            yield [
                WorkflowVariable(
                    name="output",
                    content=result,
                    source=self.node_id,
                    data_type=DataType.OBJECT,
                    input=self.sys_args.get("input_params"),
                    node_type=self.node_type,
                    node_name=self.node_name,
                ),
            ]
        else:
            raise ValueError("Invalid output type")

    def compile(self) -> Dict[str, Any]:
        """
        Compiles the text converter node into an execution block that formats
        text content.
        """
        node_param = self.sys_args["node_param"]

        if node_param["type"] == "json":
            content = {
                item["key"]: item["value"] for item in node_param["jsonParams"]
            }
        else:
            content = node_param["templateContent"]
        execs_str = f"""
{self.build_graph_var_str("result")} = \
\"\"\"{self._add_prefix_to_lines(content)}\"\"\"
{self.build_node_output_str(self.build_graph_var_str("result"), str)}
"""
        return {
            "imports": [],
            "inits": [],
            "execs": [execs_str],
        }


class InputNode(Node):
    """
    A node that represents an input to the workflow.
    """

    node_type: str = NodeType.INPUT.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        output_params = self.sys_args.get("output_params", [])
        input_params = self.sys_args.get("input_params", [])
        if not input_params:
            yield [
                WorkflowVariable(
                    name="output",
                    content=output_params,
                    source=self.node_id,
                    data_type=DataType.ARRAY_ANY,
                    output=output_params,
                    output_type="json",
                    input=output_params,
                    node_type=self.node_type,
                    node_name=self.node_name,
                    node_exec_time=str(int(time.time() * 1000) - start_time)
                    + "ms",
                ),
            ]
        else:
            output = {param["key"]: param["value"] for param in input_params}
            output_var = []
            for param in input_params:
                output_var.append(
                    WorkflowVariable(
                        name=param["key"],
                        content=param["value"],
                        source=self.node_id,
                        data_type=DataType.STRING,
                        input=output_params,
                        output=output,
                        output_type="json",
                        node_type=self.node_type,
                        node_name=self.node_name,
                        node_exec_time=str(
                            int(time.time() * 1000) - start_time,
                        )
                        + "ms",
                    ),
                )
            yield output_var


class OutputNode(Node):
    """
    A node that represents an output from the workflow.
    """

    node_type: str = NodeType.OUTPUT.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        node_param = self.sys_args.get("node_param", {})
        yield [
            WorkflowVariable(
                name="output",
                content=node_param.get("output", ""),
                output=node_param.get("output", ""),
                output_type="text",
                source=self.node_id,
                data_type=DataType.STRING,
                node_type=self.node_type,
                node_name=self.node_name,
                node_exec_time=str(int(time.time() * 1000) - start_time)
                + "ms",
            ),
        ]
