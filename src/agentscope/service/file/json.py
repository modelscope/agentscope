# -*- coding: utf-8 -*-
""" Operators for json file and directory. """
import json
import os
from typing import Any

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus


def read_json_file(file_path: str) -> ServiceResponse:
    """
    Read and parse a JSON file.

    Args:
        file_path (`str`):
            The path to the JSON file to be read.

    Returns:
        `ServiceResponse`: Where the boolean indicates success, the
        Any is the parsed JSON content (typically a dict), and the str contains
        an error message if any, including the error type.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=f"{json.load(file)}",
            )
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {e}"
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=error_message,
        )


def write_json_file(
    file_path: str,
    data: Any,
    overwrite: bool = False,
) -> ServiceResponse:
    """
    Serialize data to a JSON file.

    Args:
        file_path (`str`):
            The path to the file where the JSON data will be written.
        data (`Any`):
            The data to serialize to JSON.
        overwrite (`bool`):
            Whether to overwrite the file if it already exists.

    Returns:
        `ServiceResponse`: where the boolean indicates success, and the
        str contains an error message if any, including the error type.
    """
    if not overwrite and os.path.exists(file_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileExistsError: The file already exists.",
        )
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Success",
        )
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {e}"
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=error_message,
        )
