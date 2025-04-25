# -*- coding: utf-8 -*-
"""Service to execute shell commands."""
import subprocess

from loguru import logger

from agentscope.service.service_status import ServiceExecStatus
from agentscope.service.service_response import ServiceResponse


def execute_shell_command(
    command: str,
    timeout: float = 300,
) -> ServiceResponse:
    """Execute given command and return the return code, standard output and
    error within <returncode></returncode>, <stdout></stdout> and
    <stderr></stderr> tags.

    Args:
        command (`str`):
            The shell command to execute.
        timeout (`float`, defaults to `300`):
            The maximum time (in seconds) allowed for the command to run.

    Returns:
        `ServiceResponse`:
            The status field indicates whether the command execution was
            successful. The content field contains the return code,
            standard output, and standard error of the executed command.

    .. note:: Use any bash/shell commands you want (e.g. find, grep, cat, ls),
     but note that
     1. interactive session commands (e.g. python, vim) or
     commands that change current state (e.g. cd that change the current
     directory) are NOT supported yet, so please do not invoke them.
     2. be VERY CAREFUL when using commands that will change/edit the files
     current directory (e.g. rm, sed).
    ...
    """

    if any(_ in command for _ in execute_shell_command.insecure_commands):
        logger.warning(
            f"The command {command} is blocked for security reasons. "
            f"If you want to enable the command, try to reset the "
            f"insecure command list by executing "
            f'`execute_shell_command.insecure_commands = ["xxx", "xxx"]`',
        )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=f"The command {command} is blocked for security reasons.",
        )

    try:
        res = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            shell=True,
        )
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=(
                f"<returncode>{res.returncode}</returncode>\n"
                f"<stdout>{res.stdout}</stdout>\n"
                f"<stderr>{res.stderr}</stderr>"
            ),
        )

    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode("utf-8") if e.stdout else ""
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=(
                "<returncode>-1</returncode>\n"
                f"<stdout>{stdout}</stdout>\n"
                "<stderr>Error: Command execution timeout after "
                f"{timeout} seconds. Consider increasing the timeout "
                f"value or adjusting your command<stderr>"
            ),
        )


# Security check: Block insecure commands
execute_shell_command.insecure_commands = [
    # System management
    "shutdown",
    "kill",
    "reboot",
    "pkill",
    # User management
    "useradd",
    "userdel",
    "usermod",
    # File management
    "rm -rf",
]
