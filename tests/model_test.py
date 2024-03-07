# -*- coding: utf-8 -*-
"""
Unit tests for model wrapper classes and functions
"""

from typing import Any
import unittest
from unittest.mock import patch, MagicMock


from agentscope.models import (
    ModelResponse,
    ModelWrapperBase,
    OpenAIChatWrapper,
    PostAPIModelWrapperBase,
    _get_model_wrapper,
    read_model_configs,
    load_model_by_config_name,
    clear_model_configs,
)


class TestModelWrapperSimple(ModelWrapperBase):
    """A simple model wrapper class for test usage"""

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        return ModelResponse(text=self.config_name)


class BasicModelTest(unittest.TestCase):
    """Test cases for basic model wrappers"""

    def test_model_registry(self) -> None:
        """Test the automatic registration mechanism of model wrapper."""
        # get model wrapper class by class name
        self.assertEqual(
            _get_model_wrapper(model_type="TestModelWrapperSimple"),
            TestModelWrapperSimple,
        )
        # get model wrapper class by model type
        self.assertEqual(
            _get_model_wrapper(model_type="openai"),
            OpenAIChatWrapper,
        )
        # return PostAPIModelWrapperBase if model_type is not supported
        self.assertEqual(
            _get_model_wrapper(model_type="unknown_model_wrapper"),
            PostAPIModelWrapperBase,
        )

    @patch("loguru.logger.warning")
    def test_load_model_configs(self, mock_logging: MagicMock) -> None:
        """Test to load model configs"""
        configs = [
            {
                "model_type": "openai",
                "config_name": "gpt-4",
                "model_name": "gpt-4",
                "api_key": "xxx",
                "organization": "xxx",
                "generate_args": {"temperature": 0.5},
            },
            {
                "model_type": "post_api",
                "config_name": "my_post_api",
                "api_url": "https://xxx",
                "headers": {},
                "json_args": {},
            },
        ]
        # load a list of configs
        read_model_configs(configs=configs, clear_existing=True)
        model = load_model_by_config_name("gpt-4")
        self.assertEqual(model.config_name, "gpt-4")
        model = load_model_by_config_name("my_post_api")
        self.assertEqual(model.config_name, "my_post_api")
        self.assertRaises(
            ValueError,
            load_model_by_config_name,
            "non_existent_id",
        )

        # load a single config
        read_model_configs(configs=configs[0], clear_existing=True)
        model = load_model_by_config_name("gpt-4")
        self.assertEqual(model.config_name, "gpt-4")
        self.assertRaises(ValueError, load_model_by_config_name, "my_post_api")

        # load model with the same id
        read_model_configs(configs=configs[0], clear_existing=False)
        mock_logging.assert_called_once_with(
            "config_name [gpt-4] already exists.",
        )

        read_model_configs(
            configs={
                "model_type": "TestModelWrapperSimple",
                "config_name": "test_model_wrapper",
                "args": {},
            },
        )
        test_model = load_model_by_config_name("test_model_wrapper")
        response = test_model()
        self.assertEqual(response.text, "test_model_wrapper")
        clear_model_configs()
        self.assertRaises(
            ValueError,
            load_model_by_config_name,
            "test_model_wrapper",
        )
