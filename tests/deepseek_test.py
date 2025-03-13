# -*- coding: utf-8 -*-
"""deepseek test"""
import unittest
from unittest.mock import patch, MagicMock
from typing import List, Any
from agentscope.models import DeepSeekChatWrapper, ModelResponse


class MockStreamResponse:
    """Mock DeepSeek streaming response"""

    def __init__(self, chunks: List[Any]) -> None:
        self.chunks = chunks

    def __iter__(self) -> Any:
        for chunk in self.chunks:
            mock_chunk = MagicMock()
            mock_chunk.model_dump.return_value = chunk
            yield mock_chunk


class DeepSeekDummyResponse:
    """Mock DeepSeek API responses"""

    @staticmethod
    def normal_response() -> MagicMock:
        """Simulate DeepSeek non-streaming non-reasoning response"""
        response = {
            "id": "chatcmpl-123456789",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?",
                    },
                    "finish_reason": "stop",
                },
            ],
        }
        mock_response = MagicMock()
        mock_response.model_dump.return_value = response
        return mock_response

    @staticmethod
    def normal_response_with_reasoning() -> MagicMock:
        """Simulate DeepSeek non-streaming reasoning response"""
        response = {
            "id": "chatcmpl-123456789",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I'll help you solve this problem.",
                        "reasoning_content": (
                            "First, I need to analyze the question and"
                            "determine the best approach..."
                        ),
                    },
                    "finish_reason": "stop",
                },
            ],
        }
        mock_response = MagicMock()
        mock_response.model_dump.return_value = response
        return mock_response

    @staticmethod
    def stream_response() -> MockStreamResponse:
        """Simulate DeepSeek streaming non-reasoning response"""
        chunks = [
            {
                "choices": [
                    {
                        "delta": {"content": "Hello"},
                        "finish_reason": None,
                        "index": 0,
                    },
                ],
            },
            {
                "choices": [
                    {
                        "delta": {"content": " world"},
                        "finish_reason": None,
                        "index": 0,
                    },
                ],
            },
            {
                "choices": [
                    {
                        "delta": {"content": "!"},
                        "finish_reason": None,
                        "index": 0,
                    },
                ],
            },
            {"choices": [{"delta": {}, "finish_reason": "stop", "index": 0}]},
        ]

        return MockStreamResponse(chunks)

    @staticmethod
    def stream_response_with_reasoning() -> MockStreamResponse:
        """Simulate DeepSeek streaming reasoning response"""
        chunks = [
            {
                "choices": [
                    {
                        "delta": {"reasoning_content": "Let's analyze"},
                        "finish_reason": None,
                        "index": 0,
                    },
                ],
            },
            {
                "choices": [
                    {
                        "delta": {"reasoning_content": " this step by step"},
                        "finish_reason": None,
                        "index": 0,
                    },
                ],
            },
            {
                "choices": [
                    {
                        "delta": {"content": "The answer"},
                        "finish_reason": None,
                        "index": 0,
                    },
                ],
            },
            {
                "choices": [
                    {
                        "delta": {"content": " is 42"},
                        "finish_reason": None,
                        "index": 0,
                    },
                ],
            },
            {"choices": [{"delta": {}, "finish_reason": "stop", "index": 0}]},
        ]

        return MockStreamResponse(chunks)


class TestDeepSeekChatWrapper(unittest.TestCase):
    """Test DeepSeek Chat Wrapper"""

    def setUp(self) -> None:
        """Set up for DeepSeekChatWrapperTest."""
        self.api_key = "test_api_key.secert_key"
        self.provider_url = "http://test_provider_url"
        self.messages = [
            {"role": "user", "content": "Hello, deepseek!"},
            {"role": "assistant", "content": "How can I assist you?"},
        ]
        self.model_name = "deepseek-chat"
        self.reasoner_model_name = "deepseek-r1"

    @patch("openai.OpenAI")
    def test_normal_chat(self, mock_openai: MagicMock) -> None:
        """Test DeepSeek model with non-stearming non-reasoning response"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            DeepSeekDummyResponse.normal_response()
        )

        # Create wrapper and test
        wrapper = DeepSeekChatWrapper(
            config_name="test",
            model_name=self.model_name,
            api_key=self.api_key,
            provider_url=self.provider_url,
            stream=False,
        )

        response = wrapper(self.messages)

        # Assert
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(response.text, "Hello! How can I help you today?")
        mock_client.chat.completions.create.assert_called_once()

    @patch("openai.OpenAI")
    def test_normal_chat_with_reasoning(self, mock_openai: MagicMock) -> None:
        """Test DeepSeek model with non-stearming reasoning response"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            DeepSeekDummyResponse.normal_response_with_reasoning()
        )

        # Create wrapper with reasoner model
        wrapper = DeepSeekChatWrapper(
            config_name="test",
            model_name=self.reasoner_model_name,
            api_key=self.api_key,
            stream=False,
        )

        response = wrapper(self.messages)

        # Assert
        self.assertIsInstance(response, ModelResponse)
        self.assertIn("Reasoning:", response.text)
        self.assertIn("First, I need to analyze", response.text)
        self.assertIn("Answer:", response.text)
        self.assertIn("I'll help you solve this problem.", response.text)

    @patch("openai.OpenAI")
    def test_stream(self, mock_openai: MagicMock) -> None:
        """Test DeepSeek model with streaming non-reasoning response"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            DeepSeekDummyResponse.stream_response()
        )

        # Create wrapper
        wrapper = DeepSeekChatWrapper(
            config_name="test",
            model_name=self.model_name,
            api_key=self.api_key,
            stream=True,
        )

        response = wrapper(self.messages)

        # Assert
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(response.text, "Hello world!")

    @patch("openai.OpenAI")
    def test_stream_with_reasoning(self, mock_openai: MagicMock) -> None:
        """Test DeepSeek model with streaming reasoning response"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = (
            DeepSeekDummyResponse.stream_response_with_reasoning()
        )

        # Create wrapper with reasoner model
        wrapper = DeepSeekChatWrapper(
            config_name="test",
            model_name=self.reasoner_model_name,
            api_key=self.api_key,
            stream=True,
        )

        response = wrapper(self.messages)
        print(response.text)
        # Assert
        self.assertIsInstance(response, ModelResponse)
        self.assertIn("Reasoning:", response.text)
        self.assertIn("Let's analyze this step by step", response.text)
        self.assertIn("Answer:", response.text)
        self.assertIn("The answer is 42", response.text)


if __name__ == "__main__":
    unittest.main()
