# -*- coding: utf-8 -*-
# pylint: disable=too-many-statements
"""Workflow pipeline."""
import copy
import os
import re
import time
import json

from typing import Any, List, Generator

from app.workflow_engine.core.node_caches.node_cache_handler import NodeCache
from app.workflow_engine.core.node_caches.workflow_var import WorkflowVariable
from .interface import exec_runner, exec_compiler, exec_optimizer
from .utils.misc import create_format_output
from ..core.utils.error import ParseError


def parse_api_request(request_dict: dict, **kwargs: Any) -> dict:
    """Parse api request."""
    request_id = kwargs.get("request_id", "")

    def check_args(
        payload: dict,
        required_keys: List,
        prefix: str = "",
    ) -> None:
        for key in required_keys:
            if key not in payload:
                error_msg = (
                    f"request_id: {request_id}:\n"
                    f"Parameter {key} is required in {payload}."
                )
                if prefix:
                    error_msg = f"{prefix}, {error_msg}"
                raise ParseError(error_msg)

    custom_params = request_dict["parameters"]["custom"]

    check_args(
        custom_params,
        required_keys=["dsl_config", "params"],
        prefix="Custom args checking",
    )

    # Pass history to global parameters
    custom_params["params"]["messages"] = request_dict["input"]["messages"]

    return {
        "scene": custom_params.get("scene", "run"),
        "params": custom_params["params"],
        "dsl_config": custom_params["dsl_config"],
    }


def extract_all_node_ids(text: str) -> List:
    """Extract all node ids from text."""
    pattern = r"\$\{([^.]+)\.([^}]+)\}"
    matches = re.findall(pattern, text)
    return matches


# Pre-compile regex patterns for better performance
NON_LLM_PATTERN = re.compile(r"\$\{(?!LLM_)([^.]+)\.([^}]+)\}")
LLM_PATTERN = re.compile(r"\$\{(LLM_[^.]+)\.output\}")


# pylint: disable=too-many-return-statements, too-many-branches,
# too-many-return-statements
def get_node_content(node_result: dict, field: str) -> str:
    """Helper function to extract content from node results regardless of
    format"""
    try:
        # For object-style results
        if "results" in dir(node_result):  # Use dir() instead of hasattr()
            results = node_result.results
            if results:
                for result in results:
                    # Special case for output/content
                    if field == "output" and "content" in dir(result):
                        return str(result.content)

                    # Try dictionary-style access with exception catching
                    try:
                        # Directly try to access and catch any exceptions
                        value = result[field]
                        return str(value)
                    except Exception:
                        if field == result["key"].split(".")[-1]:
                            return str(result["content"])
                        else:
                            pass
                    # Try accessing via __dict__ if available
                    try:
                        if (
                            "__dict__"
                            in dir(
                                result,
                            )
                            and field in result.__dict__
                        ):
                            return str(result.__dict__[field])
                    except Exception:
                        pass

        # For dictionary-style results
        elif (
            isinstance(node_result, dict)
            and "results" in node_result
            and node_result["results"]
        ):
            for result in node_result["results"]:
                if field == "output" and "content" in result:
                    return str(result["content"])
                elif field in result:
                    return str(result[field])
                elif field == result["key"].split(".")[-1]:
                    return str(result["content"])
    except Exception:
        # Catch any unexpected exceptions during processing
        pass

    # Return empty string if nothing found or any error occurred
    return ""


