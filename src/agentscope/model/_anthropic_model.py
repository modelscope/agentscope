# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches, too-many-statements
"""The Anthropic API model classes."""

from datetime import datetime
from typing import (
    Any,
    AsyncGenerator,
    TYPE_CHECKING,
    List,
    Literal,
)
from collections import OrderedDict

from ._model_base import ChatModelBase
from ._model_response import ChatResponse
from ._model_usage import ChatUsage
from .._utils._common import _json_loads_with_repair
from ..message import TextBlock, ToolUseBlock, ThinkingBlock
from ..tracing import trace_llm
from ..types._json import JSONSerializableObject

if TYPE_CHECKING:
    from anthropic.types.message import Message
    from anthropic import AsyncStream
else:
    Message = "anthropic.types.message.Message"
    AsyncStream = "anthropic.AsyncStream"


class AnthropicChatModel(ChatModelBase):
    """The Anthropic model wrapper for AgentScope."""

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        max_tokens: int = 2048,
        stream: bool = True,
        thinking: dict | None = None,
        enable_prompt_cache: bool = False,
        client_args: dict | None = None,
        generate_kwargs: dict[str, JSONSerializableObject] | None = None,
    ) -> None:
        """Initialize the Anthropic chat model.

        Args:
            model_name (`str`):
                The model names.
            api_key (`str`):
                The anthropic API key.
            stream (`bool`):
                The streaming output or not
            max_tokens (`int`):
                Limit the maximum token count the model can generate.
            thinking (`dict | None`, default `None`):
                Configuration for Claude's internal reasoning process.

                .. code-block:: python
                    :caption: Example of thinking

                    {
                        "type": "enabled" | "disabled",
                        "budget_tokens": 1024
                    }

            enable_prompt_cache (`bool`, default `False`):
                Whether to cache prompt or not. For more details, please refer
                to the `official document
                <https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching>`_

                .. note:: Prompt caching currently only supports caching
                    system prompts.

                    **Important considerations:**

                    - **Additional Cost**: Enabling this feature incurs
                      extra charges from the model provider
                    - **Best Use Cases**: Recommended when using very long
                      system prompts (typically >1024 tokens)
                    - **Cost Savings**: Can significantly reduce token costs
                      when cache hit rates are high due to repeated prompt
                      usage
                    - **Trade-off**: Balance between cache storage costs and
                      token savings based on your usage pattern

            client_args (`dict | None`, optional):
                The extra keyword arguments to initialize the Anthropic client.
            generate_kwargs (`dict[str, JSONSerializableObject] | None`, \
             optional):
                The extra keyword arguments used in Gemini API generation,
                e.g. `temperature`, `seed`.
        """

        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "Please install the `anthropic` package by running "
                "`pip install anthropic`.",
            ) from e

        super().__init__(model_name, stream)

        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            **(client_args or {}),
        )
        self.max_tokens = max_tokens
        self.thinking = thinking
        self.enable_prompt_cache = enable_prompt_cache
        self.generate_kwargs = generate_kwargs or {}

    @trace_llm
    async def __call__(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
        tool_choice: Literal["auto", "none", "any", "required"]
        | str
        | None = None,
        **generate_kwargs: Any,
    ) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        """Get the response from Anthropic chat completions API by the given
        arguments.

        Args:
            messages (`list[dict]`):
                A list of dictionaries, where `role` and `content` fields are
                required, and `name` field is optional.
            tools (`list[dict]`, default `None`):
                The tools JSON schemas that in format of:

                .. code-block:: python
                    :caption: Example of tools JSON schemas

                    [
                        {
                            "type": "function",
                            "function": {
                                "name": "xxx",
                                "description": "xxx",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "param1": {
                                            "type": "string",
                                            "description": "..."
                                        },
                                        # Add more parameters as needed
                                    },
                                    "required": ["param1"]
                            }
                        },
                        # More schemas here
                    ]
            tool_choice (`Literal["auto", "none", "any", "required"] | str \
            | None`, default `None`):
                Controls which (if any) tool is called by the model.
                 Can be "auto", "none", "any", "required", or specific tool
                 name. For more details, please refer to the `official document
                 <https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use>`_
            **generate_kwargs (`Any`):
                The keyword arguments for Anthropic chat completions API,
                e.g. `temperature`, `top_p`, etc. Please
                refer to the Anthropic API documentation for more details.

        Returns:
            `ChatResponse | AsyncGenerator[ChatResponse, None]`:
                The response from the Anthropic chat completions API."""

        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
            **self.generate_kwargs,
            **generate_kwargs,
        }
        if self.thinking and "thinking" not in kwargs:
            kwargs["thinking"] = self.thinking

        if tools:
            kwargs["tools"] = self._format_tools_json_schemas(tools)

        if tool_choice:
            self._validate_tool_choice(tool_choice, tools)
            kwargs["tool_choice"] = self._format_tool_choice(tool_choice)

        # Extract the system message
        if messages[0]["role"] == "system":
            kwargs["system"] = messages[0]["content"]
            # FIXME: Only support cache system prompt now
            if self.enable_prompt_cache:
                for block in kwargs["system"]:
                    block["cache_control"] = {"type": "ephemeral"}
            messages = messages[1:]

        kwargs["messages"] = messages

        start_datetime = datetime.now()

        response = await self.client.messages.create(**kwargs)

        if self.stream:
            return self._parse_anthropic_stream_completion_response(
                start_datetime,
                response,
            )

        # Non-streaming response
        parsed_response = await self._parse_anthropic_completion_response(
            start_datetime,
            response,
        )

        return parsed_response

    async def _parse_anthropic_completion_response(
        self,
        start_datetime: datetime,
        response: Message,
    ) -> ChatResponse:
        """Parse the Anthropic chat completion response into a `ChatResponse`
        object."""
        content_blocks: List[ThinkingBlock | TextBlock | ToolUseBlock] = []

        if hasattr(response, "content") and response.content:
            for content_block in response.content:
                if (
                    hasattr(content_block, "type")
                    and content_block.type == "thinking"
                ):
                    thinking_block = ThinkingBlock(
                        type="thinking",
                        thinking=content_block.thinking,
                    )
                    thinking_block["signature"] = content_block.signature
                    content_blocks.append(thinking_block)

                elif hasattr(content_block, "text"):
                    content_blocks.append(
                        TextBlock(
                            type="text",
                            text=content_block.text,
                        ),
                    )

                elif (
                    hasattr(content_block, "type")
                    and content_block.type == "tool_use"
                ):
                    content_blocks.append(
                        ToolUseBlock(
                            type="tool_use",
                            id=content_block.id,
                            name=content_block.name,
                            input=content_block.input,
                        ),
                    )

        usage = None
        if response.usage:
            usage = ChatUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                time=(datetime.now() - start_datetime).total_seconds(),
            )

        parsed_response = ChatResponse(
            content=content_blocks,
            usage=usage,
        )

        return parsed_response

    async def _parse_anthropic_stream_completion_response(
        self,
        start_datetime: datetime,
        response: AsyncStream,
    ) -> AsyncGenerator[ChatResponse, None]:
        """Parse the Anthropic chat completion response stream into an async
        generator of `ChatResponse` objects."""

        usage = None
        text_buffer = ""
        thinking_buffer = ""
        thinking_signature = ""
        tool_calls = OrderedDict()
        tool_call_buffers = {}
        res = None

        async for event in response:
            content_changed = False
            thinking_changed = False

            if event.type == "message_start":
                message = event.message
                if message.usage:
                    usage = ChatUsage(
                        input_tokens=message.usage.input_tokens,
                        output_tokens=getattr(
                            message.usage,
                            "output_tokens",
                            0,
                        ),
                        time=(datetime.now() - start_datetime).total_seconds(),
                    )

            elif event.type == "content_block_start":
                if event.content_block.type == "tool_use":
                    block_index = event.index
                    tool_block = event.content_block
                    tool_calls[block_index] = {
                        "type": "tool_use",
                        "id": tool_block.id,
                        "name": tool_block.name,
                        "input": "",
                    }
                    tool_call_buffers[block_index] = ""
                    content_changed = True

            elif event.type == "content_block_delta":
                block_index = event.index
                delta = event.delta
                if delta.type == "text_delta":
                    text_buffer += delta.text
                    content_changed = True
                elif delta.type == "thinking_delta":
                    thinking_buffer += delta.thinking
                    thinking_changed = True
                elif delta.type == "signature_delta":
                    thinking_signature = delta.signature
                elif (
                    delta.type == "input_json_delta"
                    and block_index in tool_calls
                ):
                    tool_call_buffers[block_index] += delta.partial_json or ""
                    tool_calls[block_index]["input"] = tool_call_buffers[
                        block_index
                    ]
                    content_changed = True

            elif event.type == "message_delta":
                if event.usage and usage:
                    usage.output_tokens = event.usage.output_tokens

            if (thinking_changed or content_changed) and usage:
                contents: list = []
                if thinking_buffer:
                    thinking_block = ThinkingBlock(
                        type="thinking",
                        thinking=thinking_buffer,
                    )
                    thinking_block["signature"] = thinking_signature
                    contents.append(thinking_block)
                if text_buffer:
                    contents.append(
                        TextBlock(
                            type="text",
                            text=text_buffer,
                        ),
                    )
                for block_index, tool_call in tool_calls.items():
                    input_str = tool_call["input"]
                    try:
                        input_obj = _json_loads_with_repair(input_str or "{}")
                        if not isinstance(input_obj, dict):
                            input_obj = {}

                    except Exception:
                        input_obj = {}

                    contents.append(
                        ToolUseBlock(
                            type=tool_call["type"],
                            id=tool_call["id"],
                            name=tool_call["name"],
                            input=input_obj,
                        ),
                    )
                if contents:
                    res = ChatResponse(
                        content=contents,
                        usage=usage,
                    )
                    yield res

    def _format_tools_json_schemas(
        self,
        schemas: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Format the JSON schemas of the tool functions to the format that
        Anthropic API expects."""
        formatted_schemas = []
        for schema in schemas:
            assert (
                "function" in schema
            ), f"Invalid schema: {schema}, expect key 'function'."

            assert "name" in schema["function"], (
                f"Invalid schema: {schema}, "
                "expect key 'name' in 'function' field."
            )

            formatted_schemas.append(
                {
                    "name": schema["function"]["name"],
                    "description": schema["function"].get("description", ""),
                    "input_schema": schema["function"].get("parameters", {}),
                },
            )

        return formatted_schemas

    def _format_tool_choice(
        self,
        tool_choice: Literal["auto", "none", "any", "required"] | str | None,
    ) -> dict | None:
        """Format tool_choice parameter for API compatibility.

        Args:
            tool_choice (`Literal["auto", "none", "any", "required"] | str \
                | None`, default `None`):
                Controls which (if any) tool is called by the model.
                 Can be "auto", "none", "any", "required", or specific tool
                 name. For more details, please refer to
                 https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use
        Returns:
            `dict | None`:
                The formatted tool choice configuration dict, or None if
                tool_choice is None.
        """
        if tool_choice is None:
            return None

        type_mapping = {
            "auto": {"type": "auto"},
            "none": {"type": "none"},
            "any": {"type": "any"},
            "required": {"type": "any"},
        }
        if tool_choice in type_mapping:
            return type_mapping[tool_choice]

        return {"type": "tool", "name": tool_choice}
