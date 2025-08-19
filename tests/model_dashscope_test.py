# -*- coding: utf-8 -*-
"""Unit tests for DashScope API model class."""
from typing import Any, AsyncGenerator
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch
from http import HTTPStatus
from pydantic import BaseModel

from agentscope.model import DashScopeChatModel, ChatResponse
from agentscope.message import TextBlock, ToolUseBlock, ThinkingBlock


class MessageMock(dict):
    """Mock class for message objects, supports both dictionary and
    attribute access."""

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        for key, value in data.items():
            setattr(self, key, value)


class SampleModel(BaseModel):
    """Sample Pydantic model for testing structured output."""

    name: str
    age: int


class TestDashScopeChatModel(IsolatedAsyncioTestCase):
    """Test cases for DashScopeChatModel."""

    def test_init_default_params(self) -> None:
        """Test initialization with default parameters."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
        )
        self.assertEqual(model.model_name, "qwen-turbo")
        self.assertEqual(model.api_key, "test_key")
        self.assertTrue(model.stream)
        self.assertIsNone(model.enable_thinking)
        self.assertTrue(model.incremental_output)
        self.assertEqual(model.generate_kwargs, {})

    def test_init_with_enable_thinking_forces_stream(self) -> None:
        """Test that enable_thinking=True forces stream=True."""
        with patch("agentscope.model._dashscope_model.logger") as mock_logger:
            model = DashScopeChatModel(
                model_name="qwen-turbo",
                api_key="test_key",
                stream=False,
                enable_thinking=True,
            )
            self.assertTrue(model.stream)
            self.assertTrue(model.enable_thinking)
            mock_logger.info.assert_called_once()

    def test_init_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        generate_kwargs = {"temperature": 0.7, "max_tokens": 1000}
        model = DashScopeChatModel(
            model_name="qwen-max",
            api_key="test_key",
            stream=False,
            enable_thinking=False,
            generate_kwargs=generate_kwargs,
        )
        self.assertEqual(model.model_name, "qwen-max")
        self.assertFalse(model.stream)
        self.assertFalse(model.enable_thinking)
        self.assertEqual(model.generate_kwargs, generate_kwargs)

    async def test_call_with_qvq_model_content_conversion(self) -> None:
        """Test content conversion when calling qvq model."""
        model = DashScopeChatModel(
            model_name="qvq-preview",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": None}]

        mock_response = self._create_mock_response("Test response")
        with patch("dashscope.MultiModalConversation.call") as mock_call:
            mock_call.return_value = mock_response
            result = await model(messages)
            # Verify content=None is converted to an empty list
            call_args = mock_call.call_args[1]
            self.assertEqual(call_args["messages"][0]["content"], [])
            self.assertEqual(call_args["model"], "qvq-preview")
            self.assertIsInstance(result, ChatResponse)
            expected_content = [TextBlock(type="text", text="Test response")]
            self.assertEqual(result.content, expected_content)

    async def test_call_with_vl_model_content_conversion(self) -> None:
        """Test content conversion when calling visual language model."""
        model = DashScopeChatModel(
            model_name="qwen-vl-max",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": [{"text": None}]}]

        mock_response = self._create_mock_response("Test response")
        with patch("dashscope.MultiModalConversation.call") as mock_call:
            mock_call.return_value = mock_response
            result = await model(messages)
            # Verify content=[{"text": None}] is converted to an empty list
            call_args = mock_call.call_args[1]
            self.assertEqual(call_args["messages"][0]["content"], [])
            self.assertIsInstance(result, ChatResponse)
            expected_content = [TextBlock(type="text", text="Test response")]
            self.assertEqual(result.content, expected_content)

    async def test_call_with_regular_model(self) -> None:
        """Test calling a regular model."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "Hello"}]

        mock_response = self._create_mock_response(
            "Hello! How can I help you?",
        )
        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_response
            result = await model(messages)
            call_args = mock_call.call_args[1]
            self.assertEqual(call_args["messages"], messages)
            self.assertEqual(call_args["model"], "qwen-turbo")
            self.assertFalse(call_args["stream"])
            self.assertIsInstance(result, ChatResponse)
            expected_content = [
                TextBlock(type="text", text="Hello! How can I help you?"),
            ]
            self.assertEqual(result.content, expected_content)

    async def test_call_with_tools_integration(self) -> None:
        """Test full integration of tool calls."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "What's the weather?"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather info",
                    "parameters": {"type": "object"},
                },
            },
        ]

        mock_response = self._create_mock_response_with_tools(
            "I'll check the weather for you.",
            [
                {
                    "id": "call_123",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Beijing"}',
                    },
                },
            ],
        )

        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_response
            result = await model(messages, tools=tools, tool_choice="auto")
            call_args = mock_call.call_args[1]
            self.assertIn("tools", call_args)
            self.assertIn("tool_choice", call_args)
            self.assertEqual(call_args["tool_choice"], "auto")

            expected_content = [
                TextBlock(type="text", text="I'll check the weather for you."),
                ToolUseBlock(
                    type="tool_use",
                    id="call_123",
                    name="get_weather",
                    input={"location": "Beijing"},
                ),
            ]
            self.assertEqual(result.content, expected_content)

    async def test_call_with_enable_thinking_streaming(self) -> None:
        """Test streaming response with thinking mode enabled."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            enable_thinking=True,
        )
        messages = [{"role": "user", "content": "Solve this problem"}]

        chunks = [
            self._create_mock_chunk(
                content="Solution",
                reasoning_content="Let me think...",
            ),
        ]

        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = self._create_async_generator(chunks)
            result = await model(messages)

            call_args = mock_call.call_args[1]
            self.assertTrue(call_args["enable_thinking"])
            self.assertTrue(call_args["stream"])
            responses = []
            async for response in result:
                responses.append(response)
            self.assertGreater(len(responses), 0)
            self.assertIsInstance(responses[0], ChatResponse)

            expected_content = [
                ThinkingBlock(type="thinking", thinking="Let me think..."),
                TextBlock(type="text", text="Solution"),
            ]
            self.assertEqual(responses[0].content, expected_content)

    async def test_call_with_structured_model_integration(self) -> None:
        """Test full integration of a structured model."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "Generate a person"}]

        mock_response = self._create_mock_response_with_tools(
            "Here's a person",
            [
                {
                    "id": "call_123",
                    "function": {
                        "name": "format_output",
                        "arguments": '{"name": "John", "age": 30}',
                    },
                },
            ],
        )

        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_response

            result = await model(messages, structured_model=SampleModel)
            call_args = mock_call.call_args[1]

            expected_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "format_output",
                        "description": "Format output according to "
                        "SampleModel schema",
                        "parameters": {
                            "description": "Sample Pydantic model for "
                            "testing structured output.",
                            "properties": {
                                "name": {
                                    "type": "string",
                                },
                                "age": {
                                    "type": "integer",
                                },
                            },
                            "required": [
                                "name",
                                "age",
                            ],
                            "type": "object",
                        },
                    },
                },
            ]
            self.assertEqual(call_args["tools"], expected_tools)
            self.assertEqual(
                call_args["tool_choice"],
                {
                    "type": "function",
                    "function": {
                        "name": "format_output",
                    },
                },
            )

            self.assertIsInstance(result, ChatResponse)
            self.assertEqual(result.metadata, {"name": "John", "age": 30})
            expected_content = [
                TextBlock(type="text", text="Here's a person"),
                ToolUseBlock(
                    type="tool_use",
                    id="call_123",
                    name="format_output",
                    input={"name": "John", "age": 30},
                ),
            ]
            self.assertEqual(result.content, expected_content)

    async def test_call_with_structured_model_warning(self) -> None:
        """Test warning when a structured model overrides tools."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "Generate a person"}]
        tools = [{"type": "function", "function": {"name": "some_tool"}}]

        mock_response = self._create_mock_response("Test")

        with (
            patch("dashscope.aigc.generation.AioGeneration.call") as mock_call,
            patch("agentscope.model._dashscope_model.logger") as mock_logger,
        ):
            mock_call.return_value = mock_response
            await model(messages, tools=tools, structured_model=SampleModel)
            mock_logger.warning.assert_called_once()

    async def test_streaming_response_processing(self) -> None:
        """Test processing of streaming response."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=True,
        )
        messages = [{"role": "user", "content": "Hello"}]

        chunks = [
            self._create_mock_chunk(
                content="Hello",
                reasoning_content="I should greet",
                tool_calls=[],
            ),
            self._create_mock_chunk(
                content=" there!",
                reasoning_content=" the user",
                tool_calls=[
                    {
                        "index": 0,
                        "id": "call_123",
                        "function": {
                            "name": "greet",
                            "arguments": '{"name": "user"}',
                        },
                    },
                ],
            ),
        ]

        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = self._create_async_generator(chunks)
            result = await model(messages)

            responses = []
            async for response in result:
                responses.append(response)
            self.assertEqual(len(responses), 2)
            final_response = responses[-1]

            expected_content = [
                ThinkingBlock(
                    type="thinking",
                    thinking="I should greet the user",
                ),
                TextBlock(type="text", text="Hello there!"),
                ToolUseBlock(
                    id="call_123",
                    name="greet",
                    input={"name": "user"},
                    type="tool_use",
                ),
            ]
            self.assertEqual(final_response.content, expected_content)

    async def test_tool_choice_validation_through_api(self) -> None:
        """Test tool choice validation through API call."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "Test"}]
        tools = [
            {
                "type": "function",
                "function": {"name": "test_tool"},
            },
        ]

        mock_response = self._create_mock_response("Test response")

        test_cases = [
            ("auto", "auto"),
            ("none", "none"),
            (
                "test_tool",
                {"type": "function", "function": {"name": "test_tool"}},
            ),
        ]

        for tool_choice, expected_format in test_cases:
            with self.subTest(tool_choice=tool_choice):
                with patch(
                    "dashscope.aigc.generation.AioGeneration.call",
                ) as mock_call:
                    mock_call.return_value = mock_response
                    await model(messages, tools=tools, tool_choice=tool_choice)

                    call_args = mock_call.call_args[1]
                    self.assertEqual(call_args["tool_choice"], expected_format)

    async def test_tool_choice_unsupported_options(self) -> None:
        """Test unsupported tool choice options."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "Test"}]
        tools = [{"type": "function", "function": {"name": "test_tool"}}]

        mock_response = self._create_mock_response("Test response")
        with (
            patch("dashscope.aigc.generation.AioGeneration.call") as mock_call,
            patch("agentscope.model._dashscope_model.logger") as mock_logger,
        ):
            mock_call.return_value = mock_response

            # Test unsupported option
            await model(messages, tools=tools, tool_choice="any")

            call_args = mock_call.call_args[1]
            self.assertEqual(call_args["tool_choice"], "auto")
            mock_logger.warning.assert_called()

    def test_tools_schema_validation_through_api(self) -> None:
        """Test tools schema validation through API call."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        # Test valid tools schema
        valid_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather info",
                },
            },
        ]

        # This test validates the format of the tools schema via an actual
        # API call
        messages = [{"role": "user", "content": "Test"}]
        mock_response = self._create_mock_response("Test")

        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_response

            # Should not throw an exception
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If event loop is already running, create a task
                    loop.create_task(model(messages, tools=valid_tools))
                else:
                    loop.run_until_complete(model(messages, tools=valid_tools))
            except Exception as e:
                if "schema must be a dict" in str(e):
                    self.fail("Valid tools schema was rejected")

    async def test_error_handling_scenarios(self) -> None:
        """Test various error handling scenarios."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "Hello"}]

        # Test failure of non-streaming API call
        mock_response = Mock()
        mock_response.status_code = 400
        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_response
            with self.assertRaises(RuntimeError):
                await model(messages)

    async def test_streaming_error_handling(self) -> None:
        """Test error handling for streaming responses."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=True,
        )
        messages = [{"role": "user", "content": "Hello"}]

        error_chunk = Mock()
        error_chunk.status_code = 500
        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = self._create_async_generator(
                [error_chunk],
            )

            result = await model(messages)
            with self.assertRaises(RuntimeError):
                async for _ in result:
                    pass

    async def test_content_processing_variations(self) -> None:
        """Test various content processing scenarios."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "Test"}]
        # Test content in list format
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message = MessageMock(
            {
                "content": [
                    {"text": "Hello"},
                    {"text": " world"},
                ],
            },
        )
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 10
        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_response
            result = await model(messages)

            expected_content = [
                TextBlock(type="text", text="Hello"),
                TextBlock(type="text", text=" world"),
            ]
            self.assertEqual(result.content, expected_content)

    # Auxiliary methods
    def _create_mock_response(self, content: str) -> Mock:
        """Create a standard mock response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message = MessageMock(
            {"content": content},
        )
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        return mock_response

    def _create_mock_response_with_tools(
        self,
        content: str,
        tool_calls: list,
    ) -> Mock:
        """Create a mock response containing tool calls."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message = MessageMock(
            {
                "content": content,
                "tool_calls": tool_calls,
            },
        )
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 30
        return mock_response

    def _create_mock_chunk(
        self,
        content: str = "",
        reasoning_content: str = "",
        tool_calls: list = None,
    ) -> Mock:
        """Create a mock chunk for streaming responses."""
        chunk = Mock()
        chunk.status_code = HTTPStatus.OK
        chunk.output.choices = [Mock()]
        chunk.output.choices[0].message = MessageMock(
            {
                "content": content,
                "reasoning_content": reasoning_content,
                "tool_calls": tool_calls or [],
            },
        )
        chunk.usage = Mock()
        chunk.usage.input_tokens = 5
        chunk.usage.output_tokens = 10
        return chunk

    async def _create_async_generator(self, items: list) -> AsyncGenerator:
        """Create an asynchronous generator."""
        for item in items:
            yield item


class TestDashScopeIntegrationScenarios(IsolatedAsyncioTestCase):
    """Integration test scenarios for Dashscope model."""

    async def test_complete_conversation_flow(self) -> None:
        """Test the complete conversation flow."""
        model = DashScopeChatModel(
            model_name="qwen-max",
            api_key="test_key",
            stream=False,
        )
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message = MessageMock(
            {
                "content": "I'm doing well, thank you for asking!",
            },
        )
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25

        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_response
            result = await model(messages)
            self.assertIsInstance(result, ChatResponse)
            self.assertEqual(len(result.content), 1)
            expected_content = [
                TextBlock(
                    type="text",
                    text="I'm doing well, thank you for asking!",
                ),
            ]
            self.assertEqual(result.content, expected_content)
            self.assertEqual(result.usage.input_tokens, 15)
            self.assertEqual(result.usage.output_tokens, 25)

    async def test_multi_turn_conversation_with_tools(self) -> None:
        """Test multi-turn conversation with tools."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=False,
        )

        messages = [
            {"role": "user", "content": "What's the weather in Beijing?"},
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                        },
                    },
                },
            },
        ]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message = MessageMock(
            {
                "content": "Let me check the weather for you.",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Beijing"}',
                        },
                    },
                ],
            },
        )
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 30
        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_response
            result = await model(messages, tools=tools, tool_choice="auto")

            expected_content = [
                TextBlock(
                    type="text",
                    text="Let me check the weather for you.",
                ),
                ToolUseBlock(
                    type="tool_use",
                    id="call_123",
                    name="get_weather",
                    input={"location": "Beijing"},
                ),
            ]
            self.assertEqual(result.content, expected_content)

    async def test_streaming_with_complex_content(self) -> None:
        """Test streaming processing with complex content."""
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key="test_key",
            stream=True,
        )
        messages = [
            {"role": "user", "content": "Solve this complex problem"},
        ]

        # Mock complex streaming response
        chunks = [
            # First chunk: Start thinking
            Mock(
                status_code=HTTPStatus.OK,
                output=Mock(
                    choices=[
                        Mock(
                            message=MessageMock(
                                {
                                    "content": "",
                                    "reasoning_content": "Let me analyze "
                                    "this step by step.",
                                    "tool_calls": [],
                                },
                            ),
                        ),
                    ],
                ),
                usage=Mock(input_tokens=10, output_tokens=5),
            ),
            # Second chunk: Continue thinking and start answering
            Mock(
                status_code=HTTPStatus.OK,
                output=Mock(
                    choices=[
                        Mock(
                            message=MessageMock(
                                {
                                    "content": "To solve this problem, ",
                                    "reasoning_content": " First, I need to"
                                    " understand the requirements.",
                                    "tool_calls": [],
                                },
                            ),
                        ),
                    ],
                ),
                usage=Mock(input_tokens=10, output_tokens=15),
            ),
            # Third chunk: Tool call
            Mock(
                status_code=HTTPStatus.OK,
                output=Mock(
                    choices=[
                        Mock(
                            message=MessageMock(
                                {
                                    "content": "I'll use a calculation tool.",
                                    "reasoning_content": " The calculation is"
                                    " needed here.",
                                    "tool_calls": [
                                        {
                                            "index": 0,
                                            "id": "calc_",
                                            "function": {
                                                "name": "calculate",
                                                "arguments": '{"expression":'
                                                ' "2+2"}',
                                            },
                                        },
                                    ],
                                },
                            ),
                        ),
                    ],
                ),
                usage=Mock(input_tokens=10, output_tokens=25),
            ),
        ]

        async def mock_generator() -> AsyncGenerator:
            for chunk in chunks:
                yield chunk

        with patch(
            "dashscope.aigc.generation.AioGeneration.call",
        ) as mock_call:
            mock_call.return_value = mock_generator()

            result = await model(messages)
            responses = []
            async for response in result:
                responses.append(response)

            self.assertEqual(len(responses), 3)
            final_response = responses[-1]

            expected_content = [
                ThinkingBlock(
                    type="thinking",
                    thinking="Let me analyze this step by step. First, "
                    "I need to understand the requirements. "
                    "The calculation is needed here.",
                ),
                TextBlock(
                    type="text",
                    text="To solve this problem, I'll use a calculation tool.",
                ),
                ToolUseBlock(
                    type="tool_use",
                    id="calc_",
                    name="calculate",
                    input={"expression": "2+2"},
                ),
            ]
            self.assertEqual(final_response.content, expected_content)
