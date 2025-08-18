# -*- coding: utf-8 -*-
"""Unit tests for Google Gemini API model class."""
from typing import AsyncGenerator
from unittest.mock import Mock, patch, AsyncMock
import pytest
from pydantic import BaseModel

from agentscope.model import GeminiChatModel, ChatResponse
from agentscope.message import TextBlock, ToolUseBlock, ThinkingBlock


class GeminiResponseMock:
    """Mock class for Gemini response objects."""

    def __init__(
        self,
        text: str = "",
        function_calls: list = None,
        usage_metadata: dict = None,
        candidates: list = None,
    ):
        self.text = text
        self.function_calls = function_calls or []
        self.usage_metadata = (
            self._create_usage_mock(usage_metadata) if usage_metadata else None
        )
        self.candidates = candidates or []

    def _create_usage_mock(self, usage_data: dict) -> Mock:
        usage_mock = Mock()
        usage_mock.prompt_token_count = usage_data.get("prompt_token_count", 0)
        usage_mock.total_token_count = usage_data.get("total_token_count", 0)
        return usage_mock


class GeminiFunctionCallMock:
    """Mock class for Gemini function calls."""

    def __init__(self, call_id: str, name: str, args: dict = None):
        self.id = call_id
        self.name = name
        self.args = args or {}


class GeminiPartMock:
    """Mock class for Gemini content parts."""

    def __init__(self, text: str = "", thought: bool = False):
        self.text = text
        self.thought = thought


class GeminiCandidateMock:
    """Mock class for Gemini candidates."""

    def __init__(self, parts: list = None):
        self.content = Mock()
        self.content.parts = parts or []


class SampleModel(BaseModel):
    """Sample Pydantic model for testing structured output."""

    name: str
    age: int


