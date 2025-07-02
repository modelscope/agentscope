# -*- coding: utf-8 -*-
"""Module for variable assign node related functions."""
import json
import time
from typing import Any, Generator

from .node import Node
from .utils import NodeType
from ..utils.misc import get_model_instance
from ...core.node_caches.workflow_var import WorkflowVariable


SYS_PROMPT = (
    "You are a professional parameter extraction assistant. Your"
    "task is to accurately extract specified parameters from user input. "
    "Carefully analyze the input content to ensure the extracted parameters "
    "are accurate. If some parameters cannot be extracted, "
    'set "_is_completed" '
    'to false and provide the reason in "_reason".'
)


EXAMPLE_LIST = [
    {
        "input": "I want to travel to Beijing on March 15, 2024",
        "parameters_des": [
            "city:string:the city name:required",
            "date:string:the date with format year-month-day:required",
        ],
        "useful_info": "",
        "extracted_parameters": {
            "_is_completed": True,
            "_reason": "",
            "city": "Beijing",
            "date": "2024-03-15",
        },
    },
    {
        "input": "Help me book a flight to Shanghai",
        "useful_info": "",
        "parameters_des": [
            "city:string:the city name:required",
            "date:string:the date formatted with year-month-day:required",
        ],
        "extracted_parameters": {
            "_is_completed": False,
            "_reason": "Date information is missing",
            "city": "Shanghai",
        },
    },
    {
        "input": "Going to Hangzhou next Monday",
        "useful_info": "",
        "parameters_des": [
            "city:string:the city name:required",
            "date:string:the date formatted with year-month-day:required",
        ],
        "extracted_parameters": {
            "_is_completed": False,
            "_reason": "Cannot extract Date,because I don't the "
            "date of today.",
            "city": "Hangzhou",
        },
    },
    {
        "input": "what's the weather today",
        "useful_info": "today is 2025-05-01",
        "parameters_des": [
            "city:string:the city name:required",
            "date:string:the date formatted with year-month-day:required",
        ],
        "extracted_parameters": {
            "_is_completed": True,
            "_reason": "",
            "city": "Hangzhou",
            "date": "2025-05-01",
        },
    },
]
EXAMPLE_PROMPT = "\n".join(
    f'Input: {item.get("input")}\nParameter list: {item.get("parameters_des")}'
    f'\nUseful information: {item.get("useful_info", "")}'
    f'\nExtracted parameters: {json.dumps(item.get("extracted_parameters"))}\n'
    for item in EXAMPLE_LIST
)


class ParameterExtractorNode(Node):
    """
    Variable assign node
    """

    node_type: str = NodeType.PARAMETER_EXTRACTOR.value

    def _execute(self, **kwargs: Any) -> Generator:
        """execute"""
        start_time = int(time.time() * 1000)
        node_param = self.sys_args["node_param"]

        extract_params = node_param.get("extract_params", [])

        def transform_params(extract_params: list) -> list:
            """transform params"""
            parameter_list = []
            for param in extract_params:
                key = param["key"]
                param_type = param["type"].lower()
                desc = param["desc"]
                required_status = (
                    "required" if param["required"] else "optional"
                )

                parameter_list.append(
                    f"{key}:{param_type}:{desc}:{required_status}",
                )
            return parameter_list

        parameter_list = transform_params(extract_params)

        parameter_template = (
            f"The format of the parameters to be extracted is"
            f" - {{Parameter Name}}:{{Parameter Type}}:"
            f"{{Parameter Description}}:{{Is Parameter Required}}. "
            f"The list of parameters to be extracted this time is:"
            f"\n%{parameter_list}\n"
        )

        json_dict = {
            "_is_completed": "Summary containing the important "
            "information about the entity. Under 250 words",
            "_reason": "Reason for the extraction failure. "
            "If the extraction is successful, set it to an empty string.",
        }
        json_template = (
            "Please return the extracted parameters in JSON format "
            f"as follows:\n{json.dumps(json_dict)}\n"
        )

        for item in parameter_list:
            parameter_details = item.split(":")
            json_dict[parameter_details[0]] = parameter_details[2]

        user_instruction = node_param["instruction"]
        instruct_prompt = (
            "The following information is important for parameter "
            f"extraction: {user_instruction}"
        )

        user_input = self.sys_args["input_params"][0]["value"]

        user_input_prompt = f"user input: {user_input}"

        user_content = (
            instruct_prompt
            + parameter_template
            + user_input_prompt
            + f"\n\nHere are some examples: {EXAMPLE_PROMPT}\n\n "
            + json_template
            + "\n\nPlease directly respond with a JSON object."
        )

        model = get_model_instance(node_param["model_config"])

        output_params = self.sys_args["output_params"]

        messages = [
            {
                "role": "system",
                "content": SYS_PROMPT,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ]
        response = model(messages)

        usages = [
            {
                "prompt_tokens": response.raw.usage.input_tokens,
                "completion_tokens": response.raw.usage.output_tokens,
                "total_tokens": response.raw.usage.total_tokens,
            },
        ]

        json_response = json.loads(response.text)
        node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
        output_var = []
        for output_item in output_params:
            output_var.append(
                WorkflowVariable(
                    name=output_item["key"],
                    content=json_response.get(output_item["key"], ""),
                    source=self.node_id,
                    data_type=output_item["type"],
                    input={"messages": messages},
                    output=json_response,
                    output_type="json",
                    node_type=self.node_type,
                    node_name=self.node_name,
                    usages=usages,
                    node_exec_time=node_exec_time,
                ),
            )
        yield output_var
