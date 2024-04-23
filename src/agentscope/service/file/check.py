# -*- coding: utf-8 -*-
"""
Tools for checking files, such as linting and formatting.
"""
import subprocess

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus


def exec_py_linting(file_path: str) -> ServiceResponse:
    """
    Executes flake8 linting on the given .py file with specified checks and
    returns the linting result.

    Args:
        file_path (`str`): The path to the Python file to lint.

    Returns:
        ServiceResponse: Contains either the output from the flake8 command as
        a string if successful, or an error message including the error type.
    """
    command = f"flake8 --isolated --select=F821,F822,F831,\
        E111,E112,E113,E999,E902 {file_path}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=result.stdout.strip()
            if result.stdout
            else "No lint errors found.",
        )
    except subprocess.CalledProcessError as e:
        error_message = (
            e.stderr.strip()
            if e.stderr
            else "An error occurred while linting the file."
        )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=error_message,
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=str(e),
        )
