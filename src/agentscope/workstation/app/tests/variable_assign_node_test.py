# -*- coding: utf-8 -*-
"""Unit tests for variable assign node"""
import unittest

from app.workflow_engine.as_workflow.node.variable_assign import (
    VariableAssignNode,
)
from app.workflow_engine.core.node_caches.workflow_var import (
    DataType,
)

# pylint: disable=protected-access,unused-argument


class TestVariableAssignNode(unittest.TestCase):
    """Unit tests for VariableAssignNode"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.node_id = "VariableAssign_kCso"
        self.node_name = "VariableAssign1"
        # Configure node kwargs based on your workflow config
        self.node_kwargs = {
            "id": self.node_id,
            "name": self.node_name,
            "config": {
                "node_param": {
                    "inputs": [
                        {
                            "id": "sG6u",
                            "left": {
                                "value_from": "refer",
                                "value": "${session.s_v}",
                                "type": "String",
                            },
                            "right": {
                                "value_from": "refer",
                                "value": "${Start_Ye2c.aaa}",
                                "type": "String",
                            },
                        },
                        {
                            "id": "w3Za",
                            "left": {
                                "value_from": "refer",
                                "type": "String",
                                "value": "${session.s_v_2}",
                            },
                            "right": {
                                "value_from": "input",
                                "type": "String",
                                "value": "asg22222",
                            },
                        },
                    ],
                },
            },
            "type": "VariableAssign",
        }

        # Create the node instance
        self.node = VariableAssignNode(
            node_id=self.node_id,
            node_kwargs=self.node_kwargs,
            params={},
            glb_custom_args={},
        )

    def test_basic_variable_assignment(self) -> None:
        """Test basic variable assignment functionality"""
        # Execute the node
        result = list(self.node._execute())

        # Verify results
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 2)
        # Check first variable
        var1 = variables[0]
        self.assertEqual(var1.name, "session.s_v")
        self.assertEqual(var1.content, "${Start_Ye2c.aaa}")
        self.assertEqual(var1.data_type, DataType.STRING)
        self.assertEqual(var1.node_type, "VariableAssign")
        self.assertEqual(var1.node_name, self.node_name)

        # Check second variable
        var2 = variables[1]
        self.assertEqual(var2.name, "session.s_v_2")
        self.assertEqual(var2.content, "asg22222")
        self.assertEqual(var2.data_type, DataType.STRING)

    def test_number_variable_assignment(self) -> None:
        """Test number variable assignment"""

        # Create a new node instance for number variable
        number_node_kwargs = {
            "id": "VariableAssign_Umt6",
            "name": "VariableAssign2",
            "config": {
                "node_param": {
                    "inputs": [
                        {
                            "id": "Kjd5",
                            "left": {
                                "value_from": "refer",
                                "value": "${session.s_v_3}",
                                "type": "Number",
                            },
                            "right": {
                                "value_from": "input",
                                "value": "555555",
                                "type": "Number",
                            },
                        },
                    ],
                },
            },
            "type": "VariableAssign",
        }

        number_node = VariableAssignNode(
            node_id="VariableAssign_Umt6",
            node_kwargs=number_node_kwargs,
            params={},
            glb_custom_args={},
        )

        # Execute the node
        result = list(number_node._execute())

        # Verify results
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 1)
        # Check variable
        var = variables[0]
        self.assertEqual(var.name, "session.s_v_3")
        self.assertEqual(var.content, "555555")  # Note: Still stored as string
        self.assertEqual(var.data_type, DataType.STRING)
        self.assertEqual(var.node_type, "VariableAssign")
        self.assertEqual(var.node_name, "VariableAssign2")

    def test_no_matching_inputs(self) -> None:
        """Test behavior when form inputs don't match value inputs"""
        # Create a node with specific form inputs
        mismatch_node_kwargs = {
            "id": "VariableAssign_Test",
            "name": "测试节点",
            "config": {
                "node_param": {
                    "inputs": [
                        {
                            "id": "form_id",  # This ID won't match any value
                            "left": {
                                "value_from": "refer",
                                "value": "${session.test_var}",
                                "type": "String",
                            },
                        },
                    ],
                },
            },
            "type": "VariableAssign",
        }  # Create node instance
        mismatch_node = VariableAssignNode(
            node_id="VariableAssign_Test",
            node_kwargs=mismatch_node_kwargs,
            params={},
            glb_custom_args={},
        )

        # Completely override sys_args to ensure we have full control
        mismatch_node.sys_args = {
            "node_param": {
                "inputs": [
                    {
                        "id": "different_id",
                        # Different ID that won't match form_id
                        "left": {"value": "${session.different_var}"},
                        "right": {"value": "test_value"},
                    },
                ],
            },
        }

        # Execute the node
        result = list(mismatch_node._execute())

        # Verify no variables were created (or change expectation if needed)
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 0)  # Should be0 if no match found

    def test_empty_inputs(self) -> None:
        """Test behavior with empty inputs list"""
        empty_node_kwargs = {
            "id": "VariableAssign_Empty",
            "name": "空节点",
            "config": {
                "node_param": {
                    "inputs": [],
                },
            },
            "type": "VariableAssign",
        }
        empty_node = VariableAssignNode(
            node_id="VariableAssign_Empty",
            node_kwargs=empty_node_kwargs,
            params={},
            glb_custom_args={},
        )
        # Execute the node
        result = list(empty_node._execute())

        # Verify no variables were created
        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 0)


if __name__ == "__main__":
    unittest.main()