class TestGeminiChatModel:
    """Test cases for GeminiChatModel."""

    def test_init_default_params(self) -> None:
        """Test initialization with default parameters."""
        with patch("google.genai.Client") as mock_client:
            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
                api_key="test_key",
            )
            assert model.model_name == "gemini-2.5-flash"
            assert model.stream is True
            assert model.thinking_config is None
            assert model.generate_kwargs == {}
            mock_client.assert_called_once_with(api_key="test_key")

    def test_init_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        thinking_config = {"include_thoughts": True, "thinking_budget": 1024}
        generate_kwargs = {"temperature": 0.7, "top_p": 0.9}
        client_args = {"timeout": 30}

        with patch("google.genai.Client") as mock_client:
            model = GeminiChatModel(
                model_name="gemini-2.5-pro",
                api_key="test_key",
                stream=False,
                thinking_config=thinking_config,
                client_args=client_args,
                generate_kwargs=generate_kwargs,
            )
            assert model.model_name == "gemini-2.5-pro"
            assert model.stream is False
            assert model.thinking_config == thinking_config
            assert model.generate_kwargs == generate_kwargs
            mock_client.assert_called_once_with(
                api_key="test_key",
                timeout=30,
            )

    def test_init_missing_gemini_package(self) -> None:
        """Test initialization when gemini package is missing."""
        with patch("builtins.__import__", side_effect=ImportError):
            with pytest.raises(
                ImportError,
                match="Please install gemini Python sdk",
            ):
                GeminiChatModel(
                    model_name="gemini-2.5-flash",
                    api_key="test_key",
                )

    @pytest.mark.asyncio
    async def test_call_with_regular_model(self) -> None:
        """Test calling a regular model."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client
            messages = [{"role": "user", "content": "Hello"}]
            mock_response = self._create_mock_response(
                "Hello! How can I help you?",
            )
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response,
            )

            result = await model(messages)
            call_args = mock_client.aio.models.generate_content.call_args[1]
            assert call_args["model"] == "gemini-2.5-flash"
            assert call_args["contents"] == messages
            assert isinstance(result, ChatResponse)
            assert result.content == [
                TextBlock(type="text", text="Hello! How can I help you?"),
            ]

    @pytest.mark.asyncio
    async def test_call_with_tools_integration(self) -> None:
        """Test full integration of tool calls."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
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
                    GeminiFunctionCallMock(
                        call_id="call_123",
                        name="get_weather",
                        args={"location": "Beijing"},
                    ),
                ],
            )

            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response,
            )
            result = await model(messages, tools=tools, tool_choice="auto")

            call_args = mock_client.aio.models.generate_content.call_args[1]
            assert "tools" in call_args["config"]
            assert "tool_config" in call_args["config"]
            expected_tools = [
                {
                    "function_declarations": [
                        {
                            "name": "get_weather",
                            "description": "Get weather info",
                            "parameters": {"type": "object"},
                        },
                    ],
                },
            ]
            assert call_args["config"]["tools"] == expected_tools
            assert call_args["config"]["tool_config"] == {
                "function_calling_config": {"mode": "AUTO"},
            }
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
    async def test_call_with_thinking_enabled(self) -> None:
        """Test calling with thinking functionality enabled."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            thinking_config = {
                "include_thoughts": True,
                "thinking_budget": 1024,
            }
            model = GeminiChatModel(
                model_name="gemini-2.5-pro",
                api_key="test_key",
                stream=False,
                thinking_config=thinking_config,
            )
            model.client = mock_client

            messages = [
                {"role": "user", "content": "Think about this problem"},
            ]
            thinking_part = GeminiPartMock(
                text="Let me analyze this step by step...",
                thought=True,
            )
            candidate = GeminiCandidateMock(parts=[thinking_part])
            mock_response = self._create_mock_response_with_thinking(
                "Here's my analysis",
                candidates=[candidate],
            )
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response,
            )
            result = await model(messages)

            call_args = mock_client.aio.models.generate_content.call_args[1]
            assert call_args["config"]["thinking_config"] == thinking_config
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
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            mock_response = self._create_mock_response(
                '{"name": "John", "age": 30}',
            )
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response,
            )

            result = await model(messages, structured_model=SampleModel)
            call_args = mock_client.aio.models.generate_content.call_args[1]
            assert (
                call_args["config"]["response_mime_type"] == "application/json"
            )
            assert call_args["config"]["response_schema"] == SampleModel
            assert "tools" not in call_args["config"]
            assert "tool_config" not in call_args["config"]

            assert isinstance(result, ChatResponse)
            assert result.metadata == {"name": "John", "age": 30}
            assert result.content == [
                TextBlock(type="text", text='{"name": "John", "age": 30}'),
            ]

    @pytest.mark.asyncio
    async def test_call_with_structured_model_warning(self) -> None:
        """Test warning when a structured model overrides tools."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            tools = [{"type": "function", "function": {"name": "some_tool"}}]
            mock_response = self._create_mock_response(
                '{"name": "Test", "age": 25}',
            )

            with patch("agentscope.model._gemini_model.logger") as mock_logger:
                mock_client.aio.models.generate_content = AsyncMock(
                    return_value=mock_response,
                )
                await model(
                    messages,
                    tools=tools,
                    structured_model=SampleModel,
                )
                mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_structured_model_with_invalid_json_response(self) -> None:
        """Test structured model handling when response contains invalid
        JSON."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            mock_response = self._create_mock_response(
                "This is not valid JSON",
            )
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response,
            )
            with pytest.raises(
                ValueError,
                match="Failed to decode JSON string",
            ):
                await model(messages, structured_model=SampleModel)

    @pytest.mark.asyncio
    async def test_streaming_response_processing(self) -> None:
        """Test processing of streaming response."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
                api_key="test_key",
                stream=True,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello"}]
            chunks = [
                self._create_mock_chunk(text="Hello"),
                self._create_mock_chunk(text=" there!"),
            ]

            mock_client.aio.models.generate_content_stream = AsyncMock(
                return_value=self._create_async_generator(chunks),
            )
            result = await model(messages)
            responses = []
            async for response in result:
                responses.append(response)

            assert len(responses) == 2
            final_response = responses[-1]
            assert final_response.content == [
                TextBlock(type="text", text="Hello there!"),
            ]

    @pytest.mark.asyncio
    async def test_streaming_with_thinking_and_tools(self) -> None:
        """Test streaming with thinking and tool calls."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-pro",
                api_key="test_key",
                stream=True,
                thinking_config={"include_thoughts": True},
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Calculate something"}]

            thinking_part = GeminiPartMock(
                text="Let me think...",
                thought=True,
            )
            candidate = GeminiCandidateMock(parts=[thinking_part])
            chunks = [
                self._create_mock_chunk(
                    text="I'll calculate this for you.",
                    candidates=[candidate],
                ),
                self._create_mock_chunk(
                    function_calls=[
                        GeminiFunctionCallMock(
                            call_id="calc_456",
                            name="calculate",
                            args={"expression": "2+2"},
                        ),
                    ],
                ),
            ]

            mock_client.aio.models.generate_content_stream = AsyncMock(
                return_value=self._create_async_generator(chunks),
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

    @pytest.mark.asyncio
    async def test_tool_choice_validation_through_api(self) -> None:
        """Test tool choice validation through API call."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
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

            mock_response = self._create_mock_response("Test response")

            test_cases = [
                ("auto", {"function_calling_config": {"mode": "AUTO"}}),
                ("none", {"function_calling_config": {"mode": "NONE"}}),
                ("any", {"function_calling_config": {"mode": "ANY"}}),
                (
                    "test_tool",
                    {
                        "function_calling_config": {
                            "mode": "ANY",
                            "allowed_function_names": ["test_tool"],
                        },
                    },
                ),
            ]

            for tool_choice, expected_format in test_cases:
                mock_client.aio.models.generate_content = AsyncMock(
                    return_value=mock_response,
                )
                await model(messages, tools=tools, tool_choice=tool_choice)
                call_args = mock_client.aio.models.generate_content.call_args[
                    1
                ]
                assert call_args["config"]["tool_config"] == expected_format

    @pytest.mark.asyncio
    async def test_generate_kwargs_integration(self) -> None:
        """Test integration of generate_kwargs."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            generate_kwargs = {"temperature": 0.7, "top_p": 0.9}
            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
                api_key="test_key",
                stream=False,
                generate_kwargs=generate_kwargs,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Test"}]
            mock_response = self._create_mock_response("Test response")
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response,
            )

            await model(messages, top_k=40)

            call_args = mock_client.aio.models.generate_content.call_args[1]
            assert call_args["config"]["temperature"] == 0.7
            assert call_args["config"]["top_p"] == 0.9
            assert call_args["config"]["top_k"] == 40

    # Auxiliary methods
    def _create_mock_response(
        self,
        text: str = "",
        usage_metadata: dict = None,
    ) -> GeminiResponseMock:
        """Create a standard mock response."""
        return GeminiResponseMock(
            text=text,
            usage_metadata=usage_metadata
            or {"prompt_token_count": 10, "total_token_count": 30},
        )

    def _create_mock_response_with_tools(
        self,
        text: str,
        function_calls: list,
        usage_metadata: dict = None,
    ) -> GeminiResponseMock:
        """Create a mock response containing tool calls."""
        return GeminiResponseMock(
            text=text,
            function_calls=function_calls,
            usage_metadata=usage_metadata
            or {"prompt_token_count": 20, "total_token_count": 50},
        )

    def _create_mock_response_with_thinking(
        self,
        text: str,
        candidates: list = None,
        usage_metadata: dict = None,
    ) -> GeminiResponseMock:
        """Create a mock response with thinking parts."""
        return GeminiResponseMock(
            text=text,
            candidates=candidates or [],
            usage_metadata=usage_metadata
            or {"prompt_token_count": 15, "total_token_count": 35},
        )

    def _create_mock_chunk(
        self,
        text: str = "",
        function_calls: list = None,
        candidates: list = None,
        usage_metadata: dict = None,
    ) -> GeminiResponseMock:
        """Create a mock chunk for streaming responses."""
        return GeminiResponseMock(
            text=text,
            function_calls=function_calls or [],
            candidates=candidates or [],
            usage_metadata=usage_metadata
            or {"prompt_token_count": 5, "total_token_count": 15},
        )

    async def _create_async_generator(self, items: list) -> AsyncGenerator:
        """Create an asynchronous generator."""
        for item in items:
            yield item


class TestGeminiIntegrationScenarios:
    """Integration test scenarios for Gemini model."""

    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self) -> None:
        """Test the complete conversation flow."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-pro",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello, how are you?"}]
            mock_response = GeminiResponseMock(
                text="I'm doing well, thank you for asking!",
                usage_metadata={
                    "prompt_token_count": 15,
                    "total_token_count": 40,
                },
            )

            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response,
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

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_with_tools(self) -> None:
        """Test multi-turn conversation with tools."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-flash",
                api_key="test_key",
                stream=False,
            )
            model.client = mock_client

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

            mock_response = GeminiResponseMock(
                text="Let me check the weather for you.",
                function_calls=[
                    GeminiFunctionCallMock(
                        call_id="call_123",
                        name="get_weather",
                        args={"location": "Beijing"},
                    ),
                ],
                usage_metadata={
                    "prompt_token_count": 20,
                    "total_token_count": 50,
                },
            )
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response,
            )
            result = await model(messages, tools=tools, tool_choice="auto")

            assert result.content == [
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

    @pytest.mark.asyncio
    async def test_streaming_with_complex_content(self) -> None:
        """Test streaming processing with complex content."""
        with patch("google.genai.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = GeminiChatModel(
                model_name="gemini-2.5-pro",
                api_key="test_key",
                stream=True,
                thinking_config={"include_thoughts": True},
            )
            model.client = mock_client

            messages = [
                {"role": "user", "content": "Solve this complex problem"},
            ]

            # Mock complex streaming response
            thinking_part1 = GeminiPartMock(
                text="Let me analyze this step by step.",
                thought=True,
            )
            thinking_part2 = GeminiPartMock(
                text=" First, I need to understand the requirements.",
                thought=True,
            )
            candidate1 = GeminiCandidateMock(parts=[thinking_part1])
            candidate2 = GeminiCandidateMock(parts=[thinking_part2])

            chunks = [
                # First chunk: Start thinking
                GeminiResponseMock(
                    text="",
                    candidates=[candidate1],
                    usage_metadata={
                        "prompt_token_count": 10,
                        "total_token_count": 15,
                    },
                ),
                # Second chunk: Continue thinking and start answering
                GeminiResponseMock(
                    text="To solve this problem, ",
                    candidates=[candidate2],
                    usage_metadata={
                        "prompt_token_count": 10,
                        "total_token_count": 25,
                    },
                ),
                # Third chunk: Tool call
                GeminiResponseMock(
                    text="I'll use a calculation tool.",
                    function_calls=[
                        GeminiFunctionCallMock(
                            call_id="calc_789",
                            name="calculate",
                            args={"expression": "2+2"},
                        ),
                    ],
                    usage_metadata={
                        "prompt_token_count": 10,
                        "total_token_count": 35,
                    },
                ),
            ]

            async def mock_generator() -> AsyncGenerator:
                for chunk in chunks:
                    yield chunk

            mock_client.aio.models.generate_content_stream = AsyncMock(
                return_value=mock_generator(),
            )

            result = await model(messages)
            responses = []
            async for response in result:
                responses.append(response)

            assert len(responses) == 3
            final_response = responses[-1]

            assert final_response.content == [
                ThinkingBlock(
                    type="thinking",
                    thinking="Let me analyze this step by step. First, "
                    "I need to understand the requirements.",
                ),
                TextBlock(
                    type="text",
                    text="To solve this problem, I'll use a calculation tool.",
                ),
                ToolUseBlock(
                    type="tool_use",
                    id="calc_789",
                    name="calculate",
                    input={"expression": "2+2"},
                ),
            ]
