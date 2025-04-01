# -*- coding: utf-8 -*-
""" Unit test for auto service toolkit. """
# pylint: disable=W0212
import json
import unittest
from typing import Any
from unittest.mock import patch, MagicMock

import agentscope
from agentscope.service import AutoServiceToolkit
from agentscope.models import ModelResponse, OpenAIChatWrapper

SELECTED_PACKAGE = "@test_mcp_server/test_mcp"


class DummyModelForAutoServiceToolkit(OpenAIChatWrapper):
    """
    Dummy model wrapper for testing
    """

    model_type: str = "dummy_test_for_autoservice_toolkit"

    def __init__(self, **kwargs: Any) -> None:
        """dummy init"""

    def format(self, *arg: Any, **kwargs: Any) -> str:
        return str(arg) + str(kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        """dummy call"""
        return ModelResponse(text=SELECTED_PACKAGE)


class AutoServiceToolkitTest(unittest.TestCase):
    """
    Unit test for AutoServiceToolkit.
    """

    def setUp(self) -> None:
        """Init for ExampleTest."""
        self.model_free_toolkit = AutoServiceToolkit(
            model_free=True,
        )
        model_config_name = "dummy_test_config"
        agentscope.register_model_wrapper_class(
            DummyModelForAutoServiceToolkit,
            exist_ok=True,
        )
        agentscope.init(
            model_configs=[
                {
                    "model_type": "dummy_test_for_autoservice_toolkit",
                    "config_name": model_config_name,
                },
            ],
            disable_saving=True,
        )
        self.model_based_toolkit = AutoServiceToolkit(
            model_config_name=model_config_name,
        )

        self.search_response = {
            "objects": [
                {
                    "downloads": {
                        "monthly": 100,
                        "weekly": 100,
                    },
                    "package": {
                        "name": "@test_package/test",
                        "keywords": ["mcp"],
                        "version": "x.x.x",
                        "description": "test package",
                        "sanitized_name": "@test_package/test",
                        "publisher": {
                            "email": "xxx@xxx.io",
                            "username": "yyyy",
                        },
                        "maintainers": [
                            {
                                "email": "xxx@xxx.io",
                                "username": "yyyy",
                            },
                        ],
                        "license": "GPL-3.0",
                        "date": "2025-03-xxT15:42:03.276Z",
                        "links": {
                            "npm": "https://www.npmjs.com/package/"
                            "@test_package/test",
                        },
                    },
                },
                {
                    "downloads": {
                        "monthly": 1000,
                        "weekly": 1000,
                    },
                    "package": {
                        "name": "@test_package/test_dummy",
                        "keywords": [],
                        "version": "x.x.x",
                        "description": "test package that does not install",
                        "sanitized_name": "@test_package/test_dummy",
                        "publisher": {
                            "email": "xxx@xxx.io",
                            "username": "yyyy",
                        },
                    },
                },
                {
                    "downloads": {
                        "monthly": 3000,
                        "weekly": 1000,
                    },
                    "package": {
                        "name": "@test_mcp_server/test_mcp",
                        "keywords": ["mcp", "MCP server", "test", "unittest"],
                        "version": "x.x.x",
                        "description": "test mcp server that is recommended",
                        "sanitized_name": "@test_mcp_server/test_mcp",
                        "publisher": {
                            "email": "xxx@xxx.io",
                            "username": "yyyy",
                        },
                    },
                },
            ],
        }
        self.desired_search_result = [
            {
                "name": "@test_package/test",
                "description": "test package",
                "keywords": ["mcp"],
                "downloads": {"monthly": 100, "weekly": 100},
                "publisher": {"email": "xxx@xxx.io", "username": "yyyy"},
            },
            {
                "name": "@test_mcp_server/test_mcp",
                "description": "test mcp server that is recommended",
                "keywords": ["mcp", "MCP server", "test", "unittest"],
                "downloads": {"monthly": 3000, "weekly": 1000},
                "publisher": {"email": "xxx@xxx.io", "username": "yyyy"},
            },
        ]
        self.package_description = {
            "name": "@test_package",
        }
        self.test_query = "test"
        # README snapshot obatained by
        # requests.get(
        #   "https://registry.npmjs.org/@modelcontextprotocol/server-github",
        # )
        self.test_readme = (
            "# GitHub MCP Server\n\nMCP Server for the GitHub API, enabling "
            "file operations, repository management, search functionality, "
            "and more.\n\n### Features\n\n .... - Copy the generated token\n\n"
            "### Usage with Claude Desktop\nTo use this with Claude Desktop, "
            "add the following to your `claude_desktop_config.json`:"
            '\n\n#### Docker\n```json\n{\n  "mcpServers": {\n    "github":'
            ' {\n      "command": "docker",\n      "args": [\n        '
            '"run",\n        "-i",\n        "--rm",\n        "-e",\n'
            '        "GITHUB_PERSONAL_ACCESS_TOKEN",\n        "mcp/'
            'github"\n      ],\n      "env": {\n        "GITHUB_PERSONAL_'
            'ACCESS_TOKEN": "<YOUR_TOKEN>"\n      }\n    }\n  }\n}\n```\n\n'
            '### NPX\n\n```json\n{\n  "mcpServers": {\n    "github": {\n'
            '      "command": "npx",\n      "args": [\n        "-y",'
            '\n        "@modelcontextprotocol/server-github"\n      ],\n   '
            '   "env": {\n        "GITHUB_PERSONAL_ACCESS_TOKEN": '
            '"<YOUR_TOKEN>"\n      }\n    }\n  }\n}\n```\n\n## Build\n'
            "\nDocker build:\n\n```bash\ndocker build -t mcp/github -f "
            "src/github/Dockerfile .\n```\n\n## License\n\nThis MCP server is "
            "licensed under the MIT License. This means you are free to use, "
            "modify, and distribute the software, subject to the terms and "
            "conditions of the MIT License. For more details, please see the "
            "LICENSE file in the project repository.\n"
        )

    @patch("requests.get")
    def test_search_and_model_free_select(self, mock_get: MagicMock) -> None:
        """
        Unit test for AutoServiceToolkit._model_free_select.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = self.search_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        search_result = self.model_free_toolkit.search_mcp_server(
            self.test_query,
        )

        self.assertEqual(len(search_result), 2)
        self.assertEqual(search_result, self.desired_search_result)

        selected = self.model_free_toolkit._model_free_select(
            self.test_query,
            search_result,
        )
        self.assertEqual(selected, self.desired_search_result[1])

    def test_model_based_select(self) -> None:
        """Unit test for AutoServiceToolkit._model_based_select."""
        selected = self.model_based_toolkit._llm_select(
            self.test_query,
            self.desired_search_result,
        )
        self.assertEqual(selected, self.desired_search_result[1])

    @patch("requests.get")
    def test_mcp_config_parser(self, mock_get: MagicMock) -> None:
        """Unit test for extracting config from README"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "readme": self.test_readme,
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        config = self.model_free_toolkit._build_server_config(
            chosen_mcp_name="@modelcontextprotocol/server-github",
            skip_modification=True,
        )
        s = """{
            "@modelcontextprotocol/server-github": {
              "command": "npx",
              "args": [
                "-y",
                "@modelcontextprotocol/server-github"
              ],
              "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
              }
            }
        }
        """
        desired_config = json.loads(s)
        self.assertEqual(config, desired_config)


if __name__ == "__main__":
    unittest.main()
