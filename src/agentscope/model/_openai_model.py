# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches
"""OpenAI Chat model class."""
from datetime import datetime
from typing import (
    Any,
    TYPE_CHECKING,
    List,
    AsyncGenerator,
    Literal,
    Type,
)
from collections import OrderedDict

from pydantic import BaseModel

from . import ChatResponse
from ._model_base import ChatModelBase
from ._model_usage import ChatUsage
from .._logging import logger
from .._utils._common import _json_loads_with_repair
from ..message import ToolUseBlock, TextBlock, ThinkingBlock
from ..tracing import trace_llm
from ..types import JSONSerializableObject

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion
    from openai import AsyncStream
else:
    ChatCompletion = "openai.types.chat.ChatCompletion"
    AsyncStream = "openai.types.chat.AsyncStream"


class OpenAIChatModel(ChatModelBase):
    """The OpenAI chat model class."""

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        stream: bool = True,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        organization: str = None,
        client_args: dict = None,
        generate_kwargs: dict[str, JSONSerializableObject] | None = None,
    ) -> None:
        """Initialize the openai client.

        Args:
            model_name (`str`, default `None`):
                The name of the model to use in OpenAI API.
            api_key (`str`, default `None`):
                The API key for OpenAI API. If not specified, it will
                be read from the environment variable `OPENAI_API_KEY`.
            stream (`bool`, default `True`):
                Whether to use streaming output or not.
            reasoning_effort (`Literal["low", "medium", "high"] | None`, \
            optional):
                Reasoning effort, supported for o3, o4, etc. Please refer to
                `OpenAI documentation
                <https://platform.openai.com/docs/guides/reasoning?api-mode=chat>`_
                for more details.
            organization (`str`, default `None`):
                The organization ID for OpenAI API. If not specified, it will
                be read from the environment variable `OPENAI_ORGANIZATION`.
            client_args (`dict`, default `None`):
                The extra keyword arguments to initialize the OpenAI client.
            generate_kwargs (`dict[str, JSONSerializableObject] | None`, \
             optional):
               The extra keyword arguments used in OpenAI API generation,
                e.g. `temperature`, `seed`.
        """

        super().__init__(model_name, stream)

        import openai

        self.client = openai.AsyncClient(
            api_key=api_key,
            organization=organization,
            **(client_args or {}),
        )

        self.reasoning_effort = reasoning_effort
        self.generate_kwargs = generate_kwargs or {}

    @trace_llm
    async def __call__(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: Literal["auto", "none", "any", "required"]
        | str
        | None = None,
        structured_model: Type[BaseModel] | None = None,
        **kwargs: Any,
    ) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        """Get the response from OpenAI chat completions API by the given
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
                 name. For more details, please refer to
                 https://platform.openai.com/docs/api-reference/responses/create#responses_create-tool_choice
            structured_model (`Type[BaseModel] | None`, default `None`):
                A Pydantic BaseModel class that defines the expected structure
                for the model's output. When provided, the model will be forced
                to return data that conforms to this schema by automatically
                converting the BaseModel to a tool function and setting
                `tool_choice` to enforce its usage. This enables structured
                output generation.

                .. note:: When `structured_model` is specified,
                    both `tools` and `tool_choice` parameters are ignored,
                    and the model will only perform structured output
                    generation without calling any other tools.

                For more details, please refer to the `official document
                <https://platform.openai.com/docs/guides/structured-outputs>`_

            **kwargs (`Any`):
                The keyword arguments for OpenAI chat completions API,
                e.g. `temperature`, `max_tokens`, `top_p`, etc. Please
                refer to the OpenAI API documentation for more details.

        Returns:
            `ChatResponse | AsyncGenerator[ChatResponse, None]`:
                The response from the OpenAI chat completions API.
        """

        # checking messages
        if not isinstance(messages, list):
            raise ValueError(
                "OpenAI `messages` field expected type `list`, "
                f"got `{type(messages)}` instead.",
            )
        if not all("role" in msg and "content" in msg for msg in messages):
            raise ValueError(
                "Each message in the 'messages' list must contain a 'role' "
                "and 'content' key for OpenAI API.",
            )

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "stream": self.stream,
            **self.generate_kwargs,
            **kwargs,
        }
        if self.reasoning_effort and "reasoning_effort" not in kwargs:
            kwargs["reasoning_effort"] = self.reasoning_effort

        if tools:
            kwargs["tools"] = self._format_tools_json_schemas(tools)

        if tool_choice:
            self._validate_tool_choice(tool_choice, tools)
            kwargs["tool_choice"] = self._format_tool_choice(tool_choice)

        if self.stream:
            kwargs["stream_options"] = {"include_usage": True}

        start_datetime = datetime.now()

        if structured_model:
            if tools or tool_choice:
                logger.warning(
                    "structured_model is provided. Both 'tools' and "
                    "'tool_choice' parameters will be overridden and "
                    "ignored. The model will only perform structured output "
                    "generation without calling any other tools.",
                )
            kwargs.pop("stream", None)
            kwargs.pop("tools", None)
            kwargs.pop("tool_choice", None)
            kwargs["response_format"] = structured_model
            if not self.stream:
                response = await self.client.chat.completions.parse(**kwargs)
            else:
                response = self.client.chat.completions.stream(**kwargs)
                return self._parse_openai_stream_response(
                    start_datetime,
                    response,
                    structured_model,
                )
        else:
            response = await self.client.chat.completions.create(**kwargs)

        if self.stream:
            return self._parse_openai_stream_response(
                start_datetime,
                response,
                structured_model,
            )

        # Non-streaming response
        parsed_response = self._parse_openai_completion_response(
            start_datetime,
            response,
            structured_model,
        )

        return parsed_response

    async def _parse_openai_stream_response(
        self,
        start_datetime: datetime,
        response: AsyncStream,
        structured_model: Type[BaseModel] | None = None,
    ) -> AsyncGenerator[ChatResponse, None]:
        """Given an OpenAI streaming completion response, extract the content
         blocks and usages from it and yield ChatResponse objects.

        Args:
            start_datetime (`datetime`):
                The start datetime of the response generation.
            response (`AsyncStream`):
                OpenAI AsyncStream object to parse.
            structured_model (`Type[BaseModel] | None`, default `None`):
                A Pydantic BaseModel class that defines the expected structure
                for the model's output.

        Returns:
            `AsyncGenerator[ChatResponse, None]`:
                An async generator that yields ChatResponse objects containing
                the content blocks and usage information for each chunk in
                the streaming response.

        .. note::
            If `structured_model` is not `None`, the expected structured output
            will be stored in the metadata of the `ChatResponse`.
        """
        usage, res = None, None
        text = ""
        thinking = ""
        tool_calls = OrderedDict()
        metadata = None

        async with response as stream:
            async for item in stream:
                if structured_model:
                    if item.type != "chunk":
                        continue
                    chunk = item.chunk
                else:
                    chunk = item
                if chunk.usage:
                    usage = ChatUsage(
                        input_tokens=chunk.usage.prompt_tokens,
                        output_tokens=chunk.usage.completion_tokens,
                        time=(datetime.now() - start_datetime).total_seconds(),
                    )

                if chunk.choices:
                    choice = chunk.choices[0]
                    if (
                        hasattr(choice.delta, "reasoning_content")
                        and choice.delta.reasoning_content is not None
                    ):
                        thinking += choice.delta.reasoning_content

                    if choice.delta.content:
                        text += choice.delta.content

                    if choice.delta.tool_calls:
                        for tool_call in choice.delta.tool_calls:
                            if tool_call.index in tool_calls:
                                if tool_call.function.arguments is not None:
                                    tool_calls[tool_call.index][
                                        "input"
                                    ] += tool_call.function.arguments

                            else:
                                tool_calls[tool_call.index] = {
                                    "type": "tool_use",
                                    "id": tool_call.id,
                                    "name": tool_call.function.name,
                                    "input": tool_call.function.arguments
                                    or "",
                                }

                    contents: List[
                        TextBlock | ToolUseBlock | ThinkingBlock
                    ] = []

                    if thinking:
                        contents.append(
                            ThinkingBlock(
                                type="thinking",
                                thinking=thinking,
                            ),
                        )

                    if text:
                        contents.append(
                            TextBlock(
                                type="text",
                                text=text,
                            ),
                        )

                        if structured_model:
                            metadata = _json_loads_with_repair(text)

                    if tool_calls:
                        for tool_call in tool_calls.values():
                            contents.append(
                                ToolUseBlock(
                                    type=tool_call["type"],
                                    id=tool_call["id"],
                                    name=tool_call["name"],
                                    input=_json_loads_with_repair(
                                        tool_call["input"] or "{}",
                                    ),
                                ),
                            )

                    if contents:
                        res = ChatResponse(
                            content=contents,
                            usage=usage,
                            metadata=metadata,
                        )
                        yield res

    def _parse_openai_completion_response(
        self,
        start_datetime: datetime,
        response: ChatCompletion,
        structured_model: Type[BaseModel] | None = None,
    ) -> ChatResponse:
        """Given an OpenAI chat completion response object, extract the content
            blocks and usages from it.

        Args:
            start_datetime (`datetime`):
                The start datetime of the response generation.
            response (`ChatCompletion`):
                OpenAI ChatCompletion object to parse.
            structured_model (`Type[BaseModel] | None`, default `None`):
                A Pydantic BaseModel class that defines the expected structure
                for the model's output.

        Returns:
            ChatResponse (`ChatResponse`):
                A ChatResponse object containing the content blocks and usage.

        .. note::
            If `structured_model` is not `None`, the expected structured output
            will be stored in the metadata of the `ChatResponse`.
        """
        content_blocks: List[TextBlock | ToolUseBlock | ThinkingBlock] = []
        metadata = None

        if response.choices:
            choice = response.choices[0]
            if (
                hasattr(choice.message, "reasoning_content")
                and choice.message.reasoning_content is not None
            ):
                content_blocks.append(
                    ThinkingBlock(
                        type="thinking",
                        thinking=response.choices[0].message.reasoning_content,
                    ),
                )

            if choice.message.content:
                content_blocks.append(
                    TextBlock(
                        type="text",
                        text=response.choices[0].message.content,
                    ),
                )

            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    content_blocks.append(
                        ToolUseBlock(
                            type="tool_use",
                            id=tool_call.id,
                            name=tool_call.function.name,
                            input=_json_loads_with_repair(
                                tool_call.function.arguments,
                            ),
                        ),
                    )
            if structured_model:
                metadata = choice.message.parsed.model_dump()

        usage = None
        if response.usage:
            usage = ChatUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                time=(datetime.now() - start_datetime).total_seconds(),
            )

        parsed_response = ChatResponse(
            content=content_blocks,
            usage=usage,
            metadata=metadata,
        )

        return parsed_response

    def _format_tools_json_schemas(
        self,
        schemas: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Format the tools JSON schemas to the OpenAI format."""
        return schemas

    def _format_tool_choice(
        self,
        tool_choice: Literal["auto", "none", "any", "required"] | str | None,
    ) -> str | dict | None:
        """Format tool_choice parameter for API compatibility.

        Args:
            tool_choice (`Literal["auto", "none", "any", "required"] | str \
            | None`, default `None`):
                Controls which (if any) tool is called by the model.
                 Can be "auto", "none", "any", "required", or specific tool
                 name. For more details, please refer to
                 https://platform.openai.com/docs/api-reference/responses/create#responses_create-tool_choice
        Returns:
            `dict | None`:
                The formatted tool choice configuration dict, or None if
                    tool_choice is None.
        """
        if tool_choice is None:
            return None
        mode_mapping = {
            "auto": "auto",
            "none": "none",
            "any": "required",
            "required": "required",
        }
        if tool_choice in mode_mapping:
            return mode_mapping[tool_choice]
        return {"type": "function", "function": {"name": tool_choice}}
