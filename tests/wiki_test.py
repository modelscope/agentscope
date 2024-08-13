# -*- coding: utf-8 -*-
"""Wiki retriever test."""
import unittest
from unittest.mock import Mock, patch, MagicMock

from agentscope.service import (
    wikipedia_search,
    wikipedia_search_categories,
    ServiceResponse,
    ServiceExecStatus,
)


class TestWikipedia(unittest.TestCase):
    """ExampleTest for a unit test."""

    @patch("agentscope.utils.common.requests.get")
    def test_wikipedia_search_categories(
        self,
        mock_get: MagicMock,
    ) -> None:
        """Test test_get_category_members"""
        mock_response = Mock()
        mock_dict = {
            "query": {
                "categorymembers": [
                    {
                        "pageid": 20,
                        "ns": 0,
                        "title": "This is a test",
                    },
                ],
            },
        }

        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=[
                {
                    "pageid": 20,
                    "ns": 0,
                    "title": "This is a test",
                },
            ],
        )

        mock_response.json.return_value = mock_dict
        mock_get.return_value = mock_response

        test_entity = "Test"
        limit_per_request = 500
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{test_entity}",
            "cmlimit": limit_per_request,
            "format": "json",
        }

        results = wikipedia_search_categories(query=test_entity)

        mock_get.assert_called_once_with(
            "https://en.wikipedia.org/w/api.php",
            params=params,
            timeout=20,
        )

        self.assertEqual(
            results,
            expected_result,
        )

    @patch("agentscope.utils.common.requests.get")
    def test_wikipedia_search(
        self,
        mock_get: MagicMock,
    ) -> None:
        """Test get_page_content_by_paragraph"""

        # Mock responses for extract query
        mock_response = Mock()
        mock_dict = {
            "query": {
                "pages": {
                    "20": {
                        "pageid": 20,
                        "title": "Test",
                        "extract": "This is the first paragraph.",
                    },
                    "21": {
                        "pageid": 30,
                        "title": "Test",
                        "extract": "This is the second paragraph.",
                    },
                },
            },
        }

        mock_response.json.return_value = mock_dict
        mock_get.return_value = mock_response

        expected_response = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=(
                "This is the first paragraph.\n"
                "This is the second paragraph."
            ),
        )

        response = wikipedia_search("Test")

        self.assertEqual(expected_response, response)
