# -*- coding: utf-8 -*-
"""Tests for MCP tool permission metadata."""
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from mcp.types import Tool, ToolAnnotations

from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import MCPTool
from agentscope.workspace._gateway_client import (
    GatewayClient,
    GatewayMCPTool,
)


class MCPToolPermissionTest(IsolatedAsyncioTestCase):
    """Test MCP read-only annotations across client implementations."""

    async def test_read_only_hint_allows_tool_execution(self) -> None:
        """MCP 2.x read-only annotations should auto-allow execution."""
        raw_tool = Tool(
            name="read_data",
            input_schema={"type": "object"},
            annotations=ToolAnnotations(read_only_hint=True),
        )
        tools = [
            MCPTool(
                mcp_name="direct",
                tool=raw_tool,
                session=object(),
            ),
            GatewayMCPTool(
                mcp_name="gateway",
                tool=raw_tool,
                gateway=MagicMock(spec=GatewayClient),
            ),
        ]

        self.assertEqual(
            [tool.is_read_only for tool in tools],
            [True, True],
        )
        expected = PermissionDecision(
            behavior=PermissionBehavior.ALLOW,
            message="This is a read-only MCP tool. Allowing execution.",
        )
        self.assertEqual(
            [await tool.check_permissions() for tool in tools],
            [expected, expected],
        )
