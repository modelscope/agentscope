# -*- coding: utf-8 -*-
import unittest
from typing import Callable
from unittest.mock import patch, MagicMock, PropertyMock

from app.workflow_engine.as_workflow.node.llm import LLMNode
from app.workflow_engine.core.node_caches.workflow_var import DataType


class TestLLMNode(unittest.TestCase):
    """Unit test for LLM node"""

    def setUp(self) -> None:
        """Set up"""
        self.node_id = "test_llm_node"
        self.node_name = "Test LLM Node"

        self.node_kwargs = {
            "id": "LLM_RgEL",
            "name": "LLM1",
            "config": {
                "input_params": [],
                "output_params": [
                    {
                        "key": "output",
                        "type": "String",
                        "desc": "text output",
                    },
                ],
                "node_param": {
                    "sys_prompt_content": "You are a helpful assistant.",
                    "prompt_content": "Tell me about Python.",
                    "short_memory": {
                        "enable": False,
                        "type": "self",
                        "window": 3,
                        "param": {
                            "key": "historyList",
                            "type": "Array<String>",
                            "value_from": "refer",
                        },
                    },
                    "model_config": {
                        "model_id": "qwen-max",
                        "model_name": "",
                        "mode": "chat",
                        "provider": "Tongyi",
                        "params": [],
                        "vision_config": {
                            "enable": False,
                            "params": [
                                {
                                    "key": "imageContent",
                                    "value_from": "refer",
                                    "type": "File",
                                },
                            ],
                        },
                    },
                    "retry_config": {
                        "retry_enabled": True,
                        "max_retries": 3,
                        "retry_interval": 500,
                    },
                    "try_catch_config": {
                        "strategy": "noop",
                        "default_values": [
                            {
                                "key": "output",
                                "type": "String",
                                "desc": "文本输出",
                                "value": "Default response",
                            },
                        ],
                    },
                },
            },
            "type": "LLM",
        }

        # Create mock response with streaming capability
        self.mock_response = MagicMock()
        self.mock_response.text = "Python is a programming language."

        # Mock the stream property to yield chunks
        stream_mock = PropertyMock(
            return_value=[
                ("chunk1", "Python"),
                ("chunk2", " is a"),
                ("chunk3", " programming language."),
            ],
        )
        type(self.mock_response).stream = stream_mock

        self.mock_model = MagicMock(return_value=self.mock_response)

        self.node = LLMNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )

    @patch("app.workflow_engine.as_workflow.node.llm.get_model_instance")
    @patch("app.workflow_engine.as_workflow.node.llm.ModelWrapperBase")
    def test_basic_execution(
        self,
        mock_model_wrapper_base: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test basic execution"""
        mock_get_model_instance.return_value = self.mock_model

        # Setup mock for register_save_model_invocation_hook to capture the
        # callback
        hook_callback = None

        def mock_register_hook(hook_name: str, callback: Callable) -> None:
            nonlocal hook_callback
            hook_callback = callback

        mock_model_wrapper_base.register_save_model_invocation_hook.side_effect = (  # noqa
            mock_register_hook
        )

        # Get all yields from the generator
        result_generator = self.node._execute()

        # Simulate first three streamed chunks
        results = []
        for _ in range(3):
            results.append(next(result_generator))

        # Now simulate the model invocation being reported
        if hook_callback:
            hook_callback(
                model_wrapper=MagicMock(),
                model_invocation_id="test_id",
                timestamp="2023-01-01T12:00:00",
                arguments={},
                response={},
                usage={
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 8,
                        "total_tokens": 18,
                    },
                },
            )

        # Get the final result
        results.append(next(result_generator))

        # We should have 4 yields: 3 for streaming chunks and 1 for final
        # result
        self.assertEqual(len(results), 4)

        # Check the streaming chunks
        for i, result in enumerate(results[:3]):
            self.assertEqual(len(result), 1)
            var = result[0]
            if i == 0:
                self.assertEqual(var.content, "Python")
            elif i == 1:
                self.assertEqual(var.content, " is a")
            elif i == 2:
                self.assertEqual(var.content, " programming language.")

        # Check the final yield which contains the complete response
        final_result = results[-1]
        self.assertEqual(len(final_result), 1)
        var = final_result[0]

        self.assertEqual(var.name, "output")
        self.assertEqual(var.content, "Python is a programming language.")
        self.assertEqual(var.source, self.node_id)
        self.assertEqual(var.data_type, DataType.STRING)

        # Verify the model was called with the right messages
        self.mock_model.assert_called_once_with(
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me about Python."},
            ],
        )

        # Check token usage
        self.assertEqual(var.usages[0]["prompt_tokens"], 10)
        self.assertEqual(var.usages[0]["completion_tokens"], 8)
        self.assertEqual(var.usages[0]["total_tokens"], 18)

    @patch("app.workflow_engine.as_workflow.node.llm.get_model_instance")
    @patch("app.workflow_engine.as_workflow.node.llm.ModelWrapperBase")
    def test_short_memory_custom(
        self,
        mock_model_wrapper_base: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test custom short memory"""
        self.node.sys_args["node_param"]["short_memory"] = {
            "enable": True,
            "type": "custom",
            "param": {
                "value": [
                    {"role": "user", "content": "What is Python?"},
                    {
                        "role": "assistant",
                        "content": "Python is a programming language.",
                    },
                ],
            },
        }
        mock_get_model_instance.return_value = self.mock_model

        # Collect all results to let the generator complete
        generator = self.node._execute()
        while True:
            try:
                next(generator)
            except StopIteration:
                break

        # Verify the model was called with the right messages
        self.mock_model.assert_called_once_with(
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"},
                {
                    "role": "assistant",
                    "content": "Python is a programming language.",
                },
                {"role": "user", "content": "Tell me about Python."},
            ],
        )

    @patch("app.workflow_engine.as_workflow.node.llm.get_model_instance")
    @patch("app.workflow_engine.as_workflow.node.llm.ModelWrapperBase")
    def test_short_memory_self(
        self,
        mock_model_wrapper_base: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test self short memory"""
        self.node.sys_args["node_param"]["short_memory"] = {
            "enable": True,
            "type": "self",
            "window": 2,
        }
        global_cache = {
            "memory": [
                {
                    "status": {
                        "inter_results": {
                            self.node_id: {
                                "results": [
                                    {
                                        "input": [
                                            {"content": "What is Python?"},
                                        ],
                                        "content": "Python is a programming"
                                        " language.",
                                    },
                                ],
                            },
                        },
                    },
                },
                {
                    "status": {
                        "inter_results": {
                            self.node_id: {
                                "results": [
                                    {
                                        "input": [
                                            {"content": "Who created Python?"},
                                        ],
                                        "content": "Guido van Rossum created Python.",  # noqa
                                    },
                                ],
                            },
                        },
                    },
                },
            ],
        }

        mock_get_model_instance.return_value = self.mock_model

        # Collect all results to let the generator complete
        generator = self.node._execute(global_cache=global_cache)
        while True:
            try:
                next(generator)
            except StopIteration:
                break

        expected_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"},
            {
                "role": "assistant",
                "content": "Python is a programming language.",
            },
            {"role": "user", "content": "Who created Python?"},
            {
                "role": "assistant",
                "content": "Guido van Rossum created Python.",
            },
            {"role": "user", "content": "Tell me about Python."},
        ]

        self.mock_model.assert_called_once()
        actual_messages = self.mock_model.call_args[0][0]
        self.assertEqual(actual_messages, expected_messages)

    @patch("app.workflow_engine.as_workflow.node.llm.get_model_instance")
    @patch("app.workflow_engine.as_workflow.node.llm.ModelWrapperBase")
    def test_error_handling_noop(
        self,
        mock_model_wrapper_base: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test noop error handle"""
        mock_model = MagicMock(side_effect=Exception("Model error"))
        mock_get_model_instance.return_value = mock_model

        try:
            list(self.node._execute())
            self.fail("Expected Exception to be raised")
        except Exception as e:
            self.assertIn("Model error", str(e))

    @patch("app.workflow_engine.as_workflow.node.llm.get_model_instance")
    @patch("app.workflow_engine.as_workflow.node.llm.ModelWrapperBase")
    def test_error_handling_default_value(
        self,
        mock_model_wrapper_base: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test default value error handle"""
        self.node.sys_args["node_param"]["try_catch_config"] = {
            "strategy": "defaultValue",
            "default_values": [{"key": "output", "value": "Default response"}],
        }

        with patch.object(
            LLMNode,
            "build_var_str",
            return_value="Default response",
        ):
            mock_model = MagicMock(side_effect=Exception("Model error"))
            mock_get_model_instance.return_value = mock_model
            result = list(self.node._execute())

            self.assertEqual(len(result), 1)
            variables = result[0]
            self.assertEqual(len(variables), 1)
            var = variables[0]

            self.assertEqual(var.content, "Default response")
            self.assertEqual(var.data_type, DataType.STRING)
            self.assertTrue(var.try_catch["happened"])
            self.assertEqual(var.try_catch["strategy"], "failBranch")

    @patch("app.workflow_engine.as_workflow.node.llm.get_model_instance")
    @patch("app.workflow_engine.as_workflow.node.llm.format_output")
    @patch("app.workflow_engine.as_workflow.node.llm.ModelWrapperBase")
    def test_error_handling_fail_branch(
        self,
        mock_model_wrapper_base: MagicMock,
        mock_format_output: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test failBranch error handling strategy"""
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

        mock_model = MagicMock(side_effect=Exception("Model error"))
        mock_get_model_instance.return_value = mock_model
        mock_format_output.return_value = "Formatted error: Model error"

        result = list(self.node._execute(graph=mock_graph))

        self.assertEqual(len(result), 1)
        variables = result[0]
        self.assertEqual(len(variables), 1)
        var = variables[0]

        self.assertEqual(var.name, "output")
        self.assertEqual(var.content, "Formatted error: Model error")
        self.assertEqual(var.targets, ["target_node"])
        self.assertEqual(var.data_type, DataType.STRING)
        self.assertTrue(var.try_catch["happened"])
        self.assertEqual(var.try_catch["strategy"], "failBranch")


if __name__ == "__main__":
    unittest.main()
