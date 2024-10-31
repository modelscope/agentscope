# -*- coding: utf-8 -*-
"""Unit tests for token counting."""
import json
import unittest
from http import HTTPStatus
from unittest.mock import patch, MagicMock

from agentscope.tokens import (
    count_openai_tokens,
    count_dashscope_tokens,
    count_gemini_tokens,
    register_model,
    count,
    supported_models,
    count_huggingface_tokens,
)


class TokenCountTest(unittest.TestCase):
    """Unit test for token counting."""

    def setUp(self) -> None:
        """Init for ExampleTest."""
        self.messages = [
            {"role": "system", "content": "You're a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm fine, thank you."},
        ]

        self.messages_gemini = [
            {"role": "system", "parts": "You're a helpful assistant."},
            {"role": "user", "parts": "Hello, how are you?"},
            {"role": "assistant", "parts": "I'm fine, thank you."},
        ]

        self.messages_openai = [
            {
                "role": "system",
                "content": "You're a helpful assistant named Friday.",
                "name": "system",
            },
            {
                "role": "user",
                "content": "Hello, how are you?",
                "name": "Bob",
            },
            {
                "role": "assistant",
                "content": "I'm fine, thank you.",
                "name": "Friday",
            },
        ]
        self.messages_openai_vision = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "I want to book a flight to Paris.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://example.com/image.jpg",
                            "detail": "auto",
                        },
                    },
                ],
            },
        ]

    def test_openai_token_counting(self) -> None:
        """Test OpenAI token counting functions."""
        n_tokens = count_openai_tokens("gpt-4o", self.messages_openai)
        self.assertEqual(n_tokens, 40)

        n_tokens = count_openai_tokens("gpt-4o", self.messages)
        self.assertEqual(n_tokens, 32)

        n_tokens = count_openai_tokens("gpt-4o", self.messages_openai_vision)
        self.assertEqual(n_tokens, 186)

    @patch("dashscope.Tokenization.call")
    def test_dashscope_token_counting(self, mock_call: MagicMock) -> None:
        """Test Dashscope token counting functions."""
        mock_call.return_value.status_code = HTTPStatus.OK
        mock_call.return_value.usage = {"input_tokens": 21}

        n_tokens = count_dashscope_tokens("qwen-max", self.messages)
        self.assertEqual(n_tokens, 21)

    @patch("google.generativeai.GenerativeModel")
    def test_gemini_token_counting(self, mock_model: MagicMock) -> None:
        """Test Gemini token counting functions."""

        mock_response = MagicMock()
        mock_response.total_tokens = 24
        mock_model.return_value.count_tokens.return_value = mock_response

        n_tokens = count_gemini_tokens(
            "gemini-1.5-pro",
            self.messages_gemini,
        )
        self.assertEqual(n_tokens, 24)

    def test_register_token_counting(self) -> None:
        """Test register token counting functions."""

        def dummy_token_counting(_: str, messages: list) -> int:
            return len(json.dumps(messages, indent=4, ensure_ascii=False))

        register_model("my-model", dummy_token_counting)
        num = count("my-model", self.messages)

        self.assertListEqual(
            supported_models(),
            ["gpt-.*", "gemini-.*", "qwen-.*"] + ["my-model"],
        )
        self.assertEqual(num, 252)

    def test_huggingface_token_counting(self) -> None:
        """Test Huggingface token counting functions."""
        n_tokens = count_huggingface_tokens(
            "Qwen/Qwen2.5-7B-Instruct",
            messages=self.messages,
            enable_mirror=True,
        )
        self.assertEqual(n_tokens, 34)


if __name__ == "__main__":
    unittest.main()
