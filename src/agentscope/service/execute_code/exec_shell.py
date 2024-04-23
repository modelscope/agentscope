# -*- coding: utf-8 -*-
"""Service to execute shell commands."""
import subprocess
from agentscope.service.service_status import ServiceExecStatus
from agentscope.service.service_response import ServiceResponse


def execute_shell_command(command: str) -> ServiceResponse:
    """
    Executes a given shell command.

    Args:
        command (str): The shell command to execute.

    Returns:
        ServiceResponse: Contains either the output from the shell command as a
        string if sucessful, or an error message include the error type.

    Note:
        Use any bash/shell commands you want (e.g. find, grep, cat, ls),
        but note that :
        1. interactive session commands (e.g. python, vim) or commands that
        change current state (e.g. cd that change the current directory)
        are NOT supported yet, so please do not invoke them.
        2. be VERY CAREFUL when using commands that will
        change/edit the files current directory (e.g. rm, sed).
    ...
    """
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
            content=result.stdout.strip() if result.stdout else "Success.",
        )
    except subprocess.CalledProcessError as e:
        error_message = (
            e.stderr.strip()
            if e.stderr
            else "An error occurred \
            while executing the command."
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
