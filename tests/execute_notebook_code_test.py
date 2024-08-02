# -*- coding: utf-8 -*-
""" iPython code execution test."""
import unittest
from agentscope.service.execute_code.exec_notebook import NoteBookExecutor
from agentscope.service.service_status import ServiceExecStatus


class ExecuteNotebookCodeTest(unittest.TestCase):
    """
    Notebook code execution test.
    """

    def setUp(self) -> None:
        """Init for ExecuteNotebookCodeTest."""
        self.executor = NoteBookExecutor()

        # Basic expression
        self.arg0 = {"code": "print('Hello World')"}
        # Using External Libraries
        self.arg1 = {"code": "import math\nprint(math.sqrt(16))"}
        # No input code
        self.arg2 = {"code": ""}
        # test without print
        self.arg3 = {"code": "1+1"}

    def test_basic_expression(self) -> None:
        """Execute basic expression test."""
        response = self.executor.run_code_on_notebook(self.arg0["code"])
        self.assertEqual(response.status, ServiceExecStatus.SUCCESS)
        self.assertIn("Hello World\n", response.content[0])

    def test_using_external_libs(self) -> None:
        """Execute using external libs test."""
        response = self.executor.run_code_on_notebook(self.arg1["code"])
        self.assertEqual(response.status, ServiceExecStatus.SUCCESS)
        self.assertIn("4.0\n", response.content[0])

    def test_no_input_code(self) -> None:
        """Execute no input code test."""
        response = self.executor.run_code_on_notebook(self.arg2["code"])
        self.assertEqual(response.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(response.content, [])

    def test_no_print(self) -> None:
        """Execute no print test."""
        response = self.executor.run_code_on_notebook(self.arg3["code"])
        self.assertEqual(response.status, ServiceExecStatus.SUCCESS)
        self.assertIn("2", response.content[0])


if __name__ == "__main__":
    unittest.main()
