# -*- coding: utf-8 -*-
"""Unit tests for Ollama API model class."""
from typing import AsyncGenerator, Any
from unittest.mock import patch, AsyncMock
import pytest
from pydantic import BaseModel

from agentscope.model import OllamaChatModel, ChatResponse
from agentscope.message import TextBlock, ToolUseBlock, ThinkingBlock


class OllamaMessageMock:
    """Mock class for Ollama message objects."""

    def __init__(
        self,
        content: str = "",
        thinking: str = "",
        tool_calls: list = None,
    ):
        self.content = content
        self.thinking = thinking
        self.tool_calls = tool_calls or []


class OllamaFunctionMock:
    """Mock class for Ollama function objects."""

    def __init__(self, name: str, arguments: dict = None):
        self.name = name
        self.arguments = arguments or {}


class OllamaToolCallMock:
    """Mock class for Ollama tool call objects."""

    def __init__(
        self,
        call_id: str = None,
        function: OllamaFunctionMock = None,
    ):
        self.id = call_id
        self.function = function


class OllamaResponseMock:
    """Mock class for Ollama response objects."""

    def __init__(
        self,
        message: OllamaMessageMock = None,
        done: bool = True,
        prompt_eval_count: int = 0,
        eval_count: int = 0,
    ) -> None:
        self.message = message or OllamaMessageMock()
        self.done = done
        self.prompt_eval_count = prompt_eval_count
        self.eval_count = eval_count

    def get(self, key: str, default: Any = None) -> Any:
        """Mock dict-like get method."""
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        """Mock dict-like contains method."""
        return hasattr(self, key)


class SampleModel(BaseModel):
    """Sample Pydantic model for testing structured output."""

    name: str
    age: int


