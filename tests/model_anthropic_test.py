# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines
"""Unit tests for Anthropic API model class."""
from typing import Any, AsyncGenerator
from unittest.mock import Mock, patch, AsyncMock
import pytest
from pydantic import BaseModel

from agentscope.model import AnthropicChatModel, ChatResponse
from agentscope.message import TextBlock, ToolUseBlock, ThinkingBlock


class SampleModel(BaseModel):
    """Sample Pydantic model for testing structured output."""

    name: str
    age: int


class AnthropicMessageMock:
    """Mock class for Anthropic message objects."""

    def __init__(self, content: list = None, usage: dict = None):
        self.content = content or []
        self.usage = self._create_usage_mock(usage) if usage else None

    def _create_usage_mock(self, usage_data: dict) -> Mock:
        usage_mock = Mock()
        usage_mock.input_tokens = usage_data.get("input_tokens", 0)
        usage_mock.output_tokens = usage_data.get("output_tokens", 0)
        return usage_mock


class AnthropicContentBlockMock:
    """Mock class for Anthropic content blocks."""

    def __init__(self, block_type: str, **kwargs: Any) -> None:
        self.type = block_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class AnthropicEventMock:
    """Mock class for Anthropic streaming events."""

    def __init__(self, event_type: str, **kwargs: Any) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestAnthropicChatModel:
    """Test cases for AnthropicChatModel."""

    def test_init_default_params(self) -> None:
        """Test initialization with default parameters."""
        with patch("anthropic.AsyncAnthropic") as mock_client:
            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
            )
            assert model.model_name == "claude-3-sonnet-20240229"
            assert model.max_tokens == 2048
            assert model.stream is True
            assert model.thinking is None
            assert model.generate_kwargs == {}
            mock_client.assert_called_once_with(api_key="test_key")

    def test_init_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        thinking_config = {"type": "enabled", "budget_tokens": 1024}
        generate_kwargs = {"temperature": 0.7, "top_p": 0.9}
        client_args = {"timeout": 30}

        with patch("anthropic.AsyncAnthropic") as mock_client:
            model = AnthropicChatModel(
                model_name="claude-3-opus-20240229",
                api_key="test_key",
                max_tokens=4096,
                stream=False,
                thinking=thinking_config,
                client_args=client_args,
                generate_kwargs=generate_kwargs,
            )
            assert model.model_name == "claude-3-opus-20240229"
            assert model.max_tokens == 4096
            assert model.stream is False
            assert model.thinking == thinking_config
            assert model.generate_kwargs == generate_kwargs
            mock_client.assert_called_once_with(api_key="test_key", timeout=30)

    def test_init_missing_anthropic_package(self) -> None:
        """Test initialization when anthropic package is missing."""
        with patch("builtins.__import__", side_effect=ImportError):
            with pytest.raises(
                ImportError,
                match="Please install the `anthropic` package",
            ):
                AnthropicChatModel(
                    model_name="claude-3-sonnet-20240229",
                    api_key="test_key",
                )

    @pytest.mark.asyncio
    async def test_call_with_regular_messages(self) -> None:
        """Test calling with regular messages."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello"}]
            mock_response = AnthropicMessageMock(
                content=[
                    AnthropicContentBlockMock(
                        "text",
                        text="Hello! How can I help you?",
                    ),
                ],
                usage={"input_tokens": 10, "output_tokens": 20},
            )
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await model(messages)
            # Verify API call
            call_args = mock_client.messages.create.call_args[1]
            assert call_args["model"] == "claude-3-sonnet-20240229"
            assert call_args["max_tokens"] == 2048
            assert call_args["stream"] is False
            assert call_args["messages"] == messages
            # Verify result
            assert isinstance(result, ChatResponse)
            assert result.content == [
                TextBlock(type="text", text="Hello! How can I help you?"),
            ]
            assert result.usage.input_tokens == 10
            assert result.usage.output_tokens == 20

    @pytest.mark.asyncio
    async def test_call_with_system_message(self) -> None:
        """Test calling with system message extraction."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
            ]
            mock_response = AnthropicMessageMock(
                content=[AnthropicContentBlockMock("text", text="Hi there!")],
                usage={"input_tokens": 15, "output_tokens": 5},
            )
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            await model(messages)

            # Verify system message extraction
            call_args = mock_client.messages.create.call_args[1]
            assert call_args["system"] == "You are a helpful assistant"
            assert call_args["messages"] == [
                {"role": "user", "content": "Hello"},
            ]

    @pytest.mark.asyncio
    async def test_call_with_thinking_enabled(self) -> None:
        """Test calling with thinking functionality enabled."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            thinking_config = {"type": "enabled", "budget_tokens": 1024}
            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
                thinking=thinking_config,
            )
            model.client = mock_client

            messages = [
                {"role": "user", "content": "Think about this problem"},
            ]
            thinking_block = AnthropicContentBlockMock(
                "thinking",
                thinking="Let me analyze this step by step...",
                signature="thinking_signature_123",
            )
            text_block = AnthropicContentBlockMock(
                "text",
                text="Here's my analysis",
            )
            mock_response = AnthropicMessageMock(
                content=[thinking_block, text_block],
                usage={"input_tokens": 20, "output_tokens": 40},
            )
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await model(messages)

            # Verify thinking parameter is passed
            call_args = mock_client.messages.create.call_args[1]
            assert call_args["thinking"] == thinking_config
            # Verify result contains thinking block
            expected_thinking_block = ThinkingBlock(
                type="thinking",
                thinking="Let me analyze this step by step...",
            )
            expected_thinking_block["signature"] = "thinking_signature_123"
            assert result.content == [
                expected_thinking_block,
                TextBlock(type="text", text="Here's my analysis"),
            ]

    @pytest.mark.asyncio
    async def test_call_with_tools_integration(self) -> None:
        """Test full integration of tool calls."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

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
            text_block = AnthropicContentBlockMock(
                "text",
                text="I'll check the weather",
            )
            tool_block = AnthropicContentBlockMock(
                "tool_use",
                id="tool_123",
                name="get_weather",
                input={"location": "Beijing"},
            )

            mock_response = AnthropicMessageMock(
                content=[text_block, tool_block],
                usage={"input_tokens": 25, "output_tokens": 15},
            )
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await model(messages, tools=tools, tool_choice="auto")
            # Verify tool formatting
            call_args = mock_client.messages.create.call_args[1]
            expected_tools = [
                {
                    "name": "get_weather",
                    "description": "Get weather info",
                    "input_schema": {"type": "object"},
                },
            ]
            assert call_args["tools"] == expected_tools
            assert call_args["tool_choice"] == {"type": "auto"}
            # Verify result
            assert result.content == [
                TextBlock(type="text", text="I'll check the weather"),
                ToolUseBlock(
                    type="tool_use",
                    id="tool_123",
                    name="get_weather",
                    input={"location": "Beijing"},
                ),
            ]

    @pytest.mark.asyncio
    async def test_streaming_response_processing(self) -> None:
        """Test processing of streaming response."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=True,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello"}]
            # Mock streaming events
            events = [
                AnthropicEventMock(
                    "message_start",
                    message=Mock(usage=Mock(input_tokens=10, output_tokens=0)),
                ),
                AnthropicEventMock(
                    "content_block_delta",
                    index=0,
                    delta=Mock(type="text_delta", text="Hello"),
                ),
                AnthropicEventMock(
                    "content_block_delta",
                    index=0,
                    delta=Mock(type="text_delta", text=" there!"),
                ),
                AnthropicEventMock(
                    "message_delta",
                    usage=Mock(output_tokens=5),
                ),
            ]

            async def mock_stream() -> AsyncGenerator:
                for event in events:
                    yield event

            mock_client.messages.create = AsyncMock(return_value=mock_stream())
            result = await model(messages)
            responses = []
            async for response in result:
                responses.append(response)
            # Verify we got streaming responses
            final_response = responses[-1]
            assert isinstance(final_response, ChatResponse)
            assert final_response.content == [
                TextBlock(type="text", text="Hello there!"),
            ]

    @pytest.mark.asyncio
    async def test_streaming_with_thinking_and_tools(self) -> None:
        """Test streaming with thinking and tool calls."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=True,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Calculate something"}]

            content_block_mock = Mock()
            content_block_mock.type = "tool_use"
            content_block_mock.id = "tool_456"
            content_block_mock.name = "calculate"

            events = [
                AnthropicEventMock(
                    "message_start",
                    message=Mock(usage=Mock(input_tokens=15, output_tokens=0)),
                ),
                AnthropicEventMock(
                    "content_block_delta",
                    index=0,
                    delta=Mock(
                        type="thinking_delta",
                        thinking="Let me think...",
                    ),
                ),
                AnthropicEventMock(
                    "content_block_delta",
                    index=0,
                    delta=Mock(type="signature_delta", signature="sig_123"),
                ),
                AnthropicEventMock(
                    "content_block_start",
                    index=1,
                    content_block=content_block_mock,
                ),
                AnthropicEventMock(
                    "content_block_delta",
                    index=1,
                    delta=Mock(
                        type="input_json_delta",
                        partial_json='{"expression": "2+2"}',
                    ),
                ),
                AnthropicEventMock(
                    "message_delta",
                    usage=Mock(output_tokens=10),
                ),
            ]

            async def mock_stream() -> AsyncGenerator:
                for event in events:
                    yield event

            mock_client.messages.create = AsyncMock(return_value=mock_stream())
            result = await model(messages)
            responses = []
            async for response in result:
                responses.append(response)

            final_response = responses[-1]
            expected_thinking_block = ThinkingBlock(
                type="thinking",
                thinking="Let me think...",
            )
            expected_thinking_block["signature"] = "sig_123"

            assert final_response.content == [
                expected_thinking_block,
                ToolUseBlock(
                    type="tool_use",
                    id="tool_456",
                    name="calculate",
                    input={"expression": "2+2"},
                ),
            ]

    @pytest.mark.asyncio
    async def test_tool_choice_validation_through_api(self) -> None:
        """Test tool choice validation through API call."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Test"}]
            tools = [
                {
                    "type": "function",
                    "function": {"name": "test_tool"},
                },
            ]

            mock_response = AnthropicMessageMock(
                content=[
                    AnthropicContentBlockMock("text", text="Test response"),
                ],
                usage={"input_tokens": 5, "output_tokens": 10},
            )
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            test_cases = [
                ("auto", {"type": "auto"}),
                ("none", {"type": "none"}),
                ("any", {"type": "any"}),
                ("test_tool", {"type": "tool", "name": "test_tool"}),
            ]
            for tool_choice, expected_format in test_cases:
                await model(messages, tools=tools, tool_choice=tool_choice)
                call_args = mock_client.messages.create.call_args[1]
                assert call_args["tool_choice"] == expected_format

    @pytest.mark.asyncio
    async def test_generate_kwargs_integration(self) -> None:
        """Test integration of generate_kwargs."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            generate_kwargs = {"temperature": 0.7, "top_p": 0.9}
            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
                generate_kwargs=generate_kwargs,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Test"}]
            mock_response = AnthropicMessageMock(
                content=[
                    AnthropicContentBlockMock("text", text="Test response"),
                ],
                usage={"input_tokens": 5, "output_tokens": 10},
            )
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            # Test with additional kwargs
            await model(messages, top_k=40)
            call_args = mock_client.messages.create.call_args[1]
            assert call_args["temperature"] == 0.7
            assert call_args["top_p"] == 0.9
            assert call_args["top_k"] == 40  # from call kwargs

    @pytest.mark.asyncio
    async def test_call_with_structured_model_integration(self) -> None:
        """Test full integration of structured model."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]

            text_block = AnthropicContentBlockMock(
                "text",
                text="Here's a person",
            )
            tool_block = AnthropicContentBlockMock(
                "tool_use",
                id="tool_123",
                name="format_output",
                input={"name": "John", "age": 30},
            )

            mock_response = AnthropicMessageMock(
                content=[text_block, tool_block],
                usage={"input_tokens": 20, "output_tokens": 15},
            )

            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await model(messages, structured_model=SampleModel)

            # Verify API call includes structured model tools
            call_args = mock_client.messages.create.call_args[1]
            assert "tools" in call_args
            assert "tool_choice" in call_args
            expected_tools = [
                {
                    "name": "format_output",
                    "description": "Format output according to SampleModel "
                    "schema",
                    "input_schema": {
                        "description": "Sample Pydantic model for testing "
                        "structured output.",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                        },
                        "required": ["name", "age"],
                        "type": "object",
                    },
                },
            ]
            assert call_args["tools"] == expected_tools
            assert call_args["tool_choice"] == {
                "type": "tool",
                "name": "format_output",
            }

            # Verify result contains structured output in metadata
            assert isinstance(result, ChatResponse)
            assert result.content == [
                TextBlock(type="text", text="Here's a person"),
                ToolUseBlock(
                    type="tool_use",
                    id="tool_123",
                    name="format_output",
                    input={"name": "John", "age": 30},
                ),
            ]
            assert result.metadata == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_call_with_structured_model_warning(self) -> None:
        """Test warning when structured model overrides tools."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            tools = [
                {"type": "function", "function": {"name": "some_tool"}},
            ]
            mock_response = AnthropicMessageMock(
                content=[AnthropicContentBlockMock("text", text="Test")],
                usage={"input_tokens": 10, "output_tokens": 5},
            )

            with patch(
                "agentscope._utils._common._create_tool_from_model",
            ) as mock_create_tool, patch(
                "agentscope.model._anthropic_model.logger",
            ) as mock_logger:
                mock_create_tool.return_value = {
                    "type": "function",
                    "function": {
                        "name": "SampleModel",
                        "description": "Sample model",
                    },
                }
                mock_client.messages.create = AsyncMock(
                    return_value=mock_response,
                )

                await model(
                    messages,
                    tools=tools,
                    structured_model=SampleModel,
                )

                # Verify warning was logged
                mock_logger.warning.assert_called_once()
                warning_message = mock_logger.warning.call_args[0][0]
                assert "structured_model is provided" in warning_message
                assert (
                    "tools" in warning_message
                    and "tool_choice" in warning_message
                )

    @pytest.mark.asyncio
    async def test_streaming_with_structured_model(self) -> None:
        """Test streaming response with structured model."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=True,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]

            content_block_mock = Mock()
            content_block_mock.type = "tool_use"
            content_block_mock.id = "struct_123"
            content_block_mock.name = "SampleModel"

            events = [
                AnthropicEventMock(
                    "message_start",
                    message=Mock(
                        usage=Mock(input_tokens=15, output_tokens=0),
                    ),
                ),
                AnthropicEventMock(
                    "content_block_delta",
                    index=0,
                    delta=Mock(type="text_delta", text="Here's a person: "),
                ),
                AnthropicEventMock(
                    "content_block_start",
                    index=1,
                    content_block=content_block_mock,
                ),
                AnthropicEventMock(
                    "content_block_delta",
                    index=1,
                    delta=Mock(
                        type="input_json_delta",
                        partial_json='{"name": "Alice", "age": 25}',
                    ),
                ),
                AnthropicEventMock(
                    "message_delta",
                    usage=Mock(output_tokens=12),
                ),
            ]

            async def mock_stream() -> AsyncGenerator:
                for event in events:
                    yield event

            with patch(
                "agentscope._utils._common._create_tool_from_model",
            ) as mock_create_tool:
                mock_create_tool.return_value = {
                    "type": "function",
                    "function": {
                        "name": "SampleModel",
                        "description": "Sample model",
                    },
                }
                mock_client.messages.create = AsyncMock(
                    return_value=mock_stream(),
                )
                result = await model(
                    messages,
                    structured_model=SampleModel,
                )

                responses = []
                async for response in result:
                    responses.append(response)

                final_response = responses[-1]
                assert final_response.content == [
                    TextBlock(type="text", text="Here's a person: "),
                    ToolUseBlock(
                        type="tool_use",
                        id="struct_123",
                        name="SampleModel",
                        input={"name": "Alice", "age": 25},
                    ),
                ]
                # Verify structured output is in metadata
                assert final_response.metadata == {
                    "name": "Alice",
                    "age": 25,
                }

    @pytest.mark.asyncio
    async def test_structured_model_without_tools_in_response(self) -> None:
        """Test structured model when response doesn't contain tool calls."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            mock_response = AnthropicMessageMock(
                content=[
                    AnthropicContentBlockMock(
                        "text",
                        text="I can't generate that.",
                    ),
                ],
                usage={"input_tokens": 10, "output_tokens": 5},
            )

            with patch(
                "agentscope._utils._common._create_tool_from_model",
            ) as mock_create_tool:
                mock_create_tool.return_value = {
                    "type": "function",
                    "function": {
                        "name": "SampleModel",
                        "description": "Sample model",
                    },
                }
                mock_client.messages.create = AsyncMock(
                    return_value=mock_response,
                )
                result = await model(
                    messages,
                    structured_model=SampleModel,
                )

                # Verify result has no metadata when no tool calls
                assert result.content == [
                    TextBlock(type="text", text="I can't generate that."),
                ]
                assert result.metadata is None

    @pytest.mark.asyncio
    async def test_structured_model_with_invalid_json_input(self) -> None:
        """Test structured model with invalid JSON in tool input."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=True,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]

            content_block_mock = Mock()
            content_block_mock.type = "tool_use"
            content_block_mock.id = "invalid_123"
            content_block_mock.name = "format_output"

            events = [
                AnthropicEventMock(
                    "message_start",
                    message=Mock(
                        usage=Mock(input_tokens=10, output_tokens=0),
                    ),
                ),
                AnthropicEventMock(
                    "content_block_start",
                    index=0,
                    content_block=content_block_mock,
                ),
                AnthropicEventMock(
                    "content_block_delta",
                    index=0,
                    delta=Mock(
                        type="input_json_delta",
                        partial_json='{"name": "Bob", "age":',
                        # Invalid/incomplete JSON
                    ),
                ),
                AnthropicEventMock(
                    "message_delta",
                    usage=Mock(output_tokens=8),
                ),
            ]

            async def mock_stream() -> AsyncGenerator:
                for event in events:
                    yield event

            mock_client.messages.create = AsyncMock(return_value=mock_stream())
            result = await model(messages, structured_model=SampleModel)

            responses = []
            async for response in result:
                responses.append(response)

            final_response = responses[-1]
            # Should handle invalid JSON gracefully
            assert len(final_response.content) == 1
            assert final_response.content == [
                ToolUseBlock(
                    type="tool_use",
                    id="invalid_123",
                    name="format_output",
                    input={"name": "Bob", "age": ""},
                ),
            ]

    @pytest.mark.asyncio
    async def test_structured_model_tool_choice_formatting(self) -> None:
        """Test that structured model correctly formats tool choice."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate data"}]

            mock_response = AnthropicMessageMock(
                content=[
                    AnthropicContentBlockMock("text", text="Generated"),
                ],
                usage={"input_tokens": 5, "output_tokens": 3},
            )

            mock_client.messages.create = AsyncMock(return_value=mock_response)

            await model(messages, structured_model=SampleModel)

            call_args = mock_client.messages.create.call_args[1]
            # Verify tool choice is set to the specific model name
            assert call_args["tool_choice"] == {
                "type": "tool",
                "name": "format_output",
            }
            # Verify tools contains the converted model
            assert len(call_args["tools"]) == 1
            assert call_args["tools"][0]["name"] == "format_output"


