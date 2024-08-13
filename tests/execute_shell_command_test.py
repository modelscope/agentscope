# -*- coding: utf-8 -*-
""" Python code execution test."""
import os
import unittest
import platform

from agentscope.service import execute_shell_command
from agentscope.service import ServiceExecStatus


class ExecuteShellCommandTest(unittest.TestCase):
    """
    Python code execution test.
    """

    def setUp(self) -> None:
        """Init for ExecuteShellCommandTest."""

        # Basic expression
        self.arg0 = "touch tmp_a.txt"

        self.arg1 = "echo 'Helloworld' >> tmp_a.txt"

        self.arg2 = "cat tmp_a.txt"

        self.arg3 = "rm tmp_a.txt"

    def tearDown(self) -> None:
        """Tear down for ExecuteShellCommandTest."""
        if os.path.exists("tmp_a.txt"):
            os.remove("tmp_a.txt")

    def test(self) -> None:
        """test command, skip on windows"""
        if platform.system() == "Windows":
            return
        result = execute_shell_command(
            command=self.arg0,
        )
        assert result.status == ServiceExecStatus.SUCCESS
        assert result.content == "Success."

        result = execute_shell_command(
            command=self.arg1,
        )
        assert result.status == ServiceExecStatus.SUCCESS
        assert result.content == "Success."

        result = execute_shell_command(
            command=self.arg2,
        )
        assert result.status == ServiceExecStatus.SUCCESS
        assert result.content == "Helloworld"

        result = execute_shell_command(
            command=self.arg3,
        )
        assert result.status == ServiceExecStatus.SUCCESS
        assert result.content == "Success."

        result = execute_shell_command(
            command=self.arg3,
        )
        assert result.status == ServiceExecStatus.ERROR


if __name__ == "__main__":
    unittest.main()