class TestOllamaChatModel:
    """Test cases for OllamaChatModel."""

    def test_init_default_params(self) -> None:
        """Test initialization with default parameters."""
        with patch("ollama.AsyncClient") as mock_client:
            model = OllamaChatModel(model_name="llama3.2")
            assert model.model_name == "llama3.2"
            assert model.stream is False
            assert model.options is None
            assert model.keep_alive == "5m"
            assert model.think is None
            mock_client.assert_called_once_with(host=None)

    def test_init_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        options = {"temperature": 0.7, "top_p": 0.9}
        with patch("ollama.AsyncClient") as mock_client:
            model = OllamaChatModel(
                model_name="qwen2.5",
                stream=True,
                options=options,
                keep_alive="10m",
                enable_thinking=True,
                host="http://localhost:11434",
                timeout=30,
            )
            assert model.model_name == "qwen2.5"
            assert model.stream is True
            assert model.options == options
            assert model.keep_alive == "10m"
            assert model.think is True
            mock_client.assert_called_once_with(
                host="http://localhost:11434",
                timeout=30,
            )

    def test_init_missing_ollama_package(self) -> None:
        """Test initialization when ollama package is missing."""
        with patch("builtins.__import__", side_effect=ImportError):
            with pytest.raises(
                ImportError,
                match="The package ollama is not found",
            ):
                OllamaChatModel(model_name="llama3.2")

    @pytest.mark.asyncio
    async def test_call_with_regular_model(self) -> None:
        """Test calling a regular model."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(model_name="llama3.2", stream=False)
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello"}]
            mock_response = self._create_mock_response(
                "Hello! How can I help you?",
            )
            mock_client.chat = AsyncMock(return_value=mock_response)

            result = await model(messages)
            call_args = mock_client.chat.call_args[1]
            assert call_args["model"] == "llama3.2"
            assert call_args["messages"] == messages
            assert call_args["stream"] is False
            assert isinstance(result, ChatResponse)
            assert result.content == [
                TextBlock(type="text", text="Hello! How can I help you?"),
            ]

    @pytest.mark.asyncio
    async def test_call_with_tools_integration(self) -> None:
        """Test full integration of tool calls."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(model_name="llama3.2", stream=False)
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

            function_mock = OllamaFunctionMock(
                name="get_weather",
                arguments={"location": "Beijing"},
            )
            tool_call_mock = OllamaToolCallMock(
                call_id="call_123",
                function=function_mock,
            )
            message_mock = OllamaMessageMock(
                content="I'll check the weather for you.",
                tool_calls=[tool_call_mock],
            )
            mock_response = self._create_mock_response_with_message(
                message_mock,
            )

            mock_client.chat = AsyncMock(return_value=mock_response)
            result = await model(messages, tools=tools)

            call_args = mock_client.chat.call_args[1]
            assert "tools" in call_args
            assert call_args["tools"] == tools
            assert result.content == [
                TextBlock(type="text", text="I'll check the weather for you."),
                ToolUseBlock(
                    type="tool_use",
                    id="get_weather",
                    name="get_weather",
                    input={"location": "Beijing"},
                ),
            ]

    @pytest.mark.asyncio
    async def test_call_with_tool_choice_warning(self) -> None:
        """Test warning when tool_choice is provided."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(model_name="llama3.2", stream=False)
            model.client = mock_client

            messages = [{"role": "user", "content": "Test"}]
            tools = [{"type": "function", "function": {"name": "test_tool"}}]
            mock_response = self._create_mock_response("Test response")

            with patch("agentscope.model._ollama_model.logger") as mock_logger:
                mock_client.chat = AsyncMock(return_value=mock_response)
                await model(messages, tools=tools, tool_choice="auto")
                mock_logger.warning.assert_called_once_with(
                    "Ollama does not support tool_choice yet, ignored.",
                )

    @pytest.mark.asyncio
    async def test_call_with_thinking_enabled(self) -> None:
        """Test calling with thinking functionality enabled."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(
                model_name="qwen2.5",
                stream=False,
                enable_thinking=True,
            )
            model.client = mock_client

            messages = [
                {"role": "user", "content": "Think about this problem"},
            ]
            message_mock = OllamaMessageMock(
                content="Here's my analysis",
                thinking="Let me analyze this step by step...",
            )
            mock_response = self._create_mock_response_with_message(
                message_mock,
            )

            mock_client.chat = AsyncMock(return_value=mock_response)
            result = await model(messages)

            call_args = mock_client.chat.call_args[1]
            assert call_args["think"] is True
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
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(model_name="llama3.2", stream=False)
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            mock_response = self._create_mock_response(
                '{"name": "John", "age": 30}',
            )
            mock_client.chat = AsyncMock(return_value=mock_response)

            result = await model(messages, structured_model=SampleModel)
            call_args = mock_client.chat.call_args[1]
            assert "format" in call_args
            assert call_args["format"] == SampleModel.model_json_schema()
            assert isinstance(result, ChatResponse)
            assert result.metadata == {"name": "John", "age": 30}
            assert result.content == [
                TextBlock(type="text", text='{"name": "John", "age": 30}'),
            ]

    @pytest.mark.asyncio
    async def test_structured_model_with_invalid_json_response(self) -> None:
        """Test structured model handling when response contains invalid
        JSON."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(model_name="llama3.2", stream=False)
            model.client = mock_client

            messages = [{"role": "user", "content": "Generate a person"}]
            mock_response = self._create_mock_response(
                "This is not valid JSON",
            )
            mock_client.chat = AsyncMock(return_value=mock_response)

            with pytest.raises(
                ValueError,
                match="Failed to decode JSON string",
            ):
                await model(messages, structured_model=SampleModel)

    @pytest.mark.asyncio
    async def test_streaming_response_processing(self) -> None:
        """Test processing of streaming response."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(model_name="llama3.2", stream=True)
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello"}]
            chunks = [
                self._create_mock_chunk(content="Hello", done=False),
                self._create_mock_chunk(content=" there!", done=True),
            ]

            mock_client.chat = AsyncMock(
                return_value=self._create_async_generator(chunks),
            )
            result = await model(messages)
            responses = []
            async for response in result:
                responses.append(response)

            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.content == [
                TextBlock(type="text", text="Hello there!"),
            ]

    @pytest.mark.asyncio
    async def test_streaming_with_thinking_and_tools(self) -> None:
        """Test streaming with thinking and tool calls."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(
                model_name="qwen2.5",
                stream=True,
                enable_thinking=True,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Calculate something"}]

            function_mock = OllamaFunctionMock(
                name="calculate",
                arguments={"expression": "2+2"},
            )
            tool_call_mock = OllamaToolCallMock(function=function_mock)

            chunks = [
                self._create_mock_chunk(
                    content="I'll calculate this for you.",
                    thinking="Let me think...",
                    done=False,
                ),
                self._create_mock_chunk(
                    tool_calls=[tool_call_mock],
                    done=True,
                ),
            ]

            mock_client.chat = AsyncMock(
                return_value=self._create_async_generator(chunks),
            )
            result = await model(messages)
            responses = []
            async for response in result:
                responses.append(response)

            final_response = responses[-1]
            assert isinstance(final_response, ChatResponse)

            assert final_response.content == [
                ThinkingBlock(
                    type="thinking",
                    thinking="Let me think...",
                ),
                TextBlock(type="text", text="I'll calculate this for you."),
                ToolUseBlock(
                    type="tool_use",
                    id=tool_call_mock.id,
                    name=tool_call_mock.function.name,
                    input=tool_call_mock.function.arguments,
                ),
            ]

    @pytest.mark.asyncio
    async def test_options_integration(self) -> None:
        """Test integration of options parameter."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            options = {"temperature": 0.7, "top_p": 0.9}
            model = OllamaChatModel(
                model_name="llama3.2",
                stream=False,
                options=options,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Test"}]
            mock_response = self._create_mock_response("Test response")
            mock_client.chat = AsyncMock(return_value=mock_response)

            await model(messages, top_k=40)

            call_args = mock_client.chat.call_args[1]
            assert call_args["options"] == options
            assert call_args["keep_alive"] == "5m"
            assert call_args["top_k"] == 40

    @pytest.mark.asyncio
    async def test_think_parameter_override(self) -> None:
        """Test think parameter can be overridden in call."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(
                model_name="qwen2.5",
                stream=False,
                enable_thinking=True,
            )
            model.client = mock_client

            messages = [{"role": "user", "content": "Test"}]
            mock_response = self._create_mock_response("Test response")
            mock_client.chat = AsyncMock(return_value=mock_response)

            # Override think parameter in call
            await model(messages, think=False)

            call_args = mock_client.chat.call_args[1]
            assert call_args["think"] is False

    # Auxiliary methods
    def _create_mock_response(
        self,
        content: str = "",
        prompt_eval_count: int = 10,
        eval_count: int = 20,
    ) -> OllamaResponseMock:
        """Create a standard mock response."""
        message = OllamaMessageMock(content=content)
        return OllamaResponseMock(
            message=message,
            prompt_eval_count=prompt_eval_count,
            eval_count=eval_count,
        )

    def _create_mock_response_with_message(
        self,
        message: OllamaMessageMock,
        prompt_eval_count: int = 10,
        eval_count: int = 20,
    ) -> OllamaResponseMock:
        """Create a mock response with specific message."""
        return OllamaResponseMock(
            message=message,
            prompt_eval_count=prompt_eval_count,
            eval_count=eval_count,
        )

    def _create_mock_chunk(
        self,
        content: str = "",
        thinking: str = "",
        tool_calls: list = None,
        done: bool = True,
        prompt_eval_count: int = 5,
        eval_count: int = 10,
    ) -> OllamaResponseMock:
        """Create a mock chunk for streaming responses."""
        message = OllamaMessageMock(
            content=content,
            thinking=thinking,
            tool_calls=tool_calls or [],
        )
        return OllamaResponseMock(
            message=message,
            done=done,
            prompt_eval_count=prompt_eval_count,
            eval_count=eval_count,
        )

    async def _create_async_generator(self, items: list) -> AsyncGenerator:
        """Create an asynchronous generator."""
        for item in items:
            yield item


class TestOllamaIntegrationScenarios:
    """Integration test scenarios for Ollama model."""

    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self) -> None:
        """Test the complete conversation flow."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(model_name="llama3.2", stream=False)
            model.client = mock_client

            messages = [{"role": "user", "content": "Hello, how are you?"}]
            mock_response = OllamaResponseMock(
                message=OllamaMessageMock(
                    content="I'm doing well, thank you for asking!",
                ),
                prompt_eval_count=15,
                eval_count=25,
            )

            mock_client.chat = AsyncMock(return_value=mock_response)
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
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(model_name="llama3.2", stream=False)
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

            function_mock = OllamaFunctionMock(
                name="get_weather",
                arguments={"location": "Beijing"},
            )
            tool_call_mock = OllamaToolCallMock(function=function_mock)
            message_mock = OllamaMessageMock(
                content="Let me check the weather for you.",
                tool_calls=[tool_call_mock],
            )
            mock_response = OllamaResponseMock(
                message=message_mock,
                prompt_eval_count=20,
                eval_count=30,
            )

            mock_client.chat = AsyncMock(return_value=mock_response)
            result = await model(messages, tools=tools)

            assert result.content == [
                TextBlock(
                    type="text",
                    text="Let me check the weather for you.",
                ),
                ToolUseBlock(
                    type="tool_use",
                    id="get_weather",
                    name="get_weather",
                    input={"location": "Beijing"},
                ),
            ]

    @pytest.mark.asyncio
    async def test_streaming_with_complex_content(self) -> None:
        """Test streaming processing with complex content."""
        with patch("ollama.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            model = OllamaChatModel(
                model_name="qwen2.5",
                stream=True,
                enable_thinking=True,
            )
            model.client = mock_client

            messages = [
                {"role": "user", "content": "Solve this complex problem"},
            ]

            function_mock = OllamaFunctionMock(
                name="calculate",
                arguments={"expression": "2+2"},
            )
            tool_call_mock = OllamaToolCallMock(
                call_id="call_123",
                function=function_mock,
            )

            chunks = [
                # First chunk: Start thinking
                OllamaResponseMock(
                    message=OllamaMessageMock(
                        content="",
                        thinking="Let me analyze this step by step.",
                    ),
                    done=False,
                    prompt_eval_count=10,
                    eval_count=5,
                ),
                # Second chunk: Continue thinking and start answering
                OllamaResponseMock(
                    message=OllamaMessageMock(
                        content="To solve this problem, ",
                        thinking=" First, I need to understand the "
                        "requirements.",
                    ),
                    done=False,
                    prompt_eval_count=10,
                    eval_count=15,
                ),
                # Third chunk: Tool call
                OllamaResponseMock(
                    message=OllamaMessageMock(
                        content="I'll use a calculation tool.",
                        tool_calls=[tool_call_mock],
                    ),
                    done=True,
                    prompt_eval_count=10,
                    eval_count=25,
                ),
            ]

            async def mock_generator() -> AsyncGenerator:
                for chunk in chunks:
                    yield chunk

            mock_client.chat = AsyncMock(return_value=mock_generator())

            result = await model(messages)
            responses = []
            async for response in result:
                responses.append(response)

            assert len(responses) >= 1
            final_response = responses[-1]

            # Check that we have thinking, text, and tool use blocks
            assert isinstance(final_response, ChatResponse)

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
                    id="call_123",
                    name="calculate",
                    input={"expression": "2+2"},
                ),
            ]
