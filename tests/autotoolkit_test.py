# -*- coding: utf-8 -*-
""" Unit test for auto service toolkit. """
# pylint: disable=W0212
import json
import unittest
from unittest.mock import patch, MagicMock

from agentscope.manager import ASManager
from agentscope.service.mcp_search_utils import (
    build_mcp_server_config,
    search_mcp_server,
    model_free_recommend_mcp,
)

SELECTED_PACKAGE = "@test_mcp_server/test_mcp"


class AutoServiceToolkitTest(unittest.TestCase):
    """
    Unit test for AutoServiceToolkit.
    """

    def setUp(self) -> None:
        """Init for Test."""
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

    def tearDown(self) -> None:
        """clear"""
        ASManager.get_instance().flush()

    @patch("requests.get")
    def test_search_and_model_free_select(self, mock_get: MagicMock) -> None:
        """
        Unit test for AutoServiceToolkit._model_free_select.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = self.search_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        search_result = search_mcp_server(
            self.test_query,
        )

        self.assertEqual(len(search_result), 2)
        self.assertEqual(search_result, self.desired_search_result)

        selected = model_free_recommend_mcp(
            self.test_query,
            search_result,
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
        config = build_mcp_server_config(
            chosen_mcp_name="@modelcontextprotocol/server-github",
        )
        s = """{
            "mcpServers": {
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
        }
        """
        desired_config = json.loads(s)
        self.assertEqual(config, desired_config)


if __name__ == "__main__":
    unittest.main()