class TestAnthropicIntegrationScenarios:
    """Integration test scenarios for Anthropic model."""

    @pytest.mark.asyncio
    async def test_complete_conversation_with_system_message(self) -> None:
        """Test complete conversation flow with system message."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            model = AnthropicChatModel(
                model_name="claude-3-opus-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant",
                },
                {"role": "user", "content": "Hello, how are you?"},
            ]

            mock_response = AnthropicMessageMock(
                content=[
                    AnthropicContentBlockMock(
                        "text",
                        text="I'm doing well, thank you for asking!",
                    ),
                ],
                usage={"input_tokens": 25, "output_tokens": 15},
            )
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await model(messages)
            # Verify system message handling
            call_args = mock_client.messages.create.call_args[1]
            assert call_args["system"] == "You are a helpful AI assistant"
            assert len(call_args["messages"]) == 1
            assert call_args["messages"][0]["role"] == "user"
            # Verify response
            assert isinstance(result, ChatResponse)
            assert result.content == [
                TextBlock(
                    type="text",
                    text="I'm doing well, thank you for asking!",
                ),
            ]
            assert result.usage.input_tokens == 25
            assert result.usage.output_tokens == 15

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_with_complex_tools(self) -> None:
        """Test multi-turn conversation with complex tool usage."""
        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = AnthropicChatModel(
                model_name="claude-3-sonnet-20240229",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [
                {
                    "role": "user",
                    "content": "Analyze the weather and recommend activities",
                },
            ]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get current weather information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string"},
                                "units": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                },
                            },
                            "required": ["location"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "suggest_activities",
                        "description": "Suggest activities based on weather",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "weather_condition": {"type": "string"},
                                "temperature": {"type": "number"},
                            },
                        },
                    },
                },
            ]

            # Mock response with multiple tool calls
            content_blocks = [
                AnthropicContentBlockMock(
                    "text",
                    text="I'll check the weather first.",
                ),
                AnthropicContentBlockMock(
                    "tool_use",
                    id="weather_call_1",
                    name="get_weather",
                    input={"location": "New York", "units": "celsius"},
                ),
                AnthropicContentBlockMock(
                    "tool_use",
                    id="activity_call_1",
                    name="suggest_activities",
                    input={"weather_condition": "sunny", "temperature": 22},
                ),
            ]
            mock_response = AnthropicMessageMock(
                content=content_blocks,
                usage={"input_tokens": 50, "output_tokens": 30},
            )
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            result = await model(messages, tools=tools, tool_choice="any")
            # Verify multiple tool calls in result
            assert result.content == [
                TextBlock(type="text", text="I'll check the weather first."),
                ToolUseBlock(
                    type="tool_use",
                    id="weather_call_1",
                    name="get_weather",
                    input={"location": "New York", "units": "celsius"},
                ),
                ToolUseBlock(
                    type="tool_use",
                    id="activity_call_1",
                    name="suggest_activities",
                    input={"weather_condition": "sunny", "temperature": 22},
                ),
            ]
