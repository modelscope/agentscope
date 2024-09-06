# -*- coding: utf-8 -*-
"""Unit test for Ollama model APIs."""
import unittest
from unittest.mock import patch, MagicMock
import agentscope
from agentscope.manager import ModelManager, ASManager


class OllamaModelWrapperTest(unittest.TestCase):
    """Unit test for Ollama model APIs."""

    def setUp(self) -> None:
        """Init for OllamaModelWrapperTest."""
        self.dummy_response = {
            "model": "llama2",
            "created_at": "2024-03-12T04:16:48.911377Z",
            "message": {
                "role": "assistant",
                "content": (
                    "Hello! It's nice to meet you. Is there something I can "
                    "help you with or would you like to chat?",
                ),
            },
            "done": True,
            "total_duration": 20892900042,
            "load_duration": 20019679292,
            "prompt_eval_count": 22,
            "prompt_eval_duration": 149094000,
            "eval_count": 26,
            "eval_duration": 721982000,
        }

        self.dummy_embedding = {
            "embedding": [1.0, 2.0, 3.0],
        }

        self.dummy_generate = {
            "model": "llama2",
            "created_at": "2024-03-12T03:42:19.621919Z",
            "response": "\n1 + 1 = 2",
            "done": True,
            "context": [
                518,
                25580,
                29962,
                3532,
                14816,
                29903,
                29958,
                5299,
                829,
                14816,
                29903,
                6778,
                13,
                13,
                29896,
                29974,
                29896,
                29922,
                518,
                29914,
                25580,
                29962,
                13,
                13,
                29896,
                718,
                29871,
                29896,
                353,
                29871,
                29906,
            ],
            "total_duration": 6146120041,
            "load_duration": 6677375,
            "prompt_eval_count": 9,
            "prompt_eval_duration": 5913554000,
            "eval_count": 9,
            "eval_duration": 223689000,
        }

    @patch("ollama.Client")
    def test_ollama_chat(self, mock_ollama_client: MagicMock) -> None:
        """Unit test for ollama chat API."""
        # prepare the mock
        mock_client_instance = MagicMock()
        mock_ollama_client.return_value = mock_client_instance
        mock_client_instance.chat.return_value = self.dummy_response

        # run test
        agentscope.init(
            model_configs={
                "config_name": "my_ollama_chat",
                "model_type": "ollama_chat",
                "model_name": "llama2",
                "options": {
                    "temperature": 0.5,
                },
                "keep_alive": "5m",
            },
            disable_saving=True,
        )

        model = ModelManager.get_instance().get_model_by_config_name(
            "my_ollama_chat",
        )
        response = model(messages=[{"role": "user", "content": "Hi!"}])

        self.assertEqual(response.raw, self.dummy_response)

    @patch("ollama.Client")
    def test_ollama_embedding(self, mock_ollama_client: MagicMock) -> None:
        """Unit test for ollama embeddings API."""
        # prepare the mock
        mock_client_instance = MagicMock()
        mock_ollama_client.return_value = mock_client_instance
        mock_client_instance.embeddings.return_value = self.dummy_embedding

        # run test
        agentscope.init(
            model_configs={
                "config_name": "my_ollama_embedding",
                "model_type": "ollama_embedding",
                "model_name": "llama2",
                "options": {
                    "temperature": 0.5,
                },
                "keep_alive": "5m",
            },
            disable_saving=True,
        )

        model = ModelManager.get_instance().get_model_by_config_name(
            "my_ollama_embedding",
        )
        response = model(prompt="Hi!")

        self.assertEqual(response.raw, self.dummy_embedding)

    @patch("ollama.Client")
    def test_ollama_generate(self, mock_ollama_client: MagicMock) -> None:
        """Unit test for ollama generate API."""
        # prepare the mock
        mock_client_instance = MagicMock()
        mock_ollama_client.return_value = mock_client_instance
        mock_client_instance.generate.return_value = self.dummy_generate

        # run test
        agentscope.init(
            model_configs={
                "config_name": "my_ollama_generate",
                "model_type": "ollama_generate",
                "model_name": "llama2",
                "options": None,
                "keep_alive": "5m",
            },
            disable_saving=True,
        )

        model = ModelManager.get_instance().get_model_by_config_name(
            "my_ollama_generate",
        )
        response = model(prompt="1+1=")

        self.assertEqual(response.raw, self.dummy_generate)

    def tearDown(self) -> None:
        """Clean up after each test."""
        ASManager.get_instance().flush()


if __name__ == "__main__":
    unittest.main()
