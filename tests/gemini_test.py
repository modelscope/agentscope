# -*- coding: utf-8 -*-
"""Unit test for gemini model wrapper."""
import unittest
from unittest.mock import MagicMock, patch

import agentscope
from agentscope.models import load_model_by_config_name
from agentscope._runtime import _Runtime
from agentscope.file_manager import _FileManager
from agentscope.utils.monitor import MonitorFactory


def flush() -> None:
    """
    ** Only for unittest usage. Don't use this function in your code. **
    Clear the runtime dir and destroy all singletons.
    """
    _Runtime._flush()  # pylint: disable=W0212
    _FileManager._flush()  # pylint: disable=W0212
    MonitorFactory.flush()


class DummyResponse:
    """Dummy response for testing."""

    text = "Hello! How can I help you?"

    def __str__(self) -> str:
        """Return string representation."""
        return str({"text": self.text})


class GeminiModelWrapperTest(unittest.TestCase):
    """Unit test for gemini model wrapper."""

    def setUp(self) -> None:
        """Set up for GeminiModelWrapperTest."""
        flush()

    @patch("google.generativeai.GenerativeModel")
    def test_gemini_chat(self, mock_model: MagicMock) -> None:
        """Test for chat API."""
        # prepare mock response
        mock_counter = MagicMock()
        mock_counter.total_tokens = 20

        # connect
        mock_model.return_value.model_name = "gemini-pro"
        mock_model.return_value.generate_content.return_value = DummyResponse()
        mock_model.return_value.count_tokens.return_value = mock_counter

        agentscope.init(
            model_configs={
                "config_name": "my_gemini_chat",
                "model_type": "gemini_chat",
                "model_name": "gemini-pro",
                "api_key": "xxx",
            },
        )

        model = load_model_by_config_name("my_gemini_chat")
        response = model(contents="Hi!")

        self.assertEqual(str(response.raw), str(DummyResponse()))

    @patch("google.generativeai.embed_content")
    def test_gemini_embedding(self, mock_model: MagicMock) -> None:
        """Test gemini embedding API"""
        mock_model.return_value = {
            "embedding": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        }

        agentscope.init(
            model_configs={
                "config_name": "my_gemini_embedding",
                "model_type": "gemini_embedding",
                "model_name": "models/embedding-001",
                "api_key": "xxx",
            },
        )

        model = load_model_by_config_name("my_gemini_embedding")
        response = model(content="Hi!")

        self.assertDictEqual(
            response.raw,
            {
                "embedding": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            },
        )

    def tearDown(self) -> None:
        """Clean up after each test."""
        flush()


if __name__ == "__main__":
    unittest.main()
