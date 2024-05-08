# -*- coding: utf-8 -*-
"""anthropic test"""
import unittest
from unittest.mock import patch, MagicMock

import agentscope
from agentscope.models import load_model_by_config_name


class TestAnthropicChatWrapper(unittest.TestCase):
    """Test Anthropic Chat Wrapper"""

    def setUp(self) -> None:
        self.api_key = "test_api_key.secret_key"
        self.messages = [
            {"role": "user", "content": "Hello, Anthropic!"},
            {"role": "assistant", "content": "How can I assist you?"},
        ]

    @patch("agentscope.models.anthropic_model.anthropic")
    def test_chat(self, mock_anthropic: MagicMock) -> None:
        """
        Test chat"""
        mock_response = MagicMock()
        # from https://docs.anthropic.com/claude/reference/messages-examples
        mock_response.model_dump.return_value = {
            "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Hello!",
                },
            ],
            "model": "claude-3-opus-20240229",
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 12,
                "output_tokens": 6,
            },
        }
        mock_response.content.text = "Hello!"
        mock_anthropic_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_client

        mock_anthropic_client.messages.create.return_value = mock_response

        agentscope.init(
            model_configs={
                "config_name": "test_config",
                "model_type": "anthropic_chat",
                "model_name": "claude-3-opus-20240229",
                "api_key": self.api_key,
            },
        )

        model = load_model_by_config_name("test_config")

        response = model(messages=self.messages)

        self.assertEqual(response.text, "Hello!")

        mock_anthropic_client.messages.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
