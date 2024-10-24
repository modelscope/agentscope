# -*- coding: utf-8 -*-
"""Unit test for prompt engineering strategies in format function."""
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

import agentscope
from agentscope.message import Msg
from agentscope.models import (
    OpenAIChatWrapper,
    OllamaChatWrapper,
    OllamaGenerationWrapper,
    GeminiChatWrapper,
    ZhipuAIChatWrapper,
    DashScopeChatWrapper,
    DashScopeMultiModalWrapper,
    LiteLLMChatWrapper,
    ModelWrapperBase,
)


class FormatTest(unittest.TestCase):
    """Unit test for the format function in the model wrappers."""

    def setUp(self) -> None:
        """Init for ExampleTest."""
        agentscope.init(disable_saving=True)
        self.inputs = [
            Msg("system", "You are a helpful assistant", role="system"),
            [
                Msg("user", "What is the weather today?", role="user"),
                Msg("assistant", "It is sunny today", role="assistant"),
            ],
        ]

        self.inputs_wo_sys_prompt = [
            [
                Msg("user", "What is the weather today?", role="user"),
                Msg("assistant", "It is sunny today", role="assistant"),
            ],
        ]

        self.inputs_vision = [
            Msg("system", "You are a helpful assistant", role="system"),
            [
                Msg(
                    "user",
                    "Describe the images",
                    role="user",
                    url="https://fakeweb/test.jpg",
                ),
                Msg(
                    "user",
                    "And this images",
                    "user",
                    url=[
                        "/Users/xxx/abc.png",
                        "/Users/xxx/def.mp3",
                    ],
                ),
            ],
        ]

        self.wrong_inputs = [
            Msg("system", "You are a helpful assistant", role="system"),
            [
                "What is the weather today?",
                Msg("assistant", "It is sunny today", role="assistant"),
            ],
        ]

    @patch("builtins.open", mock.mock_open(read_data=b"abcdef"))
    @patch("os.path.isfile")
    @patch("os.path.exists")
    @patch("openai.OpenAI")
    def test_openai_chat_vision_with_wrong_model(
        self,
        mock_client: MagicMock,
        mock_exists: MagicMock,
        mock_isfile: MagicMock,
    ) -> None:
        """Unit test for the format function in openai chat api wrapper with
        vision models"""
        mock_exists.side_effect = lambda url: url == "/Users/xxx/abc.png"
        mock_isfile.side_effect = lambda url: url == "/Users/xxx/abc.png"

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
                "name": "user",
                "content": "Describe the images",
            },
            {
                "role": "user",
                "name": "user",
                "content": "And this images",
            },
        ]

        prompt = model.format(*self.inputs_vision)
        self.assertListEqual(prompt, ground_truth)

    @patch("builtins.open", mock.mock_open(read_data=b"abcdef"))
    @patch("os.path.isfile")
    @patch("os.path.exists")
    @patch("openai.OpenAI")
    def test_openai_chat_vision(
        self,
        mock_client: MagicMock,
        mock_exists: MagicMock,
        mock_isfile: MagicMock,
    ) -> None:
        """Unit test for the format function in openai chat api wrapper with
        vision models"""
        mock_exists.side_effect = lambda url: url == "/Users/xxx/abc.png"
        mock_isfile.side_effect = lambda url: url == "/Users/xxx/abc.png"

        # Prepare the mock client
        mock_client.return_value = "client_dummy"

        model = OpenAIChatWrapper(
            config_name="",
            model_name="gpt-4o",
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
                "name": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe the images",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://fakeweb/test.jpg",
                        },
                    },
                ],
            },
            {
                "role": "user",
                "name": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "And this images",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,YWJjZGVm",
                        },
                    },
                ],
            },
        ]

        prompt = model.format(*self.inputs_vision)
        self.assertListEqual(prompt, ground_truth)

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

    @patch("builtins.open", mock.mock_open(read_data=b"abcdef"))
    @patch("openai.OpenAI")
    def test_openai_chat_with_other_models(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Test openai chat wrapper with other models."""
        # Prepare the mock client
        mock_client.return_value = "client_dummy"

        model = OpenAIChatWrapper(
            config_name="",
            model_name="glm-4",
            client_args={
                "base_url": "http://127.0.0.1:8011/v1/",
            },
        )

        # correct format
        ground_truth = [
            {
                "role": "system",
                "content": "You are a helpful assistant",
            },
            {
                "role": "user",
                "content": (
                    "## Conversation History\n"
                    "user: What is the weather today?\n"
                    "assistant: It is sunny today"
                ),
            },
        ]

        prompt = model.format(*self.inputs)  # type: ignore[arg-type]
        print(prompt)
        self.assertListEqual(prompt, ground_truth)

    def test_format_for_common_models(self) -> None:
        """Unit test for format function for common models."""
        prompt = ModelWrapperBase.format_for_common_chat_models(*self.inputs)

        # correct format
        ground_truth = [
            {
                "role": "system",
                "content": "You are a helpful assistant",
            },
            {
                "role": "user",
                "content": (
                    "## Conversation History\n"
                    "user: What is the weather today?\n"
                    "assistant: It is sunny today"
                ),
            },
        ]
        self.assertListEqual(prompt, ground_truth)

    def test_ollama_chat(self) -> None:
        """Unit test for the format function in ollama chat api wrapper."""
        model = OllamaChatWrapper(
            config_name="",
            model_name="llama2",
        )

        # correct format
        ground_truth = [
            {
                "role": "system",
                "content": "You are a helpful assistant",
            },
            {
                "role": "user",
                "content": (
                    "## Conversation History\n"
                    "user: What is the weather today?\n"
                    "assistant: It is sunny today"
                ),
            },
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
            "You are a helpful assistant\n\n## Conversation History\nuser: "
            "What is the weather today?\nassistant: It is sunny today"
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
                    "You are a helpful assistant\n\n## Conversation History\n"
                    "user: What is the weather today?\nassistant: It is "
                    "sunny today",
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
                "content": "You are a helpful assistant",
            },
            {
                "content": (
                    "## Conversation History\n"
                    "user: What is the weather today?\n"
                    "assistant: It is sunny today"
                ),
                "role": "user",
            },
        ]

        prompt = model.format(*self.inputs)
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]

    def test_zhipuai_chat(self) -> None:
        """Unit test for the format function in zhipu chat api wrapper."""
        model = ZhipuAIChatWrapper(
            config_name="",
            model_name="glm-4",
            api_key="xxx",
        )

        ground_truth = [
            {
                "role": "system",
                "content": "You are a helpful assistant",
            },
            {
                "content": (
                    "## Conversation History\n"
                    "user: What is the weather today?\n"
                    "assistant: It is sunny today"
                ),
                "role": "user",
            },
        ]

        prompt = model.format(*self.inputs)
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]

    def test_litellm_chat(self) -> None:
        """Unit test for the format function in litellm chat api wrapper."""
        model = LiteLLMChatWrapper(
            config_name="",
            model_name="gpt-3.5-turbo",
            api_key="xxx",
        )

        ground_truth = [
            {
                "role": "system",
                "content": "You are a helpful assistant",
            },
            {
                "role": "user",
                "content": (
                    "## Conversation History\n"
                    "user: What is the weather today?\n"
                    "assistant: It is sunny today"
                ),
            },
        ]

        prompt = model.format(*self.inputs)
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)  # type: ignore[arg-type]

    def test_dashscope_multimodal_image(self) -> None:
        """Unit test for the format function in dashscope multimodal
        conversation api wrapper for image."""
        model = DashScopeMultiModalWrapper(
            config_name="",
            model_name="qwen-vl-plus",
            api_key="xxx",
        )

        multimodal_input = [
            Msg(
                "system",
                "You are a helpful assistant",
                role="system",
                url="url1.png",
            ),
            [
                Msg(
                    "user",
                    "What is the weather today?",
                    role="user",
                    url="url2.png",
                ),
                Msg(
                    "assistant",
                    "It is sunny today",
                    role="assistant",
                    url="url3.png",
                ),
            ],
        ]

        ground_truth = [
            {
                "role": "system",
                "content": [
                    {"image": "url1.png"},
                    {"text": "You are a helpful assistant"},
                ],
            },
            {
                "role": "user",
                "content": [
                    {"image": "url2.png"},
                    {"image": "url3.png"},
                    {
                        "text": (
                            "## Conversation History\n"
                            "user: What is the weather today?\n"
                            "assistant: It is sunny today"
                        ),
                    },
                ],
            },
        ]

        prompt = model.format(*multimodal_input)
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)

    def test_dashscope_multimodal_audio(self) -> None:
        """Unit test for the format function in dashscope multimodal
        conversation api wrapper for audio."""
        model = DashScopeMultiModalWrapper(
            config_name="",
            model_name="qwen-audio-turbo",
            api_key="xxx",
        )

        multimodal_input = [
            Msg(
                "system",
                "You are a helpful assistant",
                role="system",
                url="url1.mp3",
            ),
            [
                Msg(
                    "user",
                    "What is the weather today?",
                    role="user",
                    url="url2.mp3",
                ),
                Msg(
                    "assistant",
                    "It is sunny today",
                    role="assistant",
                    url="url3.mp3",
                ),
            ],
        ]

        ground_truth = [
            {
                "role": "system",
                "content": [
                    {"audio": "url1.mp3"},
                    {"text": "You are a helpful assistant"},
                ],
            },
            {
                "role": "user",
                "content": [
                    {"audio": "url2.mp3"},
                    {"audio": "url3.mp3"},
                    {
                        "text": (
                            "## Conversation History\n"
                            "user: What is the weather today?\n"
                            "assistant: It is sunny today"
                        ),
                    },
                ],
            },
        ]

        prompt = model.format(*multimodal_input)
        self.assertListEqual(prompt, ground_truth)

        # wrong format
        with self.assertRaises(TypeError):
            model.format(*self.wrong_inputs)


if __name__ == "__main__":
    unittest.main()
