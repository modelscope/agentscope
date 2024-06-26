# -*- coding: utf-8 -*-
"""Wiki retriever test."""
import unittest
from unittest.mock import Mock, patch, MagicMock

from agentscope.service import ServiceResponse
from agentscope.service import (
    wiki_get_category_members,
    wiki_get_infobox,
    wiki_get_page_content_by_paragraph,
    wiki_get_all_wikipedia_tables,
    wiki_get_page_images_with_captions,
)
from agentscope.service.service_status import ServiceExecStatus


class TestWiki(unittest.TestCase):
    """ExampleTest for a unit test."""

    @patch("agentscope.utils.common.requests.get")
    def test_wiki_get_category_members(
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
        max_members = 1
        limit_per_request = 100
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{test_entity}",
            "cmlimit": limit_per_request,
            "format": "json",
        }

        results = wiki_get_category_members(
            entity=test_entity,
            max_members=max_members,
            limit_per_request=limit_per_request,
        )
        mock_get.assert_called_once_with(
            "https://en.wikipedia.org/w/api.php",
            params=params,
        )

        self.assertEqual(
            results,
            expected_result,
        )

    @patch("agentscope.utils.common.requests.get")
    def test_wiki_get_infobox(
        self,
        mock_get: MagicMock,
    ) -> None:
        """Test get_infobox with different parameters and responses"""

        # Mock responses for search query
        mock_response_search = Mock()
        mock_dict_search = {
            "query": {
                "search": [
                    {"title": "Test"},
                ],
            },
        }

        # Mock responses for parse query
        mock_response_parse = Mock()
        mock_dict_parse = {
            "parse": {
                "title": "Test",
                "pageid": 20,
                "text": {
                    "*": """
                         <table class="infobox vevent">
                         <tr>
                         <th>Column1</th>
                         <td>Data1</td>
                         </tr>
                         <tr>
                         <th>Column2</th>
                         <td>Data2</td>
                         </tr>
                         </table>
                         """,
                },
            },
        }

        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content={
                "Column1": "Data1",
                "Column2": "Data2",
            },
        )

        mock_response_search.json.return_value = mock_dict_search
        mock_response_parse.json.return_value = mock_dict_parse
        mock_get.side_effect = [mock_response_search, mock_response_parse]

        test_entity = "Test"

        results = wiki_get_infobox(entity=test_entity)

        # Define expected calls
        calls = [
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": test_entity,
                    "format": "json",
                },
            ),
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "parse",
                    "page": test_entity,
                    "prop": "text",
                    "format": "json",
                },
            ),
        ]

        mock_get.assert_has_calls(calls, any_order=True)

        self.assertEqual(results, expected_result)

    @patch("agentscope.utils.common.requests.get")
    def test_wiki_get_page_content_by_paragraph(
        self,
        mock_get: MagicMock,
    ) -> None:
        """Test get_page_content_by_paragraph"""

        # Mock responses for search query
        mock_response_search = Mock()
        mock_dict_search = {
            "query": {
                "search": [
                    {"title": "Test"},
                ],
            },
        }

        # Mock responses for extract query
        mock_response_extract = Mock()
        mock_dict_extract = {
            "query": {
                "pages": {
                    "20": {
                        "pageid": 20,
                        "title": "Test",
                        "extract": """
                            This is the first paragraph.

                            This is the second paragraph.

                            == Section Header ==

                            This is the third paragraph under a section header.
                        """,
                    },
                },
            },
        }

        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=[
                "This is the first paragraph.",
                "This is the second paragraph.",
            ],
        )

        mock_response_search.json.return_value = mock_dict_search
        mock_response_extract.json.return_value = mock_dict_extract
        mock_get.side_effect = [mock_response_search, mock_response_extract]

        test_entity = "Test"

        results = wiki_get_page_content_by_paragraph(
            entity=test_entity,
            max_paragraphs=2,
        )

        # Define expected calls
        params1 = {
            "action": "query",
            "list": "search",
            "srsearch": test_entity,
            "format": "json",
        }
        params2 = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True,
            "titles": test_entity,
            "format": "json",
        }

        calls = [
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params=params1,
            ),
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params=params2,
            ),
        ]

        mock_get.assert_has_calls(calls, any_order=True)

        self.assertEqual(results, expected_result)

    @patch("agentscope.utils.common.requests.get")
    def test_wiki_get_all_wikipedia_tables(
        self,
        mock_get: MagicMock,
    ) -> None:
        """Test get_all_wikipedia_tables"""

        # Mock responses for search query
        mock_response_search = Mock()
        mock_dict_search = {
            "query": {
                "search": [
                    {"title": "Test"},
                ],
            },
        }

        # Mock responses for parse query
        mock_response_parse = Mock()
        mock_dict_parse = {
            "parse": {
                "title": "Test",
                "pageid": 20,
                "text": {
                    "*": """
                         <table class="wikitable">
                         <tr>
                         <th>Header1</th>
                         <th>Header2</th>
                         </tr>
                         <tr>
                         <td>Row1Col1</td>
                         <td>Row1Col2</td>
                         </tr>
                         <tr>
                         <td>Row2Col1</td>
                         <td>Row2Col2</td>
                         </tr>
                         </table>
                         """,
                },
            },
        }

        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=[
                {
                    "Header1": ["Row1Col1", "Row2Col1"],
                    "Header2": ["Row1Col2", "Row2Col2"],
                },
            ],
        )

        mock_response_search.json.return_value = mock_dict_search
        mock_response_parse.json.return_value = mock_dict_parse
        mock_get.side_effect = [mock_response_search, mock_response_parse]

        test_entity = "Test"

        results = wiki_get_all_wikipedia_tables(entity=test_entity)

        # Define expected calls
        params1 = {
            "action": "query",
            "list": "search",
            "srsearch": test_entity,
            "format": "json",
        }
        params2 = {
            "action": "parse",
            "page": test_entity,
            "prop": "text",
            "format": "json",
        }

        calls = [
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params=params1,
            ),
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params=params2,
            ),
        ]

        mock_get.assert_has_calls(calls, any_order=True)

        self.assertEqual(results, expected_result)

    @patch("agentscope.utils.common.requests.get")
    def test_get_page_images_with_captions(
        self,
        mock_get: MagicMock,
    ) -> None:
        """Test get_page_images_with_captions"""

        # Mock responses for search query
        mock_response_search = Mock()
        mock_dict_search = {
            "query": {
                "search": [
                    {"title": "Test"},
                ],
            },
        }

        # Mock responses for images query
        mock_response_images = Mock()
        mock_dict_images = {
            "query": {
                "pages": {
                    "20": {
                        "pageid": 20,
                        "title": "Test",
                        "images": [
                            {"title": "Image1"},
                            {"title": "Image2"},
                        ],
                    },
                },
            },
        }

        # Mock responses for image details query
        mock_response_image1 = Mock()
        mock_dict_image1 = {
            "query": {
                "pages": {
                    "30": {
                        "pageid": 30,
                        "imageinfo": [
                            {
                                "url": "http://example.com/image1.jpg",
                                "extmetadata": {
                                    "ImageDescription": {
                                        "value": "Caption for image 1",
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        }

        mock_response_image2 = Mock()
        mock_dict_image2 = {
            "query": {
                "pages": {
                    "31": {
                        "pageid": 31,
                        "imageinfo": [
                            {
                                "url": "http://example.com/image2.jpg",
                                "extmetadata": {
                                    "ImageDescription": {
                                        "value": "Caption for image 2",
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        }

        expected_result = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=[
                {
                    "title": "Image1",
                    "url": "http://example.com/image1.jpg",
                    "caption": "Caption for image 1",
                },
                {
                    "title": "Image2",
                    "url": "http://example.com/image2.jpg",
                    "caption": "Caption for image 2",
                },
            ],
        )

        mock_response_search.json.return_value = mock_dict_search
        mock_response_images.json.return_value = mock_dict_images
        mock_response_image1.json.return_value = mock_dict_image1
        mock_response_image2.json.return_value = mock_dict_image2
        mock_get.side_effect = [
            mock_response_search,
            mock_response_images,
            mock_response_image1,
            mock_response_image2,
        ]

        test_entity = "Test"

        results = wiki_get_page_images_with_captions(entity=test_entity)

        # Define expected calls
        params1 = {
            "action": "query",
            "list": "search",
            "srsearch": test_entity,
            "format": "json",
        }
        params2 = {
            "action": "query",
            "prop": "images",
            "titles": test_entity,
            "format": "json",
        }
        params3_image1 = {
            "action": "query",
            "titles": "Image1",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        }
        params4_image2 = {
            "action": "query",
            "titles": "Image2",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        }

        calls = [
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params=params1,
            ),
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params=params2,
            ),
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params=params3_image1,
            ),
            unittest.mock.call(
                "https://en.wikipedia.org/w/api.php",
                params=params4_image2,
            ),
        ]

        mock_get.assert_has_calls(calls, any_order=True)

        self.assertEqual(results, expected_result)


if __name__ == "__main__":
    unittest.main()
