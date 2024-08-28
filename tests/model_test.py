# -*- coding: utf-8 -*-
"""Unit tests for model wrapper classes and functions"""
from typing import Any, Union, List, Sequence
import unittest
from unittest.mock import patch, MagicMock

import agentscope
from agentscope.manager import ModelManager, ASManager
from agentscope.message import Msg
from agentscope.models import (
    ModelResponse,
    ModelWrapperBase,
    OpenAIChatWrapper,
    PostAPIModelWrapperBase,
    _get_model_wrapper,
)


class TestModelWrapperSimple(ModelWrapperBase):
    """A simple model wrapper class for test usage"""

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        return ModelResponse(text=self.config_name)

    def format(
        self,
        *args: Union[Msg, Sequence[Msg]],
    ) -> Union[List[dict], str]:
        return ""


class BasicModelTest(unittest.TestCase):
    """Test cases for basic model wrappers"""

    def setUp(self) -> None:
        """Init for BasicModelTest"""
        agentscope.init(disable_saving=True)

    def test_model_registry(self) -> None:
        """Test the automatic registration mechanism of model wrapper."""
        # get model wrapper class by class name
        self.assertEqual(
            _get_model_wrapper(model_type="TestModelWrapperSimple"),
            TestModelWrapperSimple,
        )
        # get model wrapper class by model type
        self.assertEqual(
            _get_model_wrapper(model_type="openai_chat"),
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
                "model_type": "openai_chat",
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
        model_manager = ModelManager.get_instance()
        model_manager.load_model_configs(
            model_configs=configs,
            clear_existing=True,
        )

        model = model_manager.get_model_by_config_name("gpt-4")
        self.assertEqual(model.config_name, "gpt-4")
        model = model_manager.get_model_by_config_name("my_post_api")
        self.assertEqual(model.config_name, "my_post_api")
        self.assertRaises(
            ValueError,
            model_manager.get_model_by_config_name,
            "non_existent_id",
        )

        # load a single config
        model_manager.load_model_configs(
            model_configs=configs[0],
            clear_existing=True,
        )
        model = model_manager.get_model_by_config_name("gpt-4")
        self.assertEqual(model.config_name, "gpt-4")
        self.assertRaises(
            ValueError,
            model_manager.get_model_by_config_name,
            "my_post_api",
        )

        # load model with the same id
        model_manager.load_model_configs(
            model_configs=configs[0],
            clear_existing=False,
        )
        mock_logging.assert_called_once_with(
            "config_name [gpt-4] already exists.",
        )

        model_manager.load_model_configs(
            model_configs={
                "model_type": "TestModelWrapperSimple",
                "model_name": "test_model_wrapper",
                "config_name": "test_model_wrapper",
                "args": {},
            },
        )
        test_model = model_manager.get_model_by_config_name(
            "test_model_wrapper",
        )
        response = test_model()
        self.assertEqual(response.text, "test_model_wrapper")
        model_manager.clear_model_configs()
        self.assertRaises(
            ValueError,
            model_manager.get_model_by_config_name,
            "test_model_wrapper",
        )

    def tearDown(self) -> None:
        """Clean up the test environment"""
        ASManager.get_instance().flush()
