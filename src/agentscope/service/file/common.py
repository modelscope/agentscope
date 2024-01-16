# -*- coding: utf-8 -*-
""" Common operators for file and directory. """
import os
import shutil

from agentscope.utils.common import write_file
from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus


def create_file(file_path: str, content: str = "") -> ServiceResponse:
    """
    Create a file and write content to it.

    Args:
        file_path (`str`):
            The path where the file will be created.
        content (`str`):
            Content to write into the file.

    Returns:
        `ServiceResponse`: Where the boolean indicates success, and the
        str contains an error message if any, including the error type.

    """
    if os.path.exists(file_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileExistsError: The file already exists.",
        )
    return write_file(content, file_path)


def delete_file(file_path: str) -> ServiceResponse:
    """Delete a file specified by the file path.

    Args:
        file_path (`str`):
            The path of the file to be deleted.

    Returns:
        `ServiceResponse`: Where the boolean indicates success, and the
        str contains an error message if any, including the error type.

    """
    try:
        os.remove(file_path)
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


def move_file(source_path: str, destination_path: str) -> ServiceResponse:
    """
    Move a file from a source path to a destination path.

    Args:
        source_path (`str`):
            The current path of the file.
        destination_path (`str`):
            The new path for the file.

    Returns:
        `ServiceResponse`: Where the boolean indicates success, and the
        str contains an error message if any, including the error type.

    """
    if not os.path.exists(source_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileNotFoundError: The source file does not exist.",
        )
    if os.path.exists(destination_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileExistsError: The destination file already exists.",
        )
    try:
        shutil.move(source_path, destination_path)
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


def create_directory(directory_path: str) -> ServiceResponse:
    """
    Create a directory at the specified path.

    Args:
        directory_path (`str`):
            The path where the directory will be created.

    Returns:
        `ServiceResponse`: where the boolean indicates success, and the
        str contains an error message if any, including the error type.

    """
    if os.path.exists(directory_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileExistsError: The directory already exists.",
        )
    try:
        os.makedirs(directory_path)
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


def delete_directory(directory_path: str) -> ServiceResponse:
    """
    Delete a directory and all of its contents.

    Args:
        directory_path (`str`):
            The path of the directory to be deleted.

    Returns:
        `ServiceResponse`: Where the boolean indicates success, and the
        str contains an error message if any, including the error type.

    """
    if not os.path.exists(directory_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileExistsError: The directory does not exists.",
        )
    try:
        shutil.rmtree(directory_path)
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


def move_directory(
    source_path: str,
    destination_path: str,
) -> ServiceResponse:
    """
    Move a directory from a source path to a destination path.

    Args:
        source_path (`str`):
            The current path of the directory.
        destination_path (`str`):
            The new path for the directory.

    Returns:
        `ServiceResponse`: Where the boolean indicates success, and the
        str contains an error message if any, including the error type.

    """
    if not os.path.exists(source_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileNotFoundError: The source directory does not exist.",
        )
    if os.path.exists(destination_path):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content="FileExistsError: The destination directory already "
            "exists.",
        )
    try:
        shutil.move(source_path, destination_path)
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
