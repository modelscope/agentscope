# -*- coding: utf-8 -*-
"""Regression tests for serializing tool results into tracing spans."""
import json
from unittest import TestCase

from agentscope.message import TextBlock, ToolResultBlock, ToolResultState
from agentscope.middleware._tracing._converter import _convert_block_to_part
from agentscope.middleware._tracing._utils import _serialize_to_str
from agentscope.tool import ToolResponse


class TracingSerializeTest(TestCase):
    """Pydantic objects must reach the span as JSON, not as a repr."""

    def test_tool_response_is_serialized_as_json(self) -> None:
        """The execute_tool span records the ToolResponse as JSON."""
        response = ToolResponse(
            content=[TextBlock(text="Wuhan: sunny, 25C")],
            state=ToolResultState.SUCCESS,
            id="call_1",
        )

        result = json.loads(_serialize_to_str(response))

        self.assertIsInstance(result, dict)
        self.assertEqual(result["state"], "success")
        self.assertEqual(result["content"][0]["text"], "Wuhan: sunny, 25C")

    def test_tool_result_block_output_is_serialized_as_json(self) -> None:
        """A list of blocks in a tool result becomes a JSON array of
        objects inside the ``tool_call_response`` part."""
        block = ToolResultBlock(
            id="call_1",
            name="get_weather",
            output=[TextBlock(text="Wuhan: sunny, 25C")],
            state=ToolResultState.SUCCESS,
        )

        part = _convert_block_to_part(block)
        response = json.loads(part["response"])

        self.assertEqual(response[0]["type"], "text")
        self.assertEqual(response[0]["text"], "Wuhan: sunny, 25C")
        self.assertNotIn("TextBlock(", part["response"])
