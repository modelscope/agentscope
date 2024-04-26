# -*- coding: utf-8 -*-
""" Common utils."""

import contextlib
import os
import re
import signal
import sys
import tempfile
import threading
from typing import Any, Generator, Optional, Union
import requests

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus


@contextlib.contextmanager
def timer(seconds: Optional[Union[int, float]] = None) -> Generator:
    """
    A context manager that limits the execution time of a code block to a
    given number of seconds.
    The implementation of this contextmanager are borrowed from
    https://github.com/openai/human-eval/blob/master/human_eval/execution.py

    Note:
        This function only works in Unix and MainThread,
        since `signal.setitimer` is only available in Unix.

    """
    if (
        seconds is None
        or sys.platform == "win32"
        or threading.currentThread().name  # pylint: disable=W4902
        != "MainThread"
    ):
        yield
        return

    def signal_handler(*args: Any, **kwargs: Any) -> None:
        raise TimeoutError("timed out")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)

    try:
        # Enter the context and execute the code block.
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@contextlib.contextmanager
def create_tempdir() -> Generator:
    """
    A context manager that creates a temporary directory and changes the
    current working directory to it.
    The implementation of this contextmanager are borrowed from
    https://github.com/openai/human-eval/blob/master/human_eval/execution.py
    """
    with tempfile.TemporaryDirectory() as dirname:
        with chdir(dirname):
            yield dirname


@contextlib.contextmanager
def chdir(path: str) -> Generator:
    """
    A context manager that changes the current working directory to the
    given path.
    The implementation of this contextmanager are borrowed from
    https://github.com/openai/human-eval/blob/master/human_eval/execution.py
    """
    if path == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    except BaseException as exc:
        raise exc
    finally:
        os.chdir(cwd)


def write_file(content: str, file_path: str) -> ServiceResponse:
    """
    Write content to a file.

    Args:
        content (str): The content to be written to the file.
        file_path (str): The path to the file where the content will be
            written.

    Returns:
        ServiceResponse: where the boolean indicates the success of the
        operation, and the str contains an empty string if successful or an
        error message if any, including the error type.

    This function attempts to open the file in write mode and write the
    provided content to it. If the file does not exist, it will be created.
    If the file exists, its content will be overwritten. If a
    PermissionError occurs, indicating a lack of necessary permissions,
    or an IOError occurs, signaling additional issues such as an invalid
    file path or hardware-related I/O error, the function will catch the
    exception and return `False` along with the error message.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
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


def requests_get(
    url: str,
    params: dict,
    headers: Optional[dict] = None,
) -> Union[dict, str]:
    """
    Sends a GET request to the specified URL with the provided query parameters
    and headers. Returns the JSON response as a dictionary.

    This function handles the request, checks for errors, logs exceptions,
        and parses the JSON response.

    Args:
        url (str): The URL to which the GET request is sent.
        params (Dict): A dictionary containing query parameters to be included
            in the request.
        headers (Optional[Dict]): An optional dictionary of HTTP headers to
            send with the request.

    Returns:
        Dict or str:
        If the request is successful, returns a dictionary containing the
        parsed JSON data.
        If the request fails, returns the error string.
    """
    # Make the request
    try:
        # Check if headers are provided, and include them if they are not None
        if headers:
            response = requests.get(url, params=params, headers=headers)
        else:
            response = requests.get(url, params=params)
        # This will raise an exception for HTTP error codes
        response.raise_for_status()
    except requests.RequestException as e:
        return str(e)
    # Parse the JSON response
    search_results = response.json()
    return search_results


def _if_change_database(sql_query: str) -> bool:
    """Check whether SQL query only contains SELECT query"""
    # Compile the regex pattern outside the function for better performance
    pattern_unsafe_sql = re.compile(
        r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE|ALTER|DROP|TRUNCATE|USE)\b",
        re.IGNORECASE,
    )

    # Remove SQL comments
    sql_query = re.sub(r"--.*?$", "", sql_query, flags=re.MULTILINE)
    # Remove /* */ comments
    sql_query = re.sub(r"/\*.*?\*/", "", sql_query, flags=re.DOTALL)
    # Matching non-SELECT statements with regular expressions
    if pattern_unsafe_sql.search(sql_query):
        return False
    return True