# pylint: disable=too-many-branches, too-many-nested-blocks
def workflow_pipeline(
    request: dict,
    **kwargs: Any,
) -> Generator:
    """Workflow pipeline, main interface for all requests."""
    request_id = kwargs.get("request_id", "")

    request_dict = copy.deepcopy(request)
    parsed_request = parse_api_request(
        request_dict,
        **kwargs,
    )
    scene = parsed_request["scene"]
    memory = kwargs.get("memory", [])

    if scene == "optimize":
        gen = exec_optimizer
    elif scene == "compile":
        gen = exec_compiler
    else:
        gen = exec_runner

    for messages in gen(
        params=parsed_request["params"],
        dsl_config=parsed_request["dsl_config"],
        request_id=request_id,
        memory=memory,
    ):
        pause_nodes = []
        for msg in messages:
            pause_nodes.extend(msg.get("status", {}).get("pause_nodes", []))
        if pause_nodes:
            dsl_config = parsed_request["dsl_config"]
            nodes = dsl_config["workflow"]["graph"]["nodes"]
            for pause_node in pause_nodes:
                if pause_node.startswith("Input_"):
                    for node in nodes:
                        if node["id"] == pause_node:
                            node_result = {
                                "node_id": pause_node,
                                "node_name": node["name"],
                                "node_type": node["type"],
                                "input": node["config"]["output_params"],
                                "node_status": "pause",
                                "batches": [],
                                "is_multi_branch": False,
                                "is_batch": False,
                            }
                            for msg in messages:
                                msg["status"]["inter_results"][pause_node] = {
                                    "results": [node_result],
                                }
                            break
        else:
            run_nodes = messages[0]["status"]["run_nodes"]
            inter_results = messages[0]["status"]["inter_results"]
            dsl_config = parsed_request["dsl_config"]
            nodes = dsl_config["workflow"]["graph"]["nodes"]
            end_node = [node for node in nodes if node["type"] == "End"][0]
            end_node_param = end_node["config"]["node_param"]

            if end_node_param.get(
                "output_type",
            ) == "text" and end_node_param.get("stream_switch", False):
                # Extract template text
                text_template = end_node_param.get("text_template", "")

                # Extract all node references (both LLM and non-LLM)
                all_node_refs = extract_all_node_ids(text_template)
                all_node_ids = set(node_id for node_id, _ in all_node_refs)

                # Prepare node categories
                llm_nodes = []
                non_llm_nodes = []
                # Classify nodes with one pass
                for node_id, field in all_node_refs:
                    if (
                        node_id.startswith(
                            "LLM_",
                        )
                        and field == "output"
                        and node_id in run_nodes
                    ):
                        llm_nodes.append(node_id)
                    elif node_id in run_nodes:
                        non_llm_nodes.append((node_id, field))

                # Check status of all nodes
                all_success = all(
                    node_id in inter_results
                    and inter_results[node_id] is not None
                    and inter_results[node_id].status == "success"
                    for node_id in all_node_ids
                    if node_id in run_nodes
                )
                status = "success" if all_success else "executing"

                # 1. First, replace all variables from non-LLM nodes
                def replace_non_llm(match: re.Match) -> str:
                    node_id = match.group(1)
                    field = match.group(2)

                    if (
                        node_id in inter_results
                        and inter_results[node_id] is not None
                    ):
                        return get_node_content(inter_results[node_id], field)
                    return ""  # Return empty string if node not found

                # Replace all non-LLM variables
                text_template = NON_LLM_PATTERN.sub(
                    replace_non_llm,
                    text_template,
                )

                # 2. Continue processing LLM nodes (streaming output part)
                if llm_nodes:
                    # Check LLM node status (only for streaming logic)
                    llm_status = all(
                        llm_node in inter_results
                        and inter_results[llm_node] is not None
                        and inter_results[llm_node].status == "success"
                        for llm_node in llm_nodes
                    )

                    if not llm_status:
                        # If there are unfinished LLM nodes, perform
                        # streaming processing
                        # Use LLM nodes as separators to split template
                        # into multiple parts
                        parts = []
                        last_pos = 0
                        # Use regex to split the template
                        for match in LLM_PATTERN.finditer(text_template):
                            llm_id = match.group(
                                1,
                            )  # Add text before the LLM node
                            prefix_text = text_template[
                                last_pos : match.start()
                            ]
                            if prefix_text:
                                last_llm = (
                                    parts[-1]["id"]
                                    if parts and parts[-1]["type"] == "llm"
                                    else None
                                )
                                parts.append(
                                    {
                                        "type": "text",
                                        "content": prefix_text,
                                        "depends_on": last_llm,
                                    },
                                )

                            # Add LLM node
                            parts.append({"type": "llm", "id": llm_id})
                            last_pos = match.end()
                        # Add text after the last LLM node
                        suffix_text = text_template[last_pos:]
                        if suffix_text:
                            last_llm = llm_id if "llm_id" in locals() else None
                            parts.append(
                                {
                                    "type": "text",
                                    "content": suffix_text,
                                    "depends_on": last_llm,
                                },
                            )

                        # Build output content
                        output_parts = []
                        for part in parts:
                            if part["type"] == "text":
                                depends_on = part.get("depends_on")
                                if depends_on is None or (
                                    depends_on in inter_results
                                    and inter_results[depends_on] is not None
                                    and inter_results[depends_on].status
                                    == "success"
                                ):
                                    output_parts.append(part["content"])
                            elif part["type"] == "llm":
                                llm_id = part["id"]
                                if (
                                    llm_id in inter_results
                                    and inter_results[llm_id] is not None
                                ):
                                    if (
                                        llm_id in inter_results
                                        and inter_results[llm_id] is not None
                                    ):
                                        content = get_node_content(
                                            inter_results[llm_id],
                                            "output",
                                        )
                                        if content:
                                            output_parts.append(content)
                        # Join output parts for better performance than +=
                        # string concatenation
                        end_node_output = "".join(output_parts)
                    else:
                        # If all LLM nodes are completed,
                        # directly replace all LLM variables
                        for llm_id in llm_nodes:
                            if (
                                llm_id in inter_results
                                and inter_results[llm_id] is not None
                            ):
                                content = ""
                                if (
                                    hasattr(inter_results[llm_id], "results")
                                    and inter_results[llm_id].results
                                ):
                                    content = (
                                        inter_results[llm_id]
                                        .results[0]
                                        .content
                                    )
                                elif (
                                    isinstance(inter_results[llm_id], dict)
                                    and "results" in inter_results[llm_id]
                                ):
                                    content = inter_results[llm_id]["results"][
                                        0
                                    ].content
                                text_template = text_template.replace(
                                    f"${{{llm_id}.output}}",
                                    content,
                                )
                        end_node_output = text_template
                else:
                    # If there are no LLM nodes,
                    # use the processed template directly
                    end_node_output = text_template

                # Update end_node output
                messages[0]["status"]["inter_results"][
                    end_node["id"]
                ] = NodeCache(
                    results=[
                        WorkflowVariable(
                            name="output",
                            node_name=end_node["name"],
                            node_type=end_node["type"],
                            input=[],
                            batches=[],
                            is_multi_branch=False,
                            is_batch=False,
                            output=end_node_output,
                            output_type="text",
                            content=end_node_output,
                        ),
                    ],
                    node_id=end_node["id"],
                    status=status,  # This status considers all nodes
                )

        yield create_format_output(
            messages=messages,
            **kwargs,
        )


