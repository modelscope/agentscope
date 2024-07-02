# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""
Tools for swe-agent, such as checking files with linting and formatting,
writing and reading files by lines, etc.
"""
import subprocess
import os

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


def write_file(
    file_path: str,
    content: str,
    start_line: int = 0,
    end_line: int = -1,
) -> ServiceResponse:
    """
    Write content to a file by replacing the current lines between <start_line> and <end_line> with <content>. Default start_line = 0 and end_line = -1. Calling this with no <start_line> <end_line> args will replace the whole file, so besure to use this with caution when writing to a file that already exists.

    Args:
        file_path (`str`): The path to the file to write to.
        content (`str`): The content to write to the file.
        start_line (`Optional[int]`, defaults to `0`): The start line of the file to be replace with <content>.
        end_line (`Optional[int]`, defaults to `-1`): The end line of the file to be replace with <content>. end_line = -1 means the end of the file, otherwise it should be a positive integer indicating the line number.
    """  # noqa
    try:
        mode = "w" if not os.path.exists(file_path) else "r+"
        insert = content.split("\n")
        with open(file_path, mode, encoding="utf-8") as file:
            if mode != "w":
                all_lines = file.readlines()
                new_file = [""] if start_line == 0 else all_lines[:start_line]
                new_file += [i + "\n" for i in insert]
                last_line = end_line + 1
                new_file += [""] if end_line == -1 else all_lines[last_line:]
            else:
                new_file = insert

            file.seek(0)
            file.writelines(new_file)
            file.truncate()
            obs = f'WRITE OPERATION:\nYou have written to "{file_path}" \
                on these lines: {start_line}:{end_line}.'
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=obs + "".join(new_file),
            )
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {e}"
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=error_message,
        )


def read_file(
    file_path: str,
    start_line: int = 0,
    end_line: int = -1,
) -> ServiceResponse:
    """
    Shows a given file's contents starting from <start_line> up to <end_line>. Default: start_line = 0, end_line = -1. By default the whole file will be read.

    Args:
        file_path (`str`): The path to the file to read.
        start_line (`Optional[int]`, defaults to `0`): The start line of the file to be read.
        end_line (`Optional[int]`, defaults to `-1`): The end line of the file to be read.
    """  # noqa
    start_line = max(start_line, 0)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            if end_line == -1:
                if start_line == 0:
                    code_view = file.read()
                else:
                    all_lines = file.readlines()
                    code_slice = all_lines[start_line:]
                    code_view = "".join(code_slice)
            else:
                all_lines = file.readlines()
                num_lines = len(all_lines)
                begin = max(0, min(start_line, num_lines - 2))
                end_line = (
                    -1 if end_line > num_lines else max(begin + 1, end_line)
                )
                code_slice = all_lines[begin:end_line]
                code_view = "".join(code_slice)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=f"{code_view}",
        )
    except Exception as e:
        error_message = f"{e.__class__.__name__}: {e}"
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=error_message,
        )
