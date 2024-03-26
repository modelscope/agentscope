# -*- coding: utf-8 -*-
"""Unit test for prompt engineering strategies in format function."""
import unittest
from unittest.mock import MagicMock, patch

from agentscope.message import Msg
from agentscope.models import (
    OpenAIChatWrapper,
    OllamaChatWrapper,
    OllamaGenerationWrapper,
    GeminiChatWrapper,
    DashScopeChatWrapper,
)


class ExampleTest(unittest.TestCase):
    """
    ExampleTest for a unit test.
    """

    def setUp(self) -> None:
        """Init for ExampleTest."""
        self.inputs = [
            Msg("system", "You are a helpful assistant", role="system"),
            [
                Msg("user", "What is the weather today?", role="user"),
                Msg("assistant", "It is sunny today", role="assistant"),
            ],
        ]

        self.wrong_inputs = [
            Msg("system", "You are a helpful assistant", role="system"),
            [
                "What is the weather today?",
                Msg("assistant", "It is sunny today", role="assistant"),
            ],
        ]

    @patch("openai.OpenAI")
    def test_openai_chat(self, mock_client: MagicMock) -> None:
        """Unit test for the format function in openai chat api wrapper."""
        # Prepare the mock client
        mock_client.return_value = "client_dummy"

        model = OpenAIChatWrapper(
            config_name="",
            model_name="gpt-4",
        )

        # correct format
        ground_truth = [
            {
                "role": "system",
                "content": "You are a helpful assistant",
                "name": "system",
            },
            {
                "role": "user",
                "content": "What is the weather today?",
                "name": "user",
            },
            {
                "role": "assistant",
                "content": "It is sunny today",
                "name": "assistant",
            },
        ]

        prompt = model.format(*self.inputs)  # type: ignore[arg-type]
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]

    def test_ollama_chat(self) -> None:
        """Unit test for the format function in ollama chat api wrapper."""
        model = OllamaChatWrapper(
            config_name="",
            model_name="llama2",
        )

        # correct format
        ground_truth = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "What is the weather today?"},
            {"role": "assistant", "content": "It is sunny today"},
        ]
        prompt = model.format(*self.inputs)  # type: ignore[arg-type]
        self.assertEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]

    def test_ollama_generation(self) -> None:
        """Unit test for the generation function in ollama chat api wrapper."""
        model = OllamaGenerationWrapper(
            config_name="",
            model_name="llama2",
        )

        # correct format
        ground_truth = (
            "system: You are a helpful assistant\nuser: What is "
            "the weather today?\nassistant: It is sunny today"
        )
        prompt = model.format(*self.inputs)  # type: ignore[arg-type]
        self.assertEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]

    @patch("google.generativeai.configure")
    def test_gemini_chat(self, mock_configure: MagicMock) -> None:
        """Unit test for the format function in gemini chat api wrapper."""
        mock_configure.return_value = "client_dummy"

        model = GeminiChatWrapper(
            config_name="",
            model_name="gemini-pro",
            api_key="xxx",
        )

        # correct format
        ground_truth = [
            {
                "role": "user",
                "parts": [
                    "system: You are a helpful assistant\nuser: What is the "
                    "weather today?\nassistant: It is sunny today",
                ],
            },
        ]

        prompt = model.format(*self.inputs)  # type: ignore[arg-type]
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]

    def test_dashscope_chat(self) -> None:
        """Unit test for the format function in dashscope chat api wrapper."""
        model = DashScopeChatWrapper(
            config_name="",
            model_name="qwen-max",
            api_key="xxx",
        )

        ground_truth = [
            {
                "role": "system",
                "name": "system",
                "content": "You are a helpful assistant",
            },
            {
                "role": "user",
                "name": "user",
                "content": "What is the weather today?",
            },
            {
                "role": "assistant",
                "name": "assistant",
                "content": "It is sunny today",
            },
        ]

        prompt = model.format(*self.inputs)  # type: ignore[arg-type]
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]

    def test_dashscope_advance_format(self) -> None:
        """Unit test for the advanced format function in dashscope chat api
        wrapper."""
        model = DashScopeChatWrapper(
            config_name="",
            model_name="qwen-max",
            api_key="xxx",
        )

        # correct format
        ground_truth = [
            {
                "role": "system",
                "content": "system: You are a helpful assistant\nuser: "
                "What is the weather today?\nassistant: It "
                "is sunny today",
            },
        ]

        prompt = model.advanced_format(*self.inputs)  # type: ignore[arg-type]
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
