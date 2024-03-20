# -*- coding: utf-8 -*-
""" Python web digest test."""

import unittest
from unittest.mock import patch, MagicMock, Mock

from agentscope.service import ServiceResponse
from agentscope.service import webpage_digest
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.message import Msg


class TestWebSearches(unittest.TestCase):
    """ExampleTest for a unit test."""

    @patch("requests.get")
    def test_webpage_digest(self, mock_get: MagicMock) -> None:
        """test webpage_digest"""
        # Set up the mock response
        mock_response = Mock()
        mock_return_text = """
            <!DOCTYPE html>
            <html>
            <body>
                <div>
                    <p>
                    Some intro text about Foo. <a href="xxx">Examples</a>
                    </p>
                </div>
            </body>
            </html>
        """

        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content={
                "html_text_content": "Some intro text about Foo. "
                "Examples (xxx)",
                "href_links": [
                    {
                        "content": "Examples",
                        "href_link": "xxx",
                    },
                ],
                "model_digested": [
                    {
                        "split_info": {},
                        "digested_text": "model return",
                    },
                ],
            },
        )

        mock_response.text = mock_return_text
        mock_get.return_value = mock_response

        # set parameters
        fake_url = "fake-url"

        # test the case with dummy model
        class DummyModel(ModelWrapperBase):
            """Dummy model for testing"""

            def __init__(self) -> None:
                pass

            def __call__(self, messages: list[Msg]) -> ModelResponse:
                return ModelResponse(text="model return")

        dummy_model = DummyModel()
        results = webpage_digest(url=fake_url, model=dummy_model)
        self.assertEqual(
            results,
            expected_result,
        )


# This allows the tests to be run from the command line
if __name__ == "__main__":
    unittest.main()
