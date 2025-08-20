# -*- coding: utf-8 -*-
"""Unit tests for ClassifierNode."""
import unittest
from unittest.mock import patch, MagicMock

from app.workflow_engine.as_workflow.node.classifier import ClassifierNode

# mypy: disable-error-code=index
# pylint: disable=protected-access,unused-argument


class TestClassifierNode(unittest.TestCase):
    """Unit test for ClassifierNode"""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.node_id = "Classifier_v2LM"
        self.node_name = "Classifier1"
        self.node_kwargs = {
            "config": {
                "node_param": {
                    "conditions": [
                        {"id": "default", "subject": ""},
                        {"id": "kJSv", "subject": "animal"},
                        {"id": "qBGQ", "subject": "plant"},
                    ],
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
                    "short_memory": {
                        "enabled": True,
                        "type": "self",
                        "round": 3,
                        "param": {
                            "key": "historyList",
                            "type": "Array<String>",
                            "value_from": "refer",
                        },
                    },
                    "instruction": "Please determine the category of the "
                    "input.",
                    "mode_switch": "efficient",
                    "multi_decision": False,
                },
                "input_params": [
                    {
                        "key": "input",
                        "value_from": "refer",
                        "type": "String",
                        "value": "pig",
                    },
                ],
                "output_params": [
                    {
                        "key": "subject",
                        "type": "String",
                        "desc": "target subject",
                    },
                    {
                        "key": "thought",
                        "type": "String",
                        "desc": "thinking progress",
                    },
                ],
            },
            "type": "Classifier",
            "id": "Classifier_v2LM",
            "name": "Classifier1",
        }

        self.node = ClassifierNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )

        # Create mock graph based on real config
        self.mock_graph = MagicMock()
        self.mock_graph.adj = {
            self.node_id: {
                "End_YuJ2": {
                    "Classifier_v2LM-Classifier_v2LM_default-End_YuJ2"
                    "-End_YuJ2": {
                        "source_handle": f"{self.node_id}_default",
                        # default condition
                        "target_handle": "End_YuJ2",
                    },
                    "Classifier_v2LM-Classifier_v2LM_kJSv-End_YuJ2-End_YuJ2": {
                        "source_handle": f"{self.node_id}_kJSv",
                        # animal condition
                        "target_handle": "End_YuJ2",
                    },
                    "Classifier_v2LM-Classifier_v2LM_qBGQ-End_YuJ2-End_YuJ2": {
                        "source_handle": f"{self.node_id}_qBGQ",
                        # plant condition
                        "target_handle": "End_YuJ2",
                    },
                },
            },
        }

    @patch(
        "app.workflow_engine.as_workflow.node.classifier.get_model_instance",
    )
    @patch(
        "app.workflow_engine.as_workflow.node.classifier"
        ".RegexTaggedContentParser",
    )
    @patch.object(ClassifierNode, "_build_prompt")
    def test_basic_execution(
        self,
        mock_build_prompt: MagicMock,
        mock_parser_class: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test basic execution of ClassifierNode."""
        # Mock prompt builder
        mock_build_prompt.return_value = (
            "Classification prompt: {"
            "candidates}, {input_question}, "
            "{instruction}"
        )

        # Mock parser
        mock_parser_instance = MagicMock()
        # Using index 0 to represent "animal"
        mock_parser_instance.parse.return_value.parsed = {
            "Think": "This is a pig, which is an animal.",
            "Decision": [0],
        }
        mock_parser_class.return_value = mock_parser_instance

        # Mock model instance and response
        mock_model = MagicMock()
        mock_model.format.return_value = [
            {"role": "system", "content": "mocked system prompt"},
        ]
        mock_response = MagicMock()
        mock_response.raw = MagicMock()
        mock_response.raw.usage = MagicMock()
        mock_response.raw.usage.input_tokens = 10
        mock_response.raw.usage.output_tokens = 5
        mock_response.raw.usage.total_tokens = 15
        mock_model.return_value = mock_response
        mock_get_model_instance.return_value = mock_model

        # Execute the method with mock graph
        result_generator = self.node._execute(
            graph=self.mock_graph,
            global_cache={"memory": []},
        )
        results = list(result_generator)

        # Verify results
        self.assertEqual(len(results), 1)
        workflow_vars = results[0]
        self.assertEqual(len(workflow_vars), 2)  # Check thought variable
        thought_var = workflow_vars[0]
        self.assertEqual(thought_var.name, "thought")
        self.assertEqual(
            thought_var.content,
            "This is a pig, which is an animal.",
        )
        self.assertEqual(thought_var.source, self.node_id)
        self.assertEqual(
            thought_var.targets,
            ["End_YuJ2"],
        )  # All conditions target End_YuJ2

        # Check subject variable
        subject_var = workflow_vars[1]
        self.assertEqual(subject_var.name, "subject")
        self.assertEqual(subject_var.content, "animal")
        self.assertEqual(subject_var.source, self.node_id)
        self.assertEqual(
            subject_var.targets,
            ["End_YuJ2"],
        )  # All conditions target End_YuJ2

        # Verify model usage metrics
        self.assertEqual(thought_var.usages[0]["prompt_tokens"], 10)
        self.assertEqual(thought_var.usages[0]["completion_tokens"], 5)
        self.assertEqual(thought_var.usages[0]["total_tokens"], 15)

    @patch(
        "app.workflow_engine.as_workflow.node.classifier.get_model_instance",
    )
    @patch(
        "app.workflow_engine.as_workflow.node.classifier"
        ".RegexTaggedContentParser",
    )
    @patch.object(ClassifierNode, "_build_prompt")
    def test_custom_short_memory(
        self,
        mock_build_prompt: MagicMock,
        mock_parser_class: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test execution with custom short memory enabled."""
        # Update node param to enable custom short memory
        self.node_kwargs["config"]["node_param"]["short_memory"] = {
            "enabled": True,
            "type": "custom",
            "param": {
                "value": [
                    {"role": "user", "content": "What is an apple?"},
                    {
                        "role": "assistant",
                        "content": "An apple is a fruit, classified as a "
                        "plant.",
                    },
                ],
            },
        }

        # Create classifier node with updated parameters
        node = ClassifierNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )

        # Mock dependencies
        mock_build_prompt.return_value = "Prompt with short memory"

        # Mock parser
        mock_parser_instance = MagicMock()  # Using index0 to represent
        # "animal"
        mock_parser_instance.parse.return_value.parsed = {
            "Think": "Unlike an apple, a pig is an animal.",
            "Decision": [0],
        }
        mock_parser_class.return_value = mock_parser_instance

        # Mock model instance and response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.raw = MagicMock()
        mock_response.raw.usage = MagicMock()
        mock_response.raw.usage.input_tokens = 15
        mock_response.raw.usage.output_tokens = 8
        mock_response.raw.usage.total_tokens = 23
        mock_model.return_value = mock_response
        mock_get_model_instance.return_value = mock_model

        # Execute the method with mock graph
        result_generator = node._execute(
            graph=self.mock_graph,
            global_cache={"memory": []},
        )
        results = list(result_generator)

        # Verify results
        workflow_vars = results[0]
        subject_var = workflow_vars[1]
        self.assertEqual(subject_var.content, "animal")
        self.assertEqual(
            subject_var.targets,
            ["End_YuJ2"],
        )  # All conditions target End_YuJ2

        # Verify usage metrics
        self.assertEqual(subject_var.usages[0]["prompt_tokens"], 15)
        self.assertEqual(subject_var.usages[0]["completion_tokens"], 8)
        self.assertEqual(subject_var.usages[0]["total_tokens"], 23)

    @patch(
        "app.workflow_engine.as_workflow.node.classifier.get_model_instance",
    )
    @patch(
        "app.workflow_engine.as_workflow.node.classifier"
        ".RegexTaggedContentParser",
    )
    @patch.object(ClassifierNode, "_build_prompt")
    def test_self_short_memory(
        self,
        mock_build_prompt: MagicMock,
        mock_parser_class: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test execution with self short memory enabled."""  # Update node
        # param to enable self short memory
        self.node_kwargs["config"]["node_param"]["short_memory"][
            "enabled"
        ] = True

        # Create classifier node with updated parameters
        node = ClassifierNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )

        # Mock dependencies
        mock_build_prompt.return_value = "Prompt with self memory"

        # Mock parser
        mock_parser_instance = MagicMock()  # Use index 0 to represent "animal"
        mock_parser_instance.parse.return_value.parsed = {
            "Think": "Based on history and current input, a pig is an animal.",
            "Decision": [0],
        }
        mock_parser_class.return_value = mock_parser_instance

        # Mock model instance and response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.raw = MagicMock()
        mock_response.raw.usage = MagicMock()
        mock_response.raw.usage.input_tokens = 20
        mock_response.raw.usage.output_tokens = 10
        mock_response.raw.usage.total_tokens = 30
        mock_model.return_value = mock_response
        mock_get_model_instance.return_value = mock_model
        # Create memory for global cache with node history
        memory = [
            {
                "status": {
                    "inter_results": {
                        self.node_id: {
                            "results": [
                                {
                                    "input": "apple",
                                    "content": {
                                        "thought": "Apple is a fruit, "
                                        "classified as "
                                        "plant.",
                                        "subject": ["plant"],
                                    },
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
                                    "input": "chicken",
                                    "content": {
                                        "thought": "Chicken is a poultry, "
                                        "classified as "
                                        "animal.",
                                        "subject": ["animal"],
                                    },
                                },
                            ],
                        },
                    },
                },
            },
        ]
        # Execute the method with mock graph
        result_generator = node._execute(
            graph=self.mock_graph,
            global_cache={"memory": memory},
        )
        results = list(result_generator)

        # Verify results
        workflow_vars = results[0]
        subject_var = workflow_vars[1]
        self.assertEqual(subject_var.content, "animal")
        self.assertEqual(subject_var.targets, ["End_YuJ2"])
        # Verify usage information
        self.assertEqual(subject_var.usages[0]["prompt_tokens"], 20)
        self.assertEqual(subject_var.usages[0]["completion_tokens"], 10)
        self.assertEqual(subject_var.usages[0]["total_tokens"], 30)
        # Verify parser was called correctly
        mock_parser_instance.parse.assert_called_once_with(
            mock_response,
        )

    @patch(
        "app.workflow_engine.as_workflow.node.classifier.get_model_instance",
    )
    @patch(
        "app.workflow_engine.as_workflow.node.classifier"
        ".RegexTaggedContentParser",
    )
    @patch.object(ClassifierNode, "_build_prompt")
    def test_default_condition(
        self,
        mock_build_prompt: MagicMock,
        mock_parser_class: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test execution with default condition."""
        # Mock dependencies
        mock_build_prompt.return_value = (
            "Classification prompt for default condition"
        )

        # Mock parser
        mock_parser_instance = MagicMock()
        # Use index -1 to represent "default" condition
        mock_parser_instance.parse.return_value.parsed = {
            "Think": "This input doesn't match any specific category.",
            "Decision": [-1],
        }
        mock_parser_class.return_value = mock_parser_instance

        # Mock model instance and response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.raw = MagicMock()
        mock_response.raw.usage = MagicMock()
        mock_response.raw.usage.input_tokens = 12
        mock_response.raw.usage.output_tokens = 6
        mock_response.raw.usage.total_tokens = 18
        mock_model.return_value = mock_response
        mock_get_model_instance.return_value = mock_model
        # Execute the method with mock graph
        result_generator = self.node._execute(
            graph=self.mock_graph,
            global_cache={"memory": []},
        )
        results = list(result_generator)

        # Verify results
        workflow_vars = results[0]
        subject_var = workflow_vars[1]
        self.assertEqual(
            subject_var.content,
            "",
        )  # Default condition has empty subject
        self.assertEqual(
            subject_var.targets,
            ["End_YuJ2"],
        )  # Verify usage metrics
        self.assertEqual(subject_var.usages[0]["prompt_tokens"], 12)
        self.assertEqual(subject_var.usages[0]["completion_tokens"], 6)
        self.assertEqual(subject_var.usages[0]["total_tokens"], 18)
        # Verify parser was called correctly
        mock_parser_instance.parse.assert_called_once_with(mock_response)

    @patch(
        "app.workflow_engine.as_workflow.node.classifier.get_model_instance",
    )
    @patch(
        "app.workflow_engine.as_workflow.node.classifier"
        ".RegexTaggedContentParser",
    )
    @patch.object(ClassifierNode, "_build_prompt")
    def test_plant_condition(
        self,
        mock_build_prompt: MagicMock,
        mock_parser_class: MagicMock,
        mock_get_model_instance: MagicMock,
    ) -> None:
        """Test execution with plant condition."""  # Mock dependencies
        mock_build_prompt.return_value = (
            "Classification prompt for plant condition"
        )
        # Mock parser
        mock_parser_instance = MagicMock()
        # Use index 1 to represent "plant"
        mock_parser_instance.parse.return_value.parsed = {
            "Think": "A rose is a beautiful flower.",
            "Decision": [1],
        }
        mock_parser_class.return_value = mock_parser_instance

        # Mock model instance and response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.raw = MagicMock()
        mock_response.raw.usage = MagicMock()
        mock_response.raw.usage.input_tokens = 14
        mock_response.raw.usage.output_tokens = 7
        mock_response.raw.usage.total_tokens = 21
        mock_model.return_value = mock_response
        mock_get_model_instance.return_value = mock_model
        # Execute the method with mock graph
        result_generator = self.node._execute(
            graph=self.mock_graph,
            global_cache={"memory": []},
        )
        results = list(result_generator)

        # Verify results
        workflow_vars = results[0]
        subject_var = workflow_vars[1]
        self.assertEqual(subject_var.content, "plant")  # Plant condition
        self.assertEqual(subject_var.targets, ["End_YuJ2"])

        # Verify usage metrics
        self.assertEqual(subject_var.usages[0]["prompt_tokens"], 14)
        self.assertEqual(subject_var.usages[0]["completion_tokens"], 7)
        self.assertEqual(subject_var.usages[0]["total_tokens"], 21)

        # Verify parser was called correctly
        mock_parser_instance.parse.assert_called_once_with(mock_response)


if __name__ == "__main__":
    unittest.main()
