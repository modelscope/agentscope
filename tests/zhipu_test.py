# -*- coding: utf-8 -*-
"""dashscope test"""
import unittest
from unittest.mock import patch, MagicMock

from agentscope.models import ZhipuAIChatWrapper


class TestZhipuAIChatWrapper(unittest.TestCase):
    """Test DashScope Chat Wrapper"""

    def setUp(self) -> None:
        self.config_name = "test_config"
        self.model_name = "test_model"
        self.api_key = "test_api_key.secret_key"
        self.messages = [
            {"role": "user", "content": "Hello, ZhipuAI!"},
            {"role": "assistant", "content": "How can I assist you?"},
        ]

    @patch("agentscope.models.zhipu_model.zhipuai")
    def test_chat(self, mock_zhipuai: MagicMock) -> None:
        """
        Test chat"""
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
        mock_zhipuai_client = MagicMock()
        mock_zhipuai.ZhipuAI.return_value = mock_zhipuai_client

        mock_zhipuai_client.chat.completions.create.return_value = (
            mock_response
        )

        chat_wrapper = ZhipuAIChatWrapper(
            config_name=self.config_name,
            model_name=self.model_name,
            api_key=self.api_key,
        )

        response = chat_wrapper(messages=self.messages)

        self.assertEqual(response.text, "Hello, this is a mocked response!")

        mock_zhipuai_client.chat.completions.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
