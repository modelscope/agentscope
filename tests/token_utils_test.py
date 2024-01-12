# -*- coding: utf-8 -*-
""" Unit test for token_utils."""
import unittest
from agentscope.utils.token_utils import get_openai_max_length
from agentscope.utils.token_utils import count_openai_token


class TokenUtilsTest(unittest.TestCase):
    """Token utils test."""

    def test_get_openai_max_length(self) -> None:
        """Test the function get_openai_max_length."""
        self.assertEqual(get_openai_max_length("gpt-4"), 8192)
        self.assertEqual(get_openai_max_length("gpt-3.5-turbo"), 4096)
        with self.assertRaises(KeyError):
            get_openai_max_length("non-existing-model")

    def test_count_openai_token(self) -> None:
        """Test the function count_openai_token."""
        test_model_1 = "text-davinci-003"
        test_content_str = "This is a test string."
        self.assertEqual(
            count_openai_token(test_content_str, test_model_1),
            6,
        )

        test_content_list = [
            {
                "role": "system",
                "content": "This is a system content.",
            },
            {
                "role": "user",
                "name": "example_user",
                "content": "This is a user content.",
            },
        ]

        test_model_2 = "gpt-4"
        self.assertEqual(
            count_openai_token(test_content_list, test_model_2),
            26,
        )

        # Test unsupported model
        unsupported_model = "unsupported-model"
        with self.assertRaises(NotImplementedError):
            count_openai_token(test_content_str, unsupported_model)


if __name__ == "__main__":
    unittest.main()
