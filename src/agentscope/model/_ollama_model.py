# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches
"""Model wrapper for Ollama models."""
from datetime import datetime
from typing import (
    Any,
    TYPE_CHECKING,
    List,
    AsyncGenerator,
    AsyncIterator,
    Literal,
)
from collections import OrderedDict

from . import ChatResponse
from ._model_base import ChatModelBase
from ._model_usage import ChatUsage
from .._logging import logger
from .._utils._common import _json_loads_with_repair
from ..message import ToolUseBlock, TextBlock, ThinkingBlock
from ..tracing import trace_llm


if TYPE_CHECKING:
    from ollama._types import OllamaChatResponse
else:
    OllamaChatResponse = "ollama._types.ChatResponse"


class OllamaChatModel(ChatModelBase):
    """The Ollama chat model class in agentscope."""

    def __init__(
        self,
        model_name: str,
        stream: bool = False,
        options: dict = None,
        keep_alive: str = "5m",
        enable_thinking: bool | None = None,
        host: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Ollama chat model.

        Args:
           model_name (`str`):
               The name of the model.
           stream (`bool`, default `True`):
               Streaming mode or not.
           options (`dict`, default `None`):
               Additional parameters to pass to the Ollama API. These can
               include temperature etc.
           keep_alive (`str`, default `"5m"`):
               Duration to keep the model loaded in memory. The format is a
               number followed by a unit suffix (s for seconds, m for minutes
               , h for hours).
           enable_thinking (`bool | None`, default `None`)
               Whether enable thinking or not, only for models such as qwen3,
               deepseek-r1, etc. For more details, please refer to
               https://ollama.com/search?c=thinking
           host (`str | None`, default `None`):
               The host address of the Ollama server. If None, uses the
               default address (typically http://localhost:11434).
           **kwargs (`Any`):
               Additional keyword arguments to pass to the base chat model
               class.
        """

        try:
            import ollama
        except ImportError as e:
            raise ImportError(
                "The package ollama is not found. Please install it by "
                'running command `pip install "ollama>=0.1.7"`',
            ) from e

        super().__init__(model_name, stream)

        self.client = ollama.AsyncClient(
            host=host,
            **kwargs,
        )
        self.options = options
        self.keep_alive = keep_alive
        self.think = enable_thinking

    @trace_llm
    async def __call__(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
        tool_choice: Literal["auto", "none", "any", "required"]
        | str
        | None = None,
        **kwargs: Any,
    ) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        """Get the response from Ollama chat completions API by the given
        arguments.

        Args:
            messages (`list[dict]`):
                A list of dictionaries, where `role` and `content` fields are
                required, and `name` field is optional.
            tools (`list[dict]`, default `None`):
                The tools JSON schemas that the model can use.
            tool_choice (`Literal["auto", "none", "any", "required"] | str \
                | None`, default `None`):
                Controls which (if any) tool is called by the model.
                 Can be "auto", "none", "any", "required", or specific tool
                 name.
            **kwargs (`Any`):
                The keyword arguments for Ollama chat completions API,
                e.g. `think`etc. Please refer to the Ollama API
                documentation for more details.

        Returns:
            `ChatResponse | AsyncGenerator[ChatResponse, None]`:
                The response from the Ollama chat completions API.
        """

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "stream": self.stream,
            "options": self.options,
            "keep_alive": self.keep_alive,
            **kwargs,
        }

        if self.think is not None and "think" not in kwargs:
            kwargs["think"] = self.think

        if tools:
            kwargs["tools"] = self._format_tools_json_schemas(tools)

        if tool_choice:
            logger.warning("Ollama does not support tool_choice yet, ignored.")

        start_datetime = datetime.now()
        response = await self.client.chat(**kwargs)

        if self.stream:
            return self._parse_ollama_stream_completion_response(
                start_datetime,
                response,
            )

        parsed_response = await self._parse_ollama_completion_response(
            start_datetime,
            response,
        )

        return parsed_response

    async def _parse_ollama_stream_completion_response(
        self,
        start_datetime: datetime,
        response: AsyncIterator[Any],
    ) -> AsyncGenerator[ChatResponse, None]:
        """Parse the Ollama chat completion response stream into an async
        generator of `ChatResponse` objects."""
        accumulated_text = ""
        acc_thinking_content = ""
        tool_calls = OrderedDict()  # Store tool calls

        async for chunk in response:
            has_new_content = False
            has_new_thinking = False

            # Handle text content
            if hasattr(chunk, "message"):
                msg = chunk.message

                if getattr(msg, "thinking", None):
                    acc_thinking_content += msg.thinking
                    has_new_thinking = True

                if getattr(msg, "content", None):
                    accumulated_text += msg.content
                    has_new_content = True

                # Handle tool calls
                if getattr(msg, "tool_calls", None):
                    has_new_content = True
                    for idx, tool_call in enumerate(msg.tool_calls):
                        function_name = (
                            getattr(
                                tool_call,
                                "function",
                                None,
                            )
                            and tool_call.function.name
                            or "tool"
                        )
                        tool_id = getattr(
                            tool_call,
                            "id",
                            f"{function_name}_{idx}",
                        )
                        if hasattr(tool_call, "function"):
                            function = tool_call.function
                            tool_calls[tool_id] = {
                                "type": "tool_use",
                                "id": tool_id,
                                "name": function.name,
                                "input": function.arguments,
                            }
            # Calculate usage statistics
            current_time = (datetime.now() - start_datetime).total_seconds()
            usage = ChatUsage(
                input_tokens=getattr(chunk, "prompt_eval_count", 0) or 0,
                output_tokens=getattr(chunk, "eval_count", 0) or 0,
                time=current_time,
            )
            # Create content blocks
            contents: list = []

            if acc_thinking_content:
                contents.append(
                    ThinkingBlock(
                        type="thinking",
                        thinking=acc_thinking_content,
                    ),
                )

            if accumulated_text:
                contents.append(TextBlock(type="text", text=accumulated_text))

            # Add tool call blocks
            if tool_calls:
                for tool_call in tool_calls.values():
                    try:
                        input_data = tool_call["input"]
                        if isinstance(input_data, str):
                            input_data = _json_loads_with_repair(input_data)
                        contents.append(
                            ToolUseBlock(
                                type=tool_call["type"],
                                id=tool_call["id"],
                                name=tool_call["name"],
                                input=input_data,
                            ),
                        )
                    except Exception as e:
                        print(f"Error parsing tool call input: {e}")

            # Generate response when there's new content or at final chunk
            is_final = getattr(chunk, "done", False)
            if (has_new_thinking or has_new_content or is_final) and contents:
                res = ChatResponse(content=contents, usage=usage)
                yield res

    async def _parse_ollama_completion_response(
        self,
        start_datetime: datetime,
        response: OllamaChatResponse,
    ) -> ChatResponse:
        """Parse the Ollama chat completion response into a `ChatResponse`
        object.

        Args:
            start_datetime (`datetime`):
                The start datetime of the response generation.
            response (`OllamaChatResponse`):
                The Ollama chat response object to parse.

        Returns:
            `ChatResponse`:
                The content blocks and usage information extracted from the
                response.
        """
        content_blocks: List[TextBlock | ToolUseBlock | ThinkingBlock] = []

        if response.message.thinking:
            content_blocks.append(
                ThinkingBlock(
                    type="thinking",
                    thinking=response.message.thinking,
                ),
            )

        if response.message.content:
            content_blocks.append(
                TextBlock(
                    type="text",
                    text=response.message.content,
                ),
            )

        if response.message.tool_calls:
            for tool_call in response.message.tool_calls:
                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=tool_call.function.name,
                        name=tool_call.function.name,
                        input=tool_call.function.arguments,
                    ),
                )

        usage = None
        if "prompt_eval_count" in response and "eval_count" in response:
            usage = ChatUsage(
                input_tokens=response.get("prompt_eval_count", 0),
                output_tokens=response.get("eval_count", 0),
                time=(datetime.now() - start_datetime).total_seconds(),
            )

        parsed_response = ChatResponse(
            content=content_blocks,
            usage=usage,
        )

        return parsed_response

    def _format_tools_json_schemas(
        self,
        schemas: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Format the tools JSON schemas to the Ollama format."""
        return schemas
