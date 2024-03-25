# -*- coding: utf-8 -*-
""" Python web digest test."""

import unittest
from unittest.mock import patch, MagicMock, Mock

from agentscope.service import ServiceResponse
from agentscope.service import web_load, webpage_digest
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.message import Msg


class TestWebSearches(unittest.TestCase):
    """ExampleTest for a unit test."""

    @patch("requests.get")
    def test_web_load(self, mock_get: MagicMock) -> None:
        """test web_load function loading html"""
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
                "raw": mock_return_text,
                "selected_tags_to_text": "Some intro text about Foo.",
            },
        )

        mock_response.text = mock_return_text
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_get.return_value = mock_response

        # set parameters
        fake_url = "fake-url"

        results = web_load(
            url=fake_url,
            html_parsing_types=["raw", "selected_tags_to_text"],
        )
        self.assertEqual(
            results,
            expected_result,
        )

    def test_web_digest(self) -> None:
        """test web_digest function"""

        # test the case with dummy model
        class DummyModel(ModelWrapperBase):
            """Dummy model for testing"""

            def __init__(self) -> None:
                self.max_length = 1000

            def __call__(self, messages: list[Msg]) -> ModelResponse:
                return ModelResponse(text="model return")

        dummy_model = DummyModel()
        response = webpage_digest("testing", dummy_model)
        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="model return",
        )
        self.assertEqual(
            response,
            expected_result,
        )


# This allows the tests to be run from the command line
if __name__ == "__main__":
    unittest.main()
