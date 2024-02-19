# -*- coding: utf-8 -*-
"""Unit test for prompt engine."""
import unittest
from typing import Any

from agentscope.models import read_model_configs
from agentscope.models import load_model_by_config_name
from agentscope.models import ModelResponse, OpenAIWrapper
from agentscope.prompt import PromptEngine


class PromptEngineTest(unittest.TestCase):
    """Unit test for prompt engine."""

    def setUp(self) -> None:
        """Init for PromptEngineTest."""
        self.name = "white"
        self.sys_prompt = (
            "You're a player in a chess game, and you are playing {name}."
        )
        self.dialog_history = [
            {"name": "white player", "content": "Move to E4."},
            {"name": "black player", "content": "Okay, I moved to F4."},
            {"name": "white player", "content": "Move to F5."},
        ]
        self.hint = "Now decide your next move."
        self.prefix = "{name} player: "

        read_model_configs(
            [
                {
                    "model_type": "post_api",
                    "config_name": "open-source",
                    "api_url": "http://xxx",
                    "headers": {"Autherization": "Bearer {API_TOKEN}"},
                    "parameters": {
                        "temperature": 0.5,
                    },
                },
                {
                    "model_type": "openai",
                    "config_name": "gpt-4",
                    "model_name": "gpt-4",
                    "api_key": "xxx",
                    "organization": "xxx",
                },
            ],
            clear_existing=True,
        )

    def test_list_prompt(self) -> None:
        """Test for list prompt."""

        class TestModelWrapper(OpenAIWrapper):
            """Test model wrapper."""

            def __init__(self) -> None:
                self.max_length = 1000

            def __call__(
                self,
                *args: Any,
                **kwargs: Any,
            ) -> ModelResponse:
                return ModelResponse(text="")

            def _register_default_metrics(self) -> None:
                pass

        model = TestModelWrapper()
        engine = PromptEngine(model)

        prompt = engine.join(
            self.sys_prompt,
            self.dialog_history,
            self.hint,
            format_map={"name": self.name},
        )

        self.assertEqual(
            [
                {
                    "role": "assistant",
                    "content": "You're a player in a chess game, and you are "
                    "playing white.",
                },
                {
                    "name": "white player",
                    "role": "assistant",
                    "content": "Move to E4.",
                },
                {
                    "name": "black player",
                    "role": "assistant",
                    "content": "Okay, I moved to F4.",
                },
                {
                    "name": "white player",
                    "role": "assistant",
                    "content": "Move to F5.",
                },
                {
                    "role": "assistant",
                    "content": "Now decide your next move.",
                },
            ],
            prompt,
        )

    def test_str_prompt(self) -> None:
        """Test for string prompt."""
        model = load_model_by_config_name("open-source")
        engine = PromptEngine(model)

        prompt = engine.join(
            self.sys_prompt,
            self.dialog_history,
            self.hint,
            self.prefix,
            format_map={"name": self.name},
        )

        self.assertEqual(
            """You're a player in a chess game, and you are playing white.
white player: Move to E4.
black player: Okay, I moved to F4.
white player: Move to F5.
Now decide your next move.
white player: """,
            prompt,
        )


if __name__ == "__main__":
    unittest.main()
