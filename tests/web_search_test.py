# -*- coding: utf-8 -*-
""" Python web search test."""
import unittest
from unittest.mock import Mock, patch, MagicMock

from agentscope.service import ServiceResponse
from agentscope.service import bing_search, google_search
from agentscope.service.service_status import ServiceExecStatus


class TestWebSearches(unittest.TestCase):
    """ExampleTest for a unit test."""

    @patch("agentscope.utils.common.requests.get")
    def test_search_bing(self, mock_get: MagicMock) -> None:
        """test bing search"""
        # Set up the mock response
        mock_response = Mock()
        mock_dict = {
            "webPages": {
                "value": [
                    {
                        "name": "Test name from Bing",
                        "url": "Test url from Bing",
                        "snippet": "Test snippet from Bing",
                    },
                ],
            },
        }

        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=[
                {
                    "title": "Test name from Bing",
                    "link": "Test url from Bing",
                    "snippet": "Test snippet from Bing",
                },
            ],
        )

        mock_response.json.return_value = mock_dict
        mock_get.return_value = mock_response

        # set parameters
        bing_api_key = "fake-bing-api-key"
        test_question = "test test_question"
        num_results = 1
        params = {"q": test_question, "count": num_results}
        headers = {"Ocp-Apim-Subscription-Key": bing_api_key}

        # Call the function
        results = bing_search(
            test_question,
            api_key=bing_api_key,
            num_results=num_results,
        )

        # Assertions
        mock_get.assert_called_once_with(
            "https://api.bing.microsoft.com/v7.0/search",
            params=params,
            headers=headers,
        )
        self.assertEqual(
            results,
            expected_result,
        )

    @patch("agentscope.utils.common.requests.get")
    def test_search_google(self, mock_get: MagicMock) -> None:
        """test google search"""
        # Set up the mock response
        mock_response = Mock()
        mock_dict = {
            "items": [
                {
                    "title": "Test title from Google",
                    "link": "Test link from Google",
                    "snippet": "Test snippet from Google",
                },
            ],
        }

        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=[
                {
                    "title": "Test title from Google",
                    "link": "Test link from Google",
                    "snippet": "Test snippet from Google",
                },
            ],
        )

        mock_response.json.return_value = mock_dict
        mock_get.return_value = mock_response

        # set parameter
        test_question = "test test_question"
        google_api_key = "fake-google-api-key"
        google_cse_id = "fake-google-cse-id"
        num_results = 1

        params = {
            "q": test_question,
            "key": google_api_key,
            "cx": google_cse_id,
            "num": num_results,
        }

        # Call the function
        results = google_search(
            test_question,
            api_key=google_api_key,
            cse_id=google_cse_id,
            num_results=num_results,
        )

        # Assertions
        mock_get.assert_called_once_with(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
        )
        self.assertEqual(results, expected_result)


# This allows the tests to be run from the command line
if __name__ == "__main__":
    unittest.main()
