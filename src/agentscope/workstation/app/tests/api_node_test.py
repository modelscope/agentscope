# -*- coding: utf-8 -*-
import json
import unittest
from unittest.mock import patch, MagicMock

from app.workflow_engine.as_workflow.node.api import APINode, AuthTypeEnum
from app.workflow_engine.as_workflow.node.common.make_request import BearerAuth
from app.workflow_engine.core.node_caches.workflow_var import DataType


class TestAPINode(unittest.TestCase):
    """Unit tests for APINode class."""

    def setUp(self) -> None:
        """Set up before tests."""
        self.node_id = "test_api_node"
        self.node_name = "Test API Node"
        self.node_kwargs = {
            "id": "API_test",
            "name": "APInode",
            "config": {
                "input_params": [],
                "output_params": [
                    {
                        "key": "output",
                        "type": "String",
                        "desc": "API output",
                    },
                ],
                "node_param": {
                    "url": "https://api.example.com/test",
                    "method": "post",
                    "headers": [
                        {"key": "Content-Type", "value": "application/json"},
                    ],
                    "params": [{"key": "param1", "value": "value1"}],
                    "body": {
                        "type": "json",
                        "data": {"test": "data"},
                    },
                    "authorization": {
                        "auth_type": "NoAuth",
                        "auth_config": {},
                    },
                    "timeout": {
                        "connect": 5,
                        "read": 10,
                        "write": 10,
                    },
                    "retry_config": {
                        "retry_enabled": True,
                        "max_retries": 3,
                        "retry_interval": 500,
                    },
                    "try_catch_config": {
                        "strategy": "noop",
                    },
                },
            },
            "type": "API",
        }

        self.node = APINode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )

        self.mock_response = json.dumps(
            {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "url": "https://api.example.com/test",
                "history": [],
                "cookies": {},
                "body": {"result": "success"},
            },
        )

    @patch("app.workflow_engine.as_workflow.node.api.make_request")
    def test_basic_execution(self, mock_make_request: MagicMock) -> None:
        """Test basic API request execution."""
        mock_make_request.return_value = self.mock_response
        result = list(self.node._execute())

        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 1)
        var = variables[0]

        self.assertEqual(var.name, "output")
        self.assertEqual(var.content, self.mock_response)
        self.assertEqual(var.source, self.node_id)
        self.assertEqual(var.data_type, DataType.STRING)

        mock_make_request.assert_called_once_with(
            url="https://api.example.com/test",
            method="post",
            auth=None,
            headers={"Content-Type": "application/json"},
            params={"param1": "value1"},
            body_type="json",
            body={"test": "data"},
            timeout_config={"connect": 5, "read": 10, "write": 10},
            max_retries=3,
            retry_delay=500,
        )

    @patch("app.workflow_engine.as_workflow.node.api.make_request")
    def test_basic_auth(self, mock_make_request: MagicMock) -> None:
        """Test basic authentication."""
        self.node.sys_args["node_param"]["authorization"] = {
            "auth_type": AuthTypeEnum.BASIC_AUTH.value,
            "auth_config": {
                "username": "testuser",
                "password": "testpass",
            },
        }
        mock_make_request.return_value = self.mock_response
        list(self.node._execute())

        call_args = mock_make_request.call_args[1]
        self.assertEqual(call_args["auth"], ("testuser", "testpass"))

    @patch("app.workflow_engine.as_workflow.node.api.make_request")
    def test_bearer_auth(self, mock_make_request: MagicMock) -> None:
        """Test Bearer token authentication."""
        self.node.sys_args["node_param"]["authorization"] = {
            "auth_type": AuthTypeEnum.BEARER_AUTH.value,
            "auth_config": {
                "value": "token123",
            },
        }
        mock_make_request.return_value = self.mock_response
        list(self.node._execute())

        call_args = mock_make_request.call_args[1]
        self.assertIsInstance(call_args["auth"], BearerAuth)
        self.assertEqual(call_args["auth"].token, "token123")

    @patch("app.workflow_engine.as_workflow.node.api.make_request")
    def test_json_response_as_object(
        self,
        mock_make_request: MagicMock,
    ) -> None:
        """Test JSON response returned as Object."""
        self.node.sys_args["output_params"][0]["type"] = "Object"
        mock_make_request.return_value = self.mock_response
        result = list(self.node._execute())

        variables = result[0]
        var = variables[0]

        self.assertEqual(var.data_type, DataType.OBJECT)
        self.assertEqual(var.content, json.loads(self.mock_response))

    @patch("app.workflow_engine.as_workflow.node.api.make_request")
    def test_error_handling_noop(self, mock_make_request: MagicMock) -> None:
        """Test noop error handling strategy."""
        mock_make_request.side_effect = ValueError(
            '{"status_code":404, "error": "Not Found"}',
        )

        with self.assertRaises(ValueError) as context:
            list(self.node._execute())

        self.assertIn("Not Found", str(context.exception))

    @patch("app.workflow_engine.as_workflow.node.api.make_request")
    def test_error_handling_default_value(
        self,
        mock_make_request: MagicMock,
    ) -> None:
        """Test defaultValue error handling strategy."""
        self.node.sys_args["node_param"]["try_catch_config"] = {
            "strategy": "defaultValue",
            "default_values": [{"key": "result", "value": "default"}],
        }
        mock_make_request.side_effect = ValueError(
            '{"status_code": 404, "error": "Not Found"}',
        )
        result = list(self.node._execute())

        variables = result[0]
        self.assertEqual(len(variables), 1)
        var = variables[0]

        self.assertEqual(var.name, "result")
        self.assertEqual(var.content, "default")
        self.assertEqual(var.data_type, DataType.STRING)
        self.assertTrue(var.try_catch["happened"])
        self.assertEqual(var.try_catch["strategy"], "defaultValue")

    @patch("app.workflow_engine.as_workflow.node.api.make_request")
    def test_error_handling_fail_branch(
        self,
        mock_make_request: MagicMock,
    ) -> None:
        """Test failBranch error handling strategy."""
        self.node.sys_args["node_param"]["try_catch_config"] = {
            "strategy": "failBranch",
        }

        mock_graph = MagicMock()
        mock_graph.adj = {
            self.node_id: {
                "target_node": {
                    "edge1": {
                        "source_handle": f"{self.node_id}_fail",
                        "target": "target_node",
                    },
                },
            },
        }

        error_msg = '{"status_code": 404, "error": "Not Found"}'
        mock_make_request.side_effect = ValueError(error_msg)
        result = list(self.node._execute(graph=mock_graph))

        variables = result[0]
        self.assertEqual(len(variables), 1)
        var = variables[0]

        self.assertEqual(var.name, "output")
        self.assertEqual(var.targets, ["target_node"])
        self.assertEqual(var.data_type, DataType.STRING)
        self.assertTrue(var.try_catch["happened"])
        self.assertEqual(var.try_catch["strategy"], "failBranch")

    @patch("app.workflow_engine.as_workflow.node.api.make_request")
    def test_form_data_body(self, mock_make_request: MagicMock) -> None:
        """Test form-data body type."""
        self.node.sys_args["node_param"]["body"] = {
            "type": "form-data",
            "data": [
                {"key": "field1", "value": "value1"},
                {"key": "field2", "value": "value2"},
            ],
        }
        mock_make_request.return_value = self.mock_response
        list(self.node._execute())

        call_args = mock_make_request.call_args[1]
        self.assertEqual(call_args["body_type"], "data")
        self.assertEqual(
            call_args["body"],
            {"field1": "value1", "field2": "value2"},
        )


if __name__ == "__main__":
    unittest.main()
