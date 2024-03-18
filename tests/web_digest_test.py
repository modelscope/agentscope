# -*- coding: utf-8 -*-
""" Python web digest test."""

import unittest
from unittest.mock import patch, MagicMock
from langchain.docstore.document import Document

from agentscope.service import ServiceResponse
from agentscope.service import webpage_digest
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.message import Msg


class TestWebSearches(unittest.TestCase):
    """ExampleTest for a unit test."""

    @patch("langchain_community.document_loaders.AsyncChromiumLoader.load")
    def test_webpage_digest(self, mock_get: MagicMock) -> None:
        """test webpage_digest"""
        # Set up the mock response
        mock_return = [
            Document(
                page_content="""
            <!DOCTYPE html>
            <html>
            <body>
                <div>
                    <h1>Foo</h1>
                    <p>Some intro text about Foo.</p>
                </div>
            </body>
            </html>
            """,
            ),
        ]

        bs4_expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Foo  Some intro text about Foo.",
        )

        mock_get.return_value = mock_return

        # set parameters
        fake_url = "fake-url"

        # Call the function
        results = webpage_digest(url=fake_url, model=None)

        # Assertions
        self.assertEqual(results, bs4_expected_result)

        # test the case with model
        class DummyModel(ModelWrapperBase):
            """Dummy model for testing"""

            def __init__(self) -> None:
                pass

            def __call__(self, messages: list[Msg]) -> ModelResponse:
                return ModelResponse(text="model return")

        dummy_model = DummyModel()
        model_expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="model return",
        )

        results = webpage_digest(url=fake_url, model=dummy_model)
        self.assertEqual(
            results,
            model_expected_result,
        )


# This allows the tests to be run from the command line
if __name__ == "__main__":
    unittest.main()
