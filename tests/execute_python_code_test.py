# -*- coding: utf-8 -*-
""" Python code execution test."""
import unittest
import sys

from agentscope.service import execute_python_code


class ExecutePythonCodeTest(unittest.TestCase):
    """
    Python code execution test.
    """

    def setUp(self) -> None:
        """Init for ExecutePythonCodeTest."""

        # Basic expression
        self.arg0 = {"code": "print('Hello World')", "timeout": 5}

        # Raising Exceptions
        self.arg1 = {
            "code": "print('Hello World')\nraise ValueError('An intentional "
            "error')",
            "timeout": 5,
        }

        # Using External Libraries
        self.arg2 = {"code": "import math\nprint(math.sqrt(16))", "timeout": 5}

        # Timeout
        self.arg3 = {
            "code": "import time\nprint('Hello World')\ntime.sleep("
            "10)\nprint('This will not print')",
            "timeout": 1,
        }

        # No input code
        self.arg4 = {"code": "", "timeout": 5}

    def run_test(
        self,
        args: dict,
        expected_output: str,
        expected_error_substr: str,
    ) -> None:
        """A helper function to avoid code repetition"""
        response = execute_python_code(
            use_docker=False,
            **args,
        )
        self.assertIn(expected_output, response.content)
        self.assertIn(expected_error_substr, response.content)

        # Uncomment it when test in local
        # response = execute_python_code(
        #     use_docker=True,
        #     **args,
        # )
        # self.assertIn(expected_output, response.content)
        # self.assertIn(expected_error_substr, response.content)

    def test_basic_expression(self) -> None:
        """Execute basic expression test."""
        self.run_test(self.arg0, "Hello World\n", "")

    def test_raising_exceptions(self) -> None:
        """Execute raising exceptions test."""
        self.run_test(
            self.arg1,
            "Hello World\n",
            "ValueError: An intentional error\n",
        )

    def test_using_external_libs(self) -> None:
        """Execute using external libs test."""
        self.run_test(self.arg2, "4.0\n", "")

    def test_timeout(self) -> None:
        """Execute timeout test (NOT available in WinOS.)"""
        if sys.platform == "win32":
            return
        self.run_test(self.arg3, "Hello World\n", "timed out\n")

    def test_no_input_code(self) -> None:
        """Execute no input code test."""
        self.run_test(self.arg4, "", "")


if __name__ == "__main__":
    unittest.main()
