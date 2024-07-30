# -*- coding: utf-8 -*-
"""litellm test"""
import unittest
from unittest.mock import patch, MagicMock

import agentscope
from agentscope.manager import ModelManager, ASManager


class TestLiteLLMChatWrapper(unittest.TestCase):
    """Test LiteLLM Chat Wrapper"""

    def setUp(self) -> None:
        self.api_key = "test_api_key.secret_key"
        self.messages = [
            {"role": "user", "content": "Hello, litellm!"},
            {"role": "assistant", "content": "How can I assist you?"},
        ]

    @patch("litellm.completion")
    def test_chat(self, mock_litellm: MagicMock) -> None:
        """Test chat"""
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [
                {"message": {"content": "Hello, this is a mocked response!"}},
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 5,
                "total_tokens": 105,
            },
        }
        mock_response.choices[
            0
        ].message.content = "Hello, this is a mocked response!"

        mock_litellm.return_value = mock_response

        agentscope.init(
            model_configs={
                "config_name": "test_config",
                "model_type": "litellm_chat",
                "model_name": "ollama/llama3:8b",
                "api_key": self.api_key,
            },
            disable_saving=True,
        )

        model = ModelManager.get_instance().get_model_by_config_name(
            "test_config",
        )

        response = model(
            messages=self.messages,
            api_base="http://localhost:11434",
        )

        self.assertEqual(response.text, "Hello, this is a mocked response!")

    def tearDown(self) -> None:
        """Tear down the test"""
        ASManager.get_instance().flush()


if __name__ == "__main__":
    unittest.main()
