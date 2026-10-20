# -*- coding: utf-8 -*-
"""Tests for keeping the MCP tool result content that carries the payload."""
import base64
import json
from typing import Any
from unittest.async_case import IsolatedAsyncioTestCase

import mcp.types

from agentscope.message import (
    Base64Source,
    DataBlock,
    TextBlock,
    ToolResultState,
)
from agentscope.tool import MCPTool


_PNG_BASE64 = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("ascii")


class _FakeSession:
    """A ClientSession stand-in that replays one prepared result."""

    def __init__(self, result: mcp.types.CallToolResult) -> None:
        self.result = result
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call_tool(  # pylint: disable=unused-argument
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        read_timeout_seconds: float | None = None,
    ) -> mcp.types.CallToolResult:
        """Record the call and return the prepared result."""
        self.calls.append((name, arguments or {}))
        return self.result


def _tool(
    result: mcp.types.CallToolResult,
) -> MCPTool:
    """Build a stateful MCP tool backed by a fake session."""
    tool_definition = mcp.types.Tool(
        name="get_weather",
        description="Read the current weather of a city.",
        input_schema={
            "type": "object",
            "properties": {"city": {"type": "string"}},
        },
        output_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "temperature_c": {"type": "number"},
            },
        },
    )
    return MCPTool(
        mcp_name="weather",
        tool=tool_definition,
        session=_FakeSession(result),
    )


class MCPStructuredResultTest(IsolatedAsyncioTestCase):
    """The model must not lose a result that only lives in
    ``structuredContent``."""

    async def test_structured_result_is_kept_when_content_is_empty(
        self,
    ) -> None:
        """A structured-only result reaches the model as JSON text."""
        structured = {"city": "Paris", "temperature_c": 21.5}
        chunk = await _tool(
            mcp.types.CallToolResult(
                content=[],
                structured_content=structured,
            ),
        ).call(city="Paris")

        self.assertEqual(len(chunk.content), 1)
        block = chunk.content[0]
        self.assertIsInstance(block, TextBlock)
        self.assertEqual(json.loads(block.text), structured)

    async def test_structured_result_is_not_duplicated(self) -> None:
        """A server that serialized the result itself is left untouched."""
        chunk = await _tool(
            mcp.types.CallToolResult(
                content=[
                    mcp.types.TextContent(type="text", text="21.5C in Paris"),
                ],
                structured_content={"city": "Paris", "temperature_c": 21.5},
            ),
        ).call(city="Paris")

        self.assertEqual(len(chunk.content), 1)
        self.assertEqual(chunk.content[0].text, "21.5C in Paris")

    async def test_structured_result_is_kept_next_to_media(self) -> None:
        """Media-only content keeps the structured payload as well."""
        structured = {"city": "Paris", "temperature_c": 21.5}
        chunk = await _tool(
            mcp.types.CallToolResult(
                content=[
                    mcp.types.ImageContent(
                        type="image",
                        data=_PNG_BASE64,
                        mime_type="image/png",
                    ),
                ],
                structured_content=structured,
            ),
        ).call(city="Paris")

        self.assertEqual(len(chunk.content), 2)
        self.assertIsInstance(chunk.content[0], DataBlock)
        source = chunk.content[0].source
        self.assertIsInstance(source, Base64Source)
        self.assertEqual(source.media_type, "image/png")
        self.assertIsInstance(chunk.content[1], TextBlock)
        self.assertEqual(json.loads(chunk.content[1].text), structured)

    async def test_empty_result_without_structured_content_stays_empty(
        self,
    ) -> None:
        """Nothing is invented when the server returned no result at all."""
        chunk = await _tool(
            mcp.types.CallToolResult(content=[]),
        ).call(city="Paris")

        self.assertEqual(chunk.content, [])

    async def test_error_result_keeps_state_and_payload(self) -> None:
        """An error result keeps its state and still carries the payload."""
        structured = {"error": "unknown city"}
        chunk = await _tool(
            mcp.types.CallToolResult(
                content=[],
                structured_content=structured,
                is_error=True,
            ),
        ).call(city="Atlantis")

        self.assertEqual(chunk.state, ToolResultState.ERROR)
        self.assertEqual(json.loads(chunk.content[0].text), structured)
