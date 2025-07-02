# -*- coding: utf-8 -*-
"""Unit tests for script node"""
import unittest
from unittest.mock import patch, MagicMock
from app.workflow_engine.as_workflow.node.script import ScriptNode

# pylint: disable=protected-access,unused-argument


class TestScriptNode(unittest.TestCase):
    """Unit tests for ScriptNode based on actual configuration."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.node_id = "Script_vtim"
        self.node_name = "Script1"

        # Configuration based on actual workflow config
        self.node_kwargs = {
            "config": {
                "node_param": {
                    "script_content": (
                        "def main():\n"
                        "  ret = {\n"
                        "    \"output\": params['input1'] + params['input2']\n"
                        "  }\n"
                        "  return ret"
                    ),
                    "script_type": "python",
                    "retry_config": {
                        "retry_enabled": False,
                        "max_retries": 3,
                        "retry_interval": 500,
                    },
                    "try_catch_config": {"strategy": "noop"},
                },
                "input_params": [
                    {
                        "key": "input1",
                        "value_from": "input",
                        "value": "3",
                        "type": "Number",
                    },
                    {
                        "key": "input2",
                        "value_from": "input",
                        "value": "4",
                        "type": "Number",
                    },
                ],
                "output_params": [
                    {
                        "key": "output",
                        "type": "Number",
                        "desc": "the sum of two inputs",
                    },
                ],
            },
            "type": "Script",
            "id": self.node_id,
            "name": self.node_name,
        }

    @patch("app.workflow_engine.as_workflow.node.script.Sandbox")
    @patch("app.workflow_engine.as_workflow.node.script.json5")
    def test_execute_addition_script(
        self,
        mock_json5: MagicMock,
        mock_sandbox: MagicMock,
    ) -> None:
        """Test executing the addition script with inputs 3 and 4."""
        # Create script node instance
        script_node = ScriptNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )

        # Set up sandbox mock
        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.run_ipython_cell.return_value.output = (
            '{"output":7}'
        )
        mock_sandbox.return_value.__enter__.return_value = (
            mock_sandbox_instance
        )

        # Set up json5 mock to parse the output
        mock_json5.loads.return_value = {"output": 7}

        # Execute the node - no graph needed for normal execution
        result_generator = script_node._execute()
        results = list(result_generator)

        # Verify results - now expecting one yield per output param
        self.assertEqual(len(results), 1)  # One yield for one output param
        output_vars = results[0]
        self.assertEqual(len(output_vars), 1)

        # Check output variable properties
        output_var = output_vars[0]
        self.assertEqual(output_var.name, "output")
        self.assertEqual(output_var.content, 7)  # 3 + 4 = 7
        self.assertEqual(output_var.source, self.node_id)
        self.assertEqual(output_var.data_type, "Number")

        # Verify sandbox was called with the correct script
        mock_sandbox_instance.run_ipython_cell.assert_called_once()
        # Check if the parameters were passed correctly
        call_args = mock_sandbox_instance.run_ipython_cell.call_args[0][0]
        self.assertIn("params = ", call_args)
        self.assertIn("params['input1']", call_args)
        self.assertIn("params['input2']", call_args)

    @patch("app.workflow_engine.as_workflow.node.script.Sandbox")
    def test_script_execution_error(self, mock_sandbox: MagicMock) -> None:
        """
        Test error handling when script execution fails with noop strategy.
        """
        # Create script node
        script_node = ScriptNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )

        # Set up sandbox mock to raise an exception
        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.run_ipython_cell.side_effect = Exception(
            "Script execution failed",
        )
        mock_sandbox.return_value.__enter__.return_value = (
            mock_sandbox_instance
        )

        # Execute the node and expect ValueError (noop strategy) - no graph
        # needed
        with self.assertRaises(ValueError) as context:
            list(script_node._execute())

        self.assertIn("Script execution failed", str(context.exception))

        # Verify sandbox was called
        mock_sandbox_instance.run_ipython_cell.assert_called_once()

    @patch("app.workflow_engine.as_workflow.node.script.Sandbox")
    @patch("app.workflow_engine.as_workflow.node.script.json5")
    @patch("app.workflow_engine.as_workflow.node.script.time")
    def test_with_retry_enabled(
        self,
        mock_time: MagicMock,
        mock_json5: MagicMock,
        mock_sandbox: MagicMock,
    ) -> None:
        """Test script execution with retry enabled."""
        # Create modified node kwargs with retry enabled
        retry_node_kwargs = {
            "config": {
                "node_param": {
                    "script_content": (
                        "def main():\n"
                        "  ret = {\n"
                        "    \"output\": params['input1'] + params['input2']\n"
                        "  }\n"
                        "  return ret"
                    ),
                    "script_type": "python",
                    "retry_config": {
                        "retry_enabled": True,
                        "max_retries": 3,
                        "retry_interval": 500,
                    },
                    "try_catch_config": {"strategy": "noop"},
                },
                "input_params": [
                    {
                        "key": "input1",
                        "value_from": "input",
                        "value": "3",
                        "type": "Number",
                    },
                    {
                        "key": "input2",
                        "value_from": "input",
                        "value": "4",
                        "type": "Number",
                    },
                ],
                "output_params": [
                    {
                        "key": "output",
                        "type": "Number",
                        "desc": "the sum of two inputs",
                    },
                ],
            },
            "type": "Script",
            "id": self.node_id,
            "name": self.node_name,
        }

        # Create script node
        script_node = ScriptNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=retry_node_kwargs,
            glb_custom_args={},
            params={},
        )

        # Set up sandbox mock to fail twice then succeed
        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.run_ipython_cell.side_effect = [
            Exception("First attempt fails"),
            Exception("Second attempt fails"),
            MagicMock(output='{"output": 7}'),  # Third attempt succeeds
        ]
        mock_sandbox.return_value.__enter__.return_value = (
            mock_sandbox_instance
        )

        # Set up json5 mock
        mock_json5.loads.return_value = {"output": 7}

        # Execute the node with retry - no graph needed
        result_generator = script_node._execute()
        results = list(result_generator)

        # Verify retry behavior
        self.assertEqual(mock_sandbox_instance.run_ipython_cell.call_count, 3)
        self.assertEqual(
            mock_time.sleep.call_count,
            2,
        )  # Should sleep twice between retries

        # Verify results after successful retry
        self.assertEqual(len(results), 1)
        output_vars = results[0]
        output_var = output_vars[0]
        self.assertEqual(output_var.content, 7)

    @patch("app.workflow_engine.as_workflow.node.script.Sandbox")
    def test_with_default_value_strategy(
        self,
        mock_sandbox: MagicMock,
    ) -> None:
        """Test script execution with defaultValue error handling strategy."""
        # Create modified node kwargs with defaultValue strategy
        default_value_kwargs = {
            "config": {
                "node_param": {
                    "script_content": (
                        "def main():\n"
                        "  ret = {\n"
                        "    \"output\": params['input1'] + params['input2']\n"
                        "  }\n"
                        "  return ret"
                    ),
                    "script_type": "python",
                    "retry_config": {
                        "retry_enabled": False,
                        "max_retries": 3,
                        "retry_interval": 500,
                    },
                    "try_catch_config": {
                        "strategy": "defaultValue",
                        "default_values": [
                            {"key": "output", "value": 999, "type": "Number"},
                        ],
                    },
                },
                "input_params": [
                    {
                        "key": "input1",
                        "value_from": "input",
                        "value": "3",
                        "type": "Number",
                    },
                    {
                        "key": "input2",
                        "value_from": "input",
                        "value": "4",
                        "type": "Number",
                    },
                ],
                "output_params": [
                    {
                        "key": "output",
                        "type": "Number",
                        "desc": "the sum of two inputs",
                    },
                ],
            },
            "type": "Script",
            "id": self.node_id,
            "name": self.node_name,
        }

        # Create script node
        script_node = ScriptNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=default_value_kwargs,
            glb_custom_args={},
            params={},
        )

        # Set up sandbox mock to raise an exception
        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.run_ipython_cell.side_effect = Exception(
            "Script execution failed",
        )
        mock_sandbox.return_value.__enter__.return_value = (
            mock_sandbox_instance
        )

        # Execute the node - no graph needed for defaultValue strategy
        result_generator = script_node._execute()
        results = list(result_generator)

        # Verify default value is used
        self.assertEqual(len(results), 1)
        output_vars = results[0]
        output_var = output_vars[0]
        self.assertEqual(output_var.name, "output")
        self.assertEqual(output_var.content, 999)  # Default value
        self.assertEqual(output_var.data_type, "Number")
        self.assertTrue(output_var.try_catch["happened"])
        self.assertEqual(output_var.try_catch["strategy"], "defaultValue")

    @patch("app.workflow_engine.as_workflow.node.script.Sandbox")
    @patch("app.workflow_engine.as_workflow.node.script.format_output")
    def test_with_fail_branch_strategy(
        self,
        mock_format_output: MagicMock,
        mock_sandbox: MagicMock,
    ) -> None:
        """Test script execution with failBranch error handling strategy."""
        # Create modified node kwargs with failBranch strategy
        fail_branch_kwargs = {
            "config": {
                "node_param": {
                    "script_content": (
                        "def main():\n"
                        "  ret = {\n"
                        "    \"output\": params['input1'] + params['input2']\n"
                        "  }\n"
                        "  return ret"
                    ),
                    "script_type": "python",
                    "retry_config": {
                        "retry_enabled": False,
                        "max_retries": 3,
                        "retry_interval": 500,
                    },
                    "try_catch_config": {"strategy": "failBranch"},
                },
                "input_params": [
                    {
                        "key": "input1",
                        "value_from": "input",
                        "value": "3",
                        "type": "Number",
                    },
                    {
                        "key": "input2",
                        "value_from": "input",
                        "value": "4",
                        "type": "Number",
                    },
                ],
                "output_params": [
                    {
                        "key": "output",
                        "type": "Number",
                        "desc": "the sum of two inputs",
                    },
                ],
            },
            "type": "Script",
            "id": self.node_id,
            "name": self.node_name,
        }

        # Create script node
        script_node = ScriptNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=fail_branch_kwargs,
            glb_custom_args={},
            params={},
        )

        # Set up mock for format_output
        mock_format_output.return_value = "Formatted error message"

        # Set up sandbox mock to raise an exception
        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.run_ipython_cell.side_effect = Exception(
            "Script execution failed",
        )
        mock_sandbox.return_value.__enter__.return_value = (
            mock_sandbox_instance
        )

        # For failBranch, we need to mock the graph according to
        # source_to_target_map logic
        mock_graph = MagicMock()
        fail_source_handle = f"{self.node_id}_fail"
        error_target_handle = "error_handler_input"
        # Mock the adjacency structure as expected by the script node
        mock_graph.adj = {
            self.node_id: {
                "error_handler_node": {
                    "edge1": {
                        "source_handle": fail_source_handle,
                        "target_handle": error_target_handle,
                    },
                },
            },
        }

        # Execute the node with graph for failBranch handling
        result_generator = script_node._execute(graph=mock_graph)
        results = list(result_generator)

        # Verify error is routed to the error handler
        self.assertEqual(len(results), 1)
        output_vars = results[0]
        self.assertEqual(len(output_vars), 1)
        output_var = output_vars[0]

        # Check error output variable properties
        self.assertEqual(output_var.name, "output")
        self.assertEqual(output_var.content, "Formatted error message")
        self.assertEqual(output_var.source, self.node_id)
        self.assertEqual(output_var.targets, [error_target_handle])
        self.assertTrue(output_var.try_catch["happened"])
        self.assertEqual(output_var.try_catch["strategy"], "failBranch")


if __name__ == "__main__":
    unittest.main()
