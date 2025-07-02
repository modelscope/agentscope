# -*- coding: utf-8 -*-
"""Unit tests for variable handle node"""
import unittest
from app.workflow_engine.as_workflow.node.variable_handle import (
    VariableHandleNode,
)
from app.workflow_engine.core.node_caches.workflow_var import DataType

# pylint: disable=protected-access,unused-argument


class TestVariableHandleNode(unittest.TestCase):
    """Unit tests for VariableHandleNode"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.node_id = "VariableHandle_test"
        self.node_name = "变量处理测试"
        # Base node kwargs that will be modified for each test
        self.base_node_kwargs = {
            "id": self.node_id,
            "name": self.node_name,
            "config": {
                "node_param": {},  # Will be set per test
            },
            "type": "VariableHandle",
        }

    def test_template_type(self) -> None:
        """Test template type variable handling"""

        node_kwargs = {
            "id": self.base_node_kwargs["id"],
            "name": self.base_node_kwargs["name"],
            "type": self.base_node_kwargs["type"],
            "config": {
                "node_param": {
                    "type": "template",
                    "template_content": "This is a template content",
                },
            },
        }

        # Create node instance
        node = VariableHandleNode(
            node_id=self.node_id,
            node_kwargs=node_kwargs,
            params={},
            glb_custom_args={},
        )
        # Execute the node
        result = list(node._execute())

        # Verify the result
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 1)
        # Check the variable
        var = variables[0]
        self.assertEqual(var.name, "output")
        self.assertEqual(var.content, "This is a template content")
        self.assertEqual(var.source, self.node_id)
        self.assertEqual(var.data_type, DataType.STRING)
        self.assertEqual(var.node_type, "VariableHandle")
        self.assertEqual(var.node_name, self.node_name)
        self.assertEqual(var.output, {"output": "This is a template content"})

    def test_json_type(self) -> None:
        """Test JSON type variable handling"""  # Configure node for JSON type
        node_kwargs = {
            "id": self.base_node_kwargs["id"],
            "name": self.base_node_kwargs["name"],
            "type": self.base_node_kwargs["type"],
            "config": {
                "node_param": {
                    "type": "json",
                    "json_params": [
                        {"key": "param1", "value": "value1", "type": "String"},
                        {"key": "param2", "value": "value2", "type": "String"},
                    ],
                },
            },
        }

        # Create node instance
        node = VariableHandleNode(
            node_id=self.node_id,
            node_kwargs=node_kwargs,
            params={},
            glb_custom_args={},
        )

        # Execute the node
        result = list(node._execute())

        # Verify the result
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 2)

        # Check first variable
        var1 = variables[0]
        self.assertEqual(var1.name, "param1")
        self.assertEqual(
            var1.content,
            "value1",
        )  # Note: This seems to be a bug in original
        # code
        self.assertEqual(var1.data_type, DataType.STRING)

        # Check second variable
        var2 = variables[1]
        self.assertEqual(var2.name, "param2")
        self.assertEqual(var2.content, "value2")  # Same bug
        # Check output contains both params
        expected_output = {"param1": "value1", "param2": "value2"}
        self.assertEqual(var1.output, expected_output)
        self.assertEqual(var2.output, expected_output)

    def test_group_type_first_not_null(self) -> None:
        """Test group type with firstNotNull strategy"""
        # Configure node for group type with firstNotNull strategy
        node_kwargs = {
            "id": self.base_node_kwargs["id"],
            "name": self.base_node_kwargs["name"],
            "type": self.base_node_kwargs["type"],
            "config": {
                "node_param": {
                    "type": "group",
                    "groups": [
                        {
                            "group_id": "group1",
                            "group_name": "Group1",
                            "variables": [
                                {"id": "var1", "value": None},
                                {"id": "var2", "value": "second_value"},
                                {"id": "var3", "value": "third_value"},
                            ],
                        },
                        {
                            "group_id": "group2",
                            "group_name": "Group2",
                            "variables": [
                                {"id": "var1", "value": "first_value"},
                                {"id": "var2", "value": None},
                            ],
                        },
                    ],
                },
            },
        }

        # Create node instance
        node = VariableHandleNode(
            node_id=self.node_id,
            node_kwargs=node_kwargs,
            params={"group_strategy": "firstNotNull"},
            glb_custom_args={},
        )
        # Execute the node
        result = list(node._execute())

        # Verify the result
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 2)
        # Check Group1 - should take the first non-null value (second_value)
        var1 = variables[0]
        self.assertEqual(var1.name, "Group1")
        self.assertEqual(var1.content, "second_value")
        # Check Group2 - should take the first non-null value (first_value)
        var2 = variables[1]
        self.assertEqual(var2.name, "Group2")
        self.assertEqual(var2.content, "first_value")

        # Check output contains both groups
        expected_output = {"Group1": "second_value", "Group2": "first_value"}
        self.assertEqual(var1.output, expected_output)
        self.assertEqual(var2.output, expected_output)

    def test_group_type_last_not_null(self) -> None:
        """Test group type with lastNotNull strategy"""
        # Configure node for group type with lastNotNull strategy
        node_kwargs = dict(self.base_node_kwargs)
        node_kwargs = {
            "id": self.node_id,
            "name": self.node_name,
            "config": {
                "node_param": {
                    "type": "group",
                    "groups": [
                        {
                            "group_id": "group1",
                            "group_name": "Group1",
                            "variables": [
                                {"id": "var1", "value": "first_value"},
                                {"id": "var2", "value": None},
                                {"id": "var3", "value": "third_value"},
                            ],
                        },
                        {
                            "group_id": "group2",
                            "group_name": "Group2",
                            "variables": [
                                {"id": "var1", "value": "first_value"},
                                {"id": "var2", "value": "second_value"},
                            ],
                        },
                    ],
                },  # Will be set per test
            },
            "type": "VariableHandle",
        }

        # Create node instance
        node = VariableHandleNode(
            node_id=self.node_id,
            node_kwargs=node_kwargs,
            params={"group_strategy": "lastNotNull"},
            glb_custom_args={},
        )
        # Execute the node
        result = list(node._execute())

        # Verify the result
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 2)
        # Check Group1 - should take the last non-null value (third_value)
        var1 = variables[0]
        self.assertEqual(var1.name, "Group1")
        self.assertEqual(var1.content, "third_value")

        # Check Group2 - should take the last non-null value (second_value)
        var2 = variables[1]
        self.assertEqual(var2.name, "Group2")
        self.assertEqual(var2.content, "second_value")

        # Check output contains both groups
        expected_output = {"Group1": "third_value", "Group2": "second_value"}
        self.assertEqual(var1.output, expected_output)
        self.assertEqual(var2.output, expected_output)

    def test_all_null_values_in_group(self) -> None:
        """Test group type with all null values"""
        # Configure node with a group containing all null values
        node_kwargs = {
            "id": self.node_id,
            "name": self.node_name,
            "config": {
                "node_param": {
                    "type": "group",
                    "groups": [
                        {
                            "group_id": "nullgroup",
                            "group_name": "NullGroup",
                            "variables": [
                                {"id": "var1", "value": None},
                                {"id": "var2", "value": None},
                            ],
                        },
                    ],
                },  # Will be set per test
            },
            "type": "VariableHandle",
        }

        # Create node instance
        node = VariableHandleNode(
            node_id=self.node_id,
            node_kwargs=node_kwargs,
            params={"group_strategy": "firstNotNull"},
            glb_custom_args={},
        )

        # Execute the node
        result = list(node._execute())

        # Verify the result
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 1)

        # Check that content is empty string when all values are null
        # (None is converted to empty string in WorkflowVariable)
        var = variables[0]
        self.assertEqual(var.name, "NullGroup")
        self.assertEqual(
            var.content,
            "",
        )  # Changed from assertIsNone to assertEqual

        # Check that in the output dictionary, the value is still None
        self.assertEqual(var.output, {"NullGroup": None})

    def test_unsupported_type(self) -> None:
        """Test error handling for unsupported type"""
        # Configure node with unsupported type
        node_kwargs = {
            "id": self.node_id,
            "name": self.node_name,
            "config": {
                "node_param": {
                    "type": "unsupported",
                },  # Will be set per test
            },
            "type": "VariableHandle",
        }

        # Create node instance
        node = VariableHandleNode(
            node_id=self.node_id,
            node_kwargs=node_kwargs,
            params={},
            glb_custom_args={},
        )
        # Execute the node and verify it raises an exception
        with self.assertRaises(Exception) as context:
            list(node._execute())

        self.assertTrue(
            "Unsupported type: unsupported" in str(context.exception),
        )

    def test_invalid_group_strategy(self) -> None:
        """Test invalid group strategy"""

        # Configure node for group type
        node_kwargs = {
            "id": self.node_id,
            "name": self.node_name,
            "config": {
                "node_param": {
                    "type": "group",
                    "groups": [
                        {
                            "group_id": "group1",
                            "group_name": "Group1",
                            "variables": [
                                {"id": "var1", "value": "value1"},
                            ],
                        },
                    ],
                },  # Will be set per test
            },
            "type": "VariableHandle",
        }
        # Create node instance with invalid strategy
        node = VariableHandleNode(
            node_id=self.node_id,
            node_kwargs=node_kwargs,
            params={"group_strategy": "invalidStrategy"},
            glb_custom_args={},
        )
        # Execute the node and verify it raises an assertion error
        with self.assertRaises(AssertionError) as context:
            list(node._execute())

        self.assertTrue(
            "group_strategy must be firstNotNull or lastNotNull"
            in str(
                context.exception,
            ),
        )


if __name__ == "__main__":
    unittest.main()
