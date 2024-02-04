# -*- coding: utf-8 -*-
"""
Unit tests for model wrapper classes and functions
"""

from typing import Any
import unittest

from agentscope.models import (
    ModelResponse,
    ModelWrapperBase,
    OpenAIChatWrapper,
    PostAPIModelWrapperBase,
    get_model,
    read_model_configs,
    load_model_by_id,
    clear_model_configs,
)


class TestModelWrapperSimple(ModelWrapperBase):
    """A simple model wrapper class for test usage"""

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        return ModelResponse(text=self.model_id)


class BasicModelTest(unittest.TestCase):
    """Test cases for basic model wrappers"""

    def test_model_registry(self) -> None:
        """Test the automatic registration mechanism of model wrapper."""
        # get model wrapper class by class name
        self.assertEqual(
            get_model(model_type="TestModelWrapperSimple"),
            TestModelWrapperSimple,
        )
        # get model wrapper class by alias
        self.assertEqual(get_model(model_type="openai"), OpenAIChatWrapper)
        # return PostAPIModelWrapperBase if model_type is not supported
        self.assertEqual(
            get_model(model_type="unknown_model_wrapper"),
            PostAPIModelWrapperBase,
        )

    def test_load_model_configs(self) -> None:
        """Test to load model configs"""
        configs = [
            {
                "model_type": "openai",
                "model_id": "gpt-4",
                "model": "gpt-4",
                "api_key": "xxx",
                "organization": "xxx",
                "generate_args": {"temperature": 0.5},
            },
            {
                "model_type": "post_api",
                "model_id": "my_post_api",
                "api_url": "https://xxx",
                "headers": {},
                "json_args": {},
            },
        ]
        # load a list of configs
        read_model_configs(configs=configs, clear_existing=True)
        model = load_model_by_id("gpt-4")
        self.assertEqual(model.model_id, "gpt-4")
        model = load_model_by_id("my_post_api")
        self.assertEqual(model.model_id, "my_post_api")
        self.assertRaises(ValueError, load_model_by_id, "non_existent_id")

        # load a single config
        read_model_configs(configs=configs[0], clear_existing=True)
        model = load_model_by_id("gpt-4")
        self.assertEqual(model.model_id, "gpt-4")
        self.assertRaises(ValueError, load_model_by_id, "my_post_api")

        # automatically detect model with the same id
        self.assertRaises(ValueError, read_model_configs, configs[0])
        read_model_configs(
            configs={
                "model_type": "TestModelWrapperSimple",
                "model_id": "test_model_wrapper",
                "args": {},
            },
        )
        test_model = load_model_by_id("test_model_wrapper")
        response = test_model()
        self.assertEqual(response.text, "test_model_wrapper")
        clear_model_configs()
        self.assertRaises(ValueError, load_model_by_id, "test_model_wrapper")
