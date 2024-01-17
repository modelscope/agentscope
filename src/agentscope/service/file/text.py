# -*- coding: utf-8 -*-
""" Operators for txt file and directory. """
import os

from agentscope.utils.common import write_file
from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus


def read_text_file(file_path: str) -> ServiceResponse:
    """
    Read the content of the text file.

    Args:
        file_path (`str`):
            The path to the text file to be read.

    Returns:
        `ServiceResponse`: A tuple (bool, str) where the boolean indicates
        success, and the str contains the file content or an error message
        if any, including the error type.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=file.read(),
            )
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {e}"
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=error_message,
        )


def write_text_file(
    file_path: str,
    content: str,
    overwrite: bool = False,
) -> ServiceResponse:
    """
    Write content to a text file.

    Args:
        file_path (`str`):
            The path to the file where content will be written.
        content (`str`):
            Content to write into the file.
        overwrite (`bool`, defaults to `False`):
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
    return write_file(content, file_path)
