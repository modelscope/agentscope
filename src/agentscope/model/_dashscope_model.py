# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches
"""The dashscope API model classes."""
import collections
from datetime import datetime
from http import HTTPStatus
from typing import (
    Any,
    AsyncGenerator,
    Generator,
    Union,
    TYPE_CHECKING,
    List,
    Literal,
)
from aioitertools import iter as giter

from ._model_base import ChatModelBase
from ._model_response import ChatResponse
from ._model_usage import ChatUsage
from .._utils._common import _json_loads_with_repair
from ..message import TextBlock, ToolUseBlock, ThinkingBlock
from ..tracing import trace_llm
from ..types import JSONSerializableObject
from .._logging import logger

if TYPE_CHECKING:
    from dashscope.api_entities.dashscope_response import GenerationResponse
    from dashscope.api_entities.dashscope_response import (
        MultiModalConversationResponse,
    )
else:
    GenerationResponse = (
        "dashscope.api_entities.dashscope_response.GenerationResponse"
    )
    MultiModalConversationResponse = (
        "dashscope.api_entities.dashscope_response."
        "MultiModalConversationResponse"
    )


class DashScopeChatModel(ChatModelBase):
    """The DashScope chat model class, which unifies the Generation and
    MultimodalConversation APIs into one method."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        stream: bool = True,
        enable_thinking: bool | None = None,
        generate_kwargs: dict[str, JSONSerializableObject] | None = None,
        base_http_api_url: str | None = None,
    ) -> None:
        """Initialize the DashScope chat model.

        Args:
            model_name (`str`):
                The model names.
            api_key (`str`):
                The dashscope API key.
            stream (`bool`):
                The streaming output or not
            enable_thinking (`bool | None`, optional):
                Enable thinking or not, only support Qwen3, QwQ, DeepSeek-R1.
                Refer to `DashScope documentation
                <https://help.aliyun.com/zh/model-studio/deep-thinking>`_
                for more details.
            generate_kwargs (`dict[str, JSONSerializableObject] | None`, \
            optional):
               The extra keyword arguments used in DashScope API generation,
               e.g. `temperature`, `seed`.
            base_http_api_url (`str | None`, optional):
                The base URL for DashScope API requests. If not provided,
                the default base URL from the DashScope SDK will be used.
        """
        if enable_thinking and not stream:
            logger.info(
                "In DashScope API, `stream` must be True when "
                "`enable_thinking` is True. ",
            )
            stream = True

        super().__init__(model_name, stream)

        self.api_key = api_key
        self.enable_thinking = enable_thinking
        self.incremental_output = self.stream
        self.generate_kwargs = generate_kwargs or {}

        if base_http_api_url is not None:
            import dashscope

            dashscope.base_http_api_url = base_http_api_url

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
        """Get the response from the dashscope
        Generation/MultimodalConversation API by the given arguments.

        .. note:: We unify the dashscope generation and multimodal conversation
         APIs into one method, since they support similar arguments and share
         the same functionality.

        Args:
            messages (`list[dict[str, Any]]`):
                A list of dictionaries, where `role` and `content` fields are
                required.
            tools (`list[dict] | None`, default `None`):
                The tools JSON schemas that the model can use.
            tool_choice (`Literal["auto", "none", "any", "required"] | str \
             |  None`,  default `None`):
                Controls which (if any) tool is called by the model.
                 Can be "auto", "none", or specific tool name.
                 For more details, please refer to
                 https://help.aliyun.com/zh/model-studio/qwen-function-calling
            **kwargs (`Any`):
                The keyword arguments for DashScope chat completions API,
                e.g. `temperature`, `max_tokens`, `top_p`, etc. Please
                refer to `DashScope documentation
                <https://help.aliyun.com/zh/dashscope/developer-reference/api-details>`_
                for more detailed arguments.
        """
        import dashscope

        # For qvq and qwen-vl models, the content field cannot be `None` or
        # `[{"text": None}]`, so we need to convert it to an empty list.
        if self.model_name.startswith("qvq") or "-vl" in self.model_name:
            for msg in messages:
                if msg["content"] is None or msg["content"] == [
                    {"text": None},
                ]:
                    msg["content"] = []

        kwargs = {
            "messages": messages,
            "model": self.model_name,
            "stream": self.stream,
            **self.generate_kwargs,
            **kwargs,
            "result_format": "message",
            # In agentscope, the `incremental_output` must be `True`
            "incremental_output": self.incremental_output,
        }

        if tools:
            kwargs["tools"] = self._format_tools_json_schemas(tools)

        if tool_choice:
            self._validate_tool_choice(tool_choice, tools)
            kwargs["tool_choice"] = self._format_tool_choice(tool_choice)

        if self.enable_thinking and "enable_thinking" not in kwargs:
            kwargs["enable_thinking"] = self.enable_thinking

        start_datetime = datetime.now()
        if self.model_name.startswith("qvq") or "-vl" in self.model_name:
            response = dashscope.MultiModalConversation.call(
                api_key=self.api_key,
                **kwargs,
            )

        else:
            response = await dashscope.aigc.generation.AioGeneration.call(
                api_key=self.api_key,
                **kwargs,
            )

        if self.stream:
            return self._parse_dashscope_stream_response(
                start_datetime,
                response,
            )

        parsed_response = await self._parse_dashscope_generation_response(
            used_time=(datetime.now() - start_datetime).total_seconds(),
            response=response,
        )

        return parsed_response

    async def _parse_dashscope_stream_response(
        self,
        start_datetime: datetime,
        response: Union[
            AsyncGenerator[GenerationResponse, None],
            Generator[MultiModalConversationResponse, None, None],
        ],
    ) -> AsyncGenerator[ChatResponse, Any]:
        """Parse the DashScope GenerationResponse object and return a
        ChatResponse object."""
        acc_content, acc_thinking_content = "", ""
        acc_tool_calls = collections.defaultdict(dict)
        parsed_chunk = None

        async for chunk in giter(response):
            if chunk.status_code != HTTPStatus.OK:
                raise RuntimeError(
                    f"Failed to get response from _ API: {chunk}",
                )

            message = chunk.output.choices[0].message

            # Update reasoning content
            if isinstance(message.get("reasoning_content"), str):
                acc_thinking_content += message["reasoning_content"]

            # Update text content
            if isinstance(message.content, str):
                acc_content += message.content
            elif isinstance(message.content, list):
                for item in message.content:
                    if isinstance(item, dict) and "text" in item:
                        acc_content += item["text"]

            # Update tool calls
            for tool_call in message.get("tool_calls", []):
                index = tool_call.get("index", 0)

                if "id" in tool_call and tool_call["id"] != acc_tool_calls[
                    index
                ].get("id"):
                    acc_tool_calls[index]["id"] = (
                        acc_tool_calls[index].get("id", "") + tool_call["id"]
                    )

                if "function" in tool_call:
                    func = tool_call["function"]
                    if "name" in func:
                        acc_tool_calls[index]["name"] = (
                            acc_tool_calls[index].get("name", "")
                            + func["name"]
                        )

                    if "arguments" in func:
                        acc_tool_calls[index]["arguments"] = (
                            acc_tool_calls[index].get("arguments", "")
                            + func["arguments"]
                        )

            # to content blocks
            content_blocks: list[TextBlock | ToolUseBlock | ThinkingBlock] = []
            if acc_thinking_content:
                content_blocks.append(
                    ThinkingBlock(
                        type="thinking",
                        thinking=acc_thinking_content,
                    ),
                )

            if acc_content:
                content_blocks.append(
                    TextBlock(
                        type="text",
                        text=acc_content,
                    ),
                )

            for tool_call in acc_tool_calls.values():
                repaired_input = _json_loads_with_repair(
                    tool_call.get("arguments", "{}") or "{}",
                )

                if not isinstance(repaired_input, dict):
                    repaired_input = {}

                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=tool_call.get("id", ""),
                        name=tool_call.get("name", ""),
                        input=repaired_input,
                    ),
                )

            usage = None
            if chunk.usage:
                usage = ChatUsage(
                    input_tokens=chunk.usage.input_tokens,
                    output_tokens=chunk.usage.output_tokens,
                    time=(datetime.now() - start_datetime).total_seconds(),
                )

            parsed_chunk = ChatResponse(
                content=content_blocks,
                usage=usage,
            )
            yield parsed_chunk

    async def _parse_dashscope_generation_response(
        self,
        used_time: float,
        response: Union[
            GenerationResponse,
            MultiModalConversationResponse,
        ],
    ) -> ChatResponse:
        """Given a DashScope GenerationResponse object, extract the content
        blocks and usages from it.

        Args:
            used_time (`float`):
                The time used for the response in seconds.
            response (
                `Union[GenerationResponse, MultiModalConversationResponse]`
            ):
                Dashscope GenerationResponse | MultiModalConversationResponse
                object to parse.

        Returns:
            `ChatResponse`:
                A ChatResponse object containing the content blocks and usage.
        """
        # Collect the content blocks from the response.
        if response.status_code != 200:
            raise RuntimeError(response)

        content_blocks: List[TextBlock | ToolUseBlock] = []

        message = response.output.choices[0].message
        content = message.get("content")

        if response.output.choices[0].message.get("content") not in [
            None,
            "",
            [],
        ]:
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        content_blocks.append(
                            TextBlock(
                                type="text",
                                text=item["text"],
                            ),
                        )
            else:
                content_blocks.append(
                    TextBlock(
                        type="text",
                        text=content,
                    ),
                )

        if message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        name=tool_call["function"]["name"],
                        input=_json_loads_with_repair(
                            tool_call["function"].get(
                                "arguments",
                                "{}",
                            )
                            or "{}",
                        ),
                        id=tool_call["id"],
                    ),
                )

        # Usage information
        usage = None
        if response.usage:
            usage = ChatUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                time=used_time,
            )

        return ChatResponse(
            content=content_blocks,
            usage=usage,
        )

    def _format_tools_json_schemas(
        self,
        schemas: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Format the tools JSON schema into required format for DashScope API.

        Args:
            schemas (`dict[str, dict[str, Any]]`):
                The tools JSON schemas.
        """
        # Check schemas format
        for value in schemas:
            if (
                not isinstance(value, dict)
                or "type" not in value
                or value["type"] != "function"
                or "function" not in value
            ):
                raise ValueError(
                    f"Each schema must be a dict with 'type' as 'function' "
                    f"and 'function' key, got {value}",
                )

        return schemas

    def _format_tool_choice(
        self,
        tool_choice: Literal["auto", "none", "any", "required"] | str | None,
    ) -> str | dict | None:
        """Format tool_choice parameter for API compatibility.

        Args:
            tool_choice (`Literal["auto", "none",  "any", "required"] | str \
            | None`, default  `None`):
                Controls which (if any) tool is called by the model.
                 Can be "auto", "none", or specific tool name.
                 For more details, please refer to
                 https://help.aliyun.com/zh/model-studio/qwen-function-calling
        Returns:
            `dict | None`:
                The formatted tool choice configuration dict, or None if
                    tool_choice is None.
        """
        if tool_choice is None:
            return None
        if tool_choice in ["auto", "none"]:
            return tool_choice
        if tool_choice in ["any", "required"]:
            logger.warning(
                "tool_choice '%s' is not supported by DashScope API. "
                "Supported options are 'auto', 'none', or specific function "
                "name. Automatically using 'auto' instead.",
                tool_choice,
            )
            return "auto"
        return {"type": "function", "function": {"name": tool_choice}}