if __name__ == "__main__":
    stime = int(time.time() * 1000)

    with open(
        "app/workflow_engine/as_workflow/configs/run/test_agent_workflow.json",
        "r",
        encoding="utf-8",
    ) as f:
        request_payload = json.load(f)

    # yml_path = "configs/dsl_examples/Iterator.yml"
    # if os.path.exists(yml_path):
    #     with open(yml_path, "r", encoding="utf-8") as f:
    #         _, file_extension = os.path.splitext(yml_path)
    #         if file_extension in [".yml", ".yaml"]:
    #             config = yaml.safe_load(f)
    #             request_payload["payload"]["parameters"]["custom"][
    #                 "dsl_config"
    #             ] = config
    example_config_path = (
        "app/workflow_engine/as_workflow/configs/config_examples/llm.json"
    )
    if os.path.exists(example_config_path):
        with open(example_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            config["workflow"] = {
                "graph": config["config"],
            }
            del config["config"]
            request_payload["payload"]["parameters"]["custom"][
                "dsl_config"
            ] = config

    package = None
    for pack_idx, package in enumerate(
        workflow_pipeline(
            request_payload["payload"],
            request_id=request_payload["header"]["request_id"],
        ),
    ):
        from app.tasks.workflow import transfer_package

        package = transfer_package(package)

        print(
            f"------Package {pack_idx}, cost time {time.time() - stime}------",
        )
        print(json.dumps(package, ensure_ascii=False, indent=2))

    task_exec_time = str(int(time.time() * 1000) - stime) + "ms"
    print(
        f"------Total cost time {task_exec_time}------",
    )
    package["task_exec_time"] = task_exec_time
    print(json.dumps(package, ensure_ascii=False, indent=2))
