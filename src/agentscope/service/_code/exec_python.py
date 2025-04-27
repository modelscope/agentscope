# -*- coding: utf-8 -*-
# pylint: disable=unused-argument,C0301
"""Execute python code"""
import os
import subprocess
import sys
import tempfile
from typing import Any

import shortuuid

from ..service_response import ServiceResponse
from ..service_status import ServiceExecStatus


def execute_python_code(
    code: str,
    timeout: float = 300,
    **kwargs: Any,
) -> ServiceResponse:
    """Execute the given python code in a temp file and capture the return code, standard output and error. Note you must `print` the output to get the result, and the tmp file will be removed right after the execution.

    Args:
        code (`str`):
            The Python code to be executed.
        timeout (`float`, defaults to `300`):
            The maximum time (in seconds) allowed for the code to run.

    Returns:
        `ServiceResponse`:
            The status field indicates whether the code execution was
            successful. The content field contains the return code,
            standard output, and standard error of the executed code.
    """  # noqa

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = os.path.join(temp_dir, f"tmp_{shortuuid.uuid()}.py")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            res = subprocess.run(
                [sys.executable, temp_file],
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
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
                    "<stderr>Error: Python code execution timeout after "
                    f"{timeout} seconds. Consider increasing the timeout "
                    f"value or adjusting your code<stderr>"
                ),
            )
