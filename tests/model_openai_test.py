# -*- coding: utf-8 -*-
"""Unit tests for OpenAI API model class."""
from typing import AsyncGenerator, Any
from unittest.mock import Mock, patch, AsyncMock
import pytest
from pydantic import BaseModel

from agentscope.model import OpenAIChatModel, ChatResponse
from agentscope.message import TextBlock, ToolUseBlock, ThinkingBlock


class SampleModel(BaseModel):
    """Sample Pydantic model for testing structured output."""

    name: str
    age: int


class TestOpenAIChatModel:
    """Test cases for OpenAIChatModel."""

    def test_init_default_params(self) -> None:
        """Test initialization with default parameters."""
        with patch("openai.AsyncClient") as mock_client:
            model = OpenAIChatModel(
                model_name="gpt-4",
                api_key="test_key",
            )
            assert model.model_name == "gpt-4"
            assert model.stream is True
            assert model.reasoning_effort is None
            assert model.generate_kwargs == {}
            mock_client.assert_called_once_with(
                api_key="test_key",
                organization=None,
            )

    def test_init_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        generate_kwargs = {"temperature": 0.7, "max_tokens": 1000}
        client_args = {"timeout": 30}
        with patch("openai.AsyncClient") as mock_client:
            model = OpenAIChatModel(
                model_name="gpt-4o",
                api_key="test_key",
                stream=False,
                reasoning_effort="high",
                organization="org-123",
                client_args=client_args,
                generate_kwargs=generate_kwargs,
            )
            assert model.model_name == "gpt-4o"
            assert model.stream is False
            assert model.reasoning_effort == "high"
            assert model.generate_kwargs == generate_kwargs
            mock_client.assert_called_once_with(
                api_key="test_key",
                organization="org-123",
                timeout=30,
            )

    @pytest.mark.asyncio
    async def test_call_with_invalid_messages_format(self) -> None:
        """Test calling with invalid messages format."""
        with patch("openai.AsyncClient"):
            model = OpenAIChatModel(model_name="gpt-4", api_key="test_key")
            # Test non-list messages
            with pytest.raises(ValueError, match="expected type `list`"):
                await model("invalid messages")
            # Test messages without required fields
            invalid_messages = [{"role": "user"}]  # missing content
            with pytest.raises(
                ValueError,
                match="must contain a 'role' and 'content' key",
            ):
                await model(invalid_messages)

    @pytest.mark.asyncio
    async def test_call_with_regular_model(self) -> None:
        """Test calling a regular model."""
        with patch("openai.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OpenAIChatModel(
                model_name="gpt-4",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello"}]
            mock_response = self._create_mock_response(
                "Hello! How can I help you?",
            )
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_response,
            )

            result = await model(messages)
            call_args = mock_client.chat.completions.create.call_args[1]
            assert call_args["model"] == "gpt-4"
            assert call_args["messages"] == messages
            assert call_args["stream"] is False
            assert isinstance(result, ChatResponse)
            assert result.content == [
                TextBlock(type="text", text="Hello! How can I help you?"),
            ]

    @pytest.mark.asyncio
    async def test_call_with_tools_integration(self) -> None:
        """Test full integration of tool calls."""
        with patch("openai.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OpenAIChatModel(
                model_name="gpt-4",
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

            mock_response = self._create_mock_response_with_tools(
                "I'll check the weather for you.",
                [
                    {
                        "id": "call_123",
                        "name": "get_weather",
                        "arguments": '{"location": "Beijing"}',
                    },
                ],
            )
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_response,
            )
            result = await model(messages, tools=tools, tool_choice="auto")
            call_args = mock_client.chat.completions.create.call_args[1]
            assert "tools" in call_args
            assert call_args["tools"] == tools
            assert call_args["tool_choice"] == "auto"
            assert result.content == [
                TextBlock(type="text", text="I'll check the weather for you."),
                ToolUseBlock(
                    type="tool_use",
                    id="call_123",
                    name="get_weather",
                    input={"location": "Beijing"},
                ),
            ]

    @pytest.mark.asyncio
    async def test_call_with_reasoning_effort(self) -> None:
        """Test calling with reasoning effort enabled."""
        with patch("openai.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OpenAIChatModel(
                model_name="o3-mini",
                api_key="test_key",
                stream=False,
                reasoning_effort="high",
            )
            model.client = mock_client

            messages = [
                {"role": "user", "content": "Think about this problem"},
            ]
            mock_response = self._create_mock_response_with_reasoning(
                "Here's my analysis",
                "Let me analyze this step by step...",
            )
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_response,
            )
            result = await model(messages)

            call_args = mock_client.chat.completions.create.call_args[1]
            assert call_args["reasoning_effort"] == "high"
            assert result.content == [
                ThinkingBlock(
                    type="thinking",
                    thinking="Let me analyze this step by step...",
                ),
                TextBlock(type="text", text="Here's my analysis"),
            ]

    @pytest.mark.asyncio
    async def test_call_with_structured_model_integration(self) -> None:
        """Test full integration of a structured model."""
        with patch("openai.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OpenAIChatModel(
                model_name="gpt-4",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            mock_response = self._create_mock_response_with_structured_data(
                {"name": "John", "age": 30},
            )
            mock_client.chat.completions.parse = AsyncMock(
                return_value=mock_response,
            )

            result = await model(messages, structured_model=SampleModel)
            call_args = mock_client.chat.completions.parse.call_args[1]
            assert call_args["response_format"] == SampleModel
            assert "tools" not in call_args
            assert "tool_choice" not in call_args
            assert "stream" not in call_args
            assert isinstance(result, ChatResponse)
            assert result.metadata == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_call_with_structured_model_warning(self) -> None:
        """Test warning when a structured model overrides tools."""
        with patch("openai.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OpenAIChatModel(
                model_name="gpt-4",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            tools = [{"type": "function", "function": {"name": "some_tool"}}]
            mock_response = self._create_mock_response_with_structured_data({})

            with patch("agentscope.model._openai_model.logger") as mock_logger:
                mock_client.chat.completions.parse = AsyncMock(
                    return_value=mock_response,
                )
                await model(
                    messages,
                    tools=tools,
                    structured_model=SampleModel,
                )
                mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_streaming_response_processing(self) -> None:
        """Test processing of streaming response."""
        with patch("openai.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OpenAIChatModel(
                model_name="gpt-4",
                api_key="test_key",
                stream=True,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello"}]
            # Create simple stream mock
            stream_mock = self._create_stream_mock(
                [
                    {"content": "Hello"},
                    {"content": " there!"},
                ],
            )

            mock_client.chat.completions.create = AsyncMock(
                return_value=stream_mock,
            )
            result = await model(messages)

            call_args = mock_client.chat.completions.create.call_args[1]
            assert call_args["stream_options"] == {"include_usage": True}
            responses = []
            async for response in result:
                responses.append(response)

            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.content == [
                TextBlock(type="text", text="Hello there!"),
            ]

    @pytest.mark.asyncio
    async def test_streaming_with_reasoning_and_tools(self) -> None:
        """Test streaming with reasoning and tool calls."""
        with patch("openai.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OpenAIChatModel(
                model_name="o3-mini",
                api_key="test_key",
                stream=True,
                reasoning_effort="medium",
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Calculate something"}]

            stream_mock = self._create_stream_mock(
                [
                    {
                        "content": "I'll calculate this for you.",
                        "reasoning_content": "Let me think...",
                    },
                    {
                        "tool_calls": [
                            {
                                "id": "calc_456",
                                "name": "calculate",
                                "arguments": '{"expression": "2+2"}',
                            },
                        ],
                    },
                ],
            )
            mock_client.chat.completions.create = AsyncMock(
                return_value=stream_mock,
            )
            result = await model(messages)

            responses = []
            async for response in result:
                responses.append(response)

            final_response = responses[-1]
            assert final_response.content == [
                ThinkingBlock(type="thinking", thinking="Let me think..."),
                TextBlock(type="text", text="I'll calculate this for you."),
                ToolUseBlock(
                    type="tool_use",
                    id="calc_456",
                    name="calculate",
                    input={"expression": "2+2"},
                ),
            ]

    # Auxiliary methods - ensure all Mock objects have complete attributes
    def _create_mock_response(
        self,
        content: str = "",
        prompt_tokens: int = 10,
        completion_tokens: int = 20,
    ) -> Mock:
        """Create a standard mock response."""
        # Create message mock, ensuring all necessary attributes are present
        message = Mock()
        message.content = content
        message.reasoning_content = None
        message.tool_calls = []  # Real empty list
        message.parsed = None  # For structured output, even if unused

        # Create choice mock
        choice = Mock()
        choice.message = message

        # Create response mock, ensuring choices is a real list
        response = Mock()
        response.choices = [choice]  # Real list

        # Create usage mock
        usage = Mock()
        usage.prompt_tokens = prompt_tokens
        usage.completion_tokens = completion_tokens
        response.usage = usage
        return response

    def _create_mock_response_with_tools(
        self,
        content: str,
        tool_calls: list,
    ) -> Mock:
        """Create a mock response with tool calls."""
        response = self._create_mock_response(content)
        # Create real list of tool call mocks
        tool_call_mocks = []
        for tool_call in tool_calls:
            tc_mock = Mock()
            tc_mock.id = tool_call["id"]
            tc_mock.function = Mock()
            tc_mock.function.name = tool_call["name"]
            tc_mock.function.arguments = tool_call["arguments"]
            tool_call_mocks.append(tc_mock)
        # Set as real list
        response.choices[0].message.tool_calls = tool_call_mocks
        return response

    def _create_mock_response_with_reasoning(
        self,
        content: str,
        reasoning_content: str,
    ) -> Mock:
        """Create a mock response with reasoning content."""
        response = self._create_mock_response(content)
        response.choices[0].message.reasoning_content = reasoning_content
        return response

    def _create_mock_response_with_structured_data(self, data: dict) -> Mock:
        """Create a mock response with structured data."""
        # Create complete message mock
        message = Mock()
        message.parsed = Mock()
        message.parsed.model_dump.return_value = data
        # Ensure all other attributes are present
        message.content = None
        message.reasoning_content = None
        message.tool_calls = []  # Real empty list

        # Create choice mock
        choice = Mock()
        choice.message = message

        # Create response mock, ensuring choices is a real list
        response = Mock()
        response.choices = [choice]  # Real list

        # Add usage (though structured response may not need it)
        response.usage = None

        return response

    def _create_stream_mock(self, chunks_data: list) -> Any:
        """Create a mock stream with proper async context management."""

        class MockStream:
            """Mock stream class."""

            def __init__(self, chunks_data: list) -> None:
                self.chunks_data = chunks_data
                self.index = 0

            async def __aenter__(self) -> "MockStream":
                return self

            async def __aexit__(
                self,
                exc_type: Any,
                exc_val: Any,
                exc_tb: Any,
            ) -> None:
                pass

            def __aiter__(self) -> "MockStream":
                return self

            async def __anext__(self) -> AsyncGenerator:
                if self.index >= len(self.chunks_data):
                    raise StopAsyncIteration
                chunk_data = self.chunks_data[self.index]
                self.index += 1

                # Create delta mock
                delta = Mock()
                delta.content = chunk_data.get("content")
                delta.reasoning_content = chunk_data.get("reasoning_content")
                # Handle tool_calls, ensuring it's always a list
                if "tool_calls" in chunk_data:
                    tool_call_mocks = []
                    for tc_data in chunk_data["tool_calls"]:
                        tc_mock = Mock()
                        tc_mock.id = tc_data["id"]
                        tc_mock.index = 0
                        tc_mock.function = Mock()
                        tc_mock.function.name = tc_data["name"]
                        tc_mock.function.arguments = tc_data["arguments"]
                        tool_call_mocks.append(tc_mock)
                    delta.tool_calls = tool_call_mocks
                else:
                    delta.tool_calls = []  # Empty list instead of None

                # Create choice mock
                choice = Mock()
                choice.delta = delta

                # Create chunk mock, ensuring choices is a real list
                chunk = Mock()
                chunk.choices = [choice]  # Real list
                chunk.usage = Mock()
                chunk.usage.prompt_tokens = 5
                chunk.usage.completion_tokens = 10
                return chunk

        return MockStream(chunks_data)


class TestOpenAIIntegrationScenarios:
    """Integration test scenarios for OpenAI model."""

    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self) -> None:
        """Test the complete conversation flow."""
        with patch("openai.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OpenAIChatModel(
                model_name="gpt-4",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello, how are you?"}]

            # Create complete message mock, ensuring all attributes are present
            message = Mock()
            message.content = "I'm doing well, thank you for asking!"
            message.reasoning_content = None
            message.tool_calls = []  # Real empty list
            message.parsed = None

            # Create choice mock
            choice = Mock()
            choice.message = message
            # Create response mock, ensuring choices is a real list
            response = Mock()
            response.choices = [choice]  # Real list

            # Create usage mock
            usage = Mock()
            usage.prompt_tokens = 15
            usage.completion_tokens = 25
            response.usage = usage

            mock_client.chat.completions.create = AsyncMock(
                return_value=response,
            )
            result = await model(messages)

            assert isinstance(result, ChatResponse)
            assert result.content == [
                TextBlock(
                    type="text",
                    text="I'm doing well, thank you for asking!",
                ),
            ]
            assert result.usage.input_tokens == 15
            assert result.usage.output_tokens == 25
