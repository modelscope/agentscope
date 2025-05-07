# -*- coding: utf-8 -*-
"""The dashscope formatter class."""
import json
import os
from typing import Union

from loguru import logger

from ..formatters import FormatterBase
from ..message import Msg
from ..utils.common import _guess_type_by_extension


class DashScopeFormatter(FormatterBase):
    """The DashScope formatter, which is responsible for formatting messages,
    JSON schemas description of the tool functions."""

    supported_model_regexes: list[str] = [
        "qwen-.*",
    ]

    @staticmethod
    def _convert_url(url: str) -> list[dict]:
        """Convert the url to the format of DashScope API. Note for local
        files, a prefix "file://" will be added.

        Args:
            url (`Union[str, Sequence[str], None]`):
                A string of url of a list of urls to be converted.

        Returns:
            `List[dict]`:
                A list of dictionaries with key as the type of the url
                and value as the url. Only "image" and "audio" are supported.
        """
        if isinstance(url, str):
            url_type = _guess_type_by_extension(url)
            if url_type in ["audio", "image"]:
                # Add prefix for local files
                if os.path.exists(url):
                    url = "file://" + url
                return [{url_type: url}]
            else:
                # skip unsupported url
                logger.warning(
                    f"Skip unsupported url ({url_type}), "
                    f"expect image or audio.",
                )
                return []
        else:
            raise TypeError(
                f"Unsupported url type {type(url)}, " f"str or list expected.",
            )

    @classmethod
    def format_chat(cls, *msgs: Union[Msg, list[Msg], None]) -> list[dict]:
        """Format the messages in chat scenario, where only one user and
        one assistant are involved.

        The current format function supports:
            - [x] image
            - [x] audio
            - [x] text
            - [x] tool_use
        """

        input_msgs = cls.check_and_flat_messages(*msgs)

        formatted_msgs: list[dict] = []
        for msg in input_msgs:
            content_blocks = []
            tool_calls = []
            for block in msg.get_content_blocks():
                typ = block.get("type")
                if typ in ["text", "image", "audio"]:
                    content_blocks.append(
                        {
                            typ: block.get("text", block.get("url")),
                        },
                    )
                elif typ == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.get("id"),
                            "type": "function",
                            "function": {
                                "name": block.get("name"),
                                "arguments": json.dumps(
                                    block.get("input", {}),
                                    ensure_ascii=False,
                                ),
                            },
                        },
                    )

                elif typ == "tool_result":
                    formatted_msgs.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.get("id"),
                            "content": str(block.get("output")),
                            "name": block.get("name"),
                        },
                    )
                else:
                    logger.warning(
                        f"Unsupported block type {typ} in the message, "
                        f"skipped.",
                    )

            msg_dashscope = {
                "role": msg.role,
                "content": content_blocks or None,
            }

            if tool_calls:
                msg_dashscope["tool_calls"] = tool_calls

            if msg_dashscope["content"] or msg_dashscope.get("tool_calls"):
                formatted_msgs.append(msg_dashscope)

        return formatted_msgs

    @classmethod
    def format_multi_agent(
        cls,
        *msgs: Union[Msg, list[Msg], None],
    ) -> list[dict]:
        """Format the messages in multi-agent scenario, where multiple agents
        are involved."""

        input_msgs = cls.check_and_flat_messages(*msgs)

        messages = []

        # record dialog history as a list of strings
        dialogue = []
        image_or_audio_dicts = []
        for i, msg in enumerate(input_msgs):
            if i == 0 and msg.role == "system" and msg.get_text_content():
                # system prompt
                content = [{"text": msg.get_text_content()}]
                messages.append(
                    {
                        "role": msg.role,
                        "content": content,
                    },
                )
            else:
                # text message
                if msg.get_text_content():
                    dialogue.append(
                        f"{msg.name}: {msg.get_text_content()}",
                    )
                # image and audio
                for block in msg.get_content_blocks():
                    if block.get("type") in ["image", "audio"]:
                        image_or_audio_dicts.extend(
                            cls._convert_url(str(block.get("url"))),
                        )

        dialogue_history = "\n".join(dialogue)

        user_content_template = "## Conversation History\n{dialogue_history}"

        messages.append(
            {
                "role": "user",
                "content": [
                    # Place the image or audio before the conversation history
                    *image_or_audio_dicts,
                    {
                        "text": user_content_template.format(
                            dialogue_history=dialogue_history,
                        ),
                    },
                ],
            },
        )

        return messages

    @classmethod
    def format_tools_json_schemas(cls, schemas: dict[str, dict]) -> list[dict]:
        """Format the JSON schemas of the tool functions to the format that
        DashScope API expects. This function will take the parsed JSON schema
        from `agentscope.service.ServiceToolkit` as input and return
        the formatted JSON schema.

        Note:
            An example of the input/output tool JSON schema

            ..code-block:: json

                {
                    "bing_search": {
                        "type": "function",
                        "function": {
                            "name": "bing_search",
                            "description": "Search the web using Bing.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query.",
                                    }
                                },
                                "required": ["query"],
                            }
                        }
                    }
                }

        Args:
            schemas (`dict[str, dict]`):
                The JSON schema of the tool functions.

        Returns:
            `list[dict]`:
                The formatted JSON schema.
        """

        # The schemas from ServiceToolkit is exactly the same with the format
        # that DashScope API expects, so we just return the input schemas.

        assert isinstance(
            schemas,
            dict,
        ), f"Expect dict of schemas, got {type(schemas)}."

        for schema in schemas.values():
            assert isinstance(
                schema,
                dict,
            ), f"Expect dict schema, got {type(schema)}."

            assert (
                "type" in schema and "function" in schema
            ), f"Invalid schema: {schema}, expect keys 'type' and 'function'."

            assert (
                schema["type"] == "function"
            ), f"Invalid schema type: {schema['type']}, expect 'function'."

            assert "name" in schema["function"], (
                f"Invalid schema: {schema}, "
                f"expect key 'name' in 'function' field."
            )

        return list(schemas.values())
