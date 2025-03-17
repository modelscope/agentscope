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
    def format_chat(cls, *msgs: Union[Msg, list[Msg]]) -> list[dict]:
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
            content = []
            for block in msg.content:
                typ = block.get("type")
                if typ in ["text", "image", "audio"]:
                    content.append(
                        {
                            typ: block.get("text", block.get("url")),
                        },
                    )
                elif typ == "tool_use":
                    formatted_msgs.append(
                        {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
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
                            ],
                        },
                    )
                elif typ == "tool_result":
                    formatted_msgs.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.get("id"),
                            "content": block.get("output"),
                            "name": block.get("name"),
                        },
                    )
                # TODO: tool use
            formatted_msgs.append(
                {
                    "role": msg.role,
                    "content": content,
                },
            )
        return formatted_msgs

    @classmethod
    def format_multi_agent(
        cls,
        *msgs: Union[Msg, list[Msg]],
    ) -> list[dict]:
        """Format the messages in multi-agent scenario, where multiple agents
        are involved."""

        input_msgs = cls.check_and_flat_messages(*msgs)

        messages = []

        # record dialog history as a list of strings
        dialogue = []
        image_or_audio_dicts = []
        for i, unit in enumerate(input_msgs):
            if i == 0 and unit.role == "system":
                # system prompt
                content = cls._convert_url(unit.url)
                content.append({"text": unit.content})

                messages.append(
                    {
                        "role": unit.role,
                        "content": content,
                    },
                )
            else:
                # text message
                dialogue.append(
                    f"{unit.name}: {unit.content}",
                )
                # image and audio
                image_or_audio_dicts.extend(cls._convert_url(unit.url))

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
    def format_tools_json_schemas(cls, schemas: list[dict]) -> list[dict]:
        """Format the JSON schemas of the tool functions to the format that
        DashScope API expects. This function will take the parsed JSON schema
        from `agentscope.service.ServiceToolkit` as input and return
        the formatted JSON schema.

        Note:
            An example of the input/output tool JSON schema

            ..code-block:: json

                [
                    {
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
                ]

        Args:
            schemas (`list[dict]`):
                The JSON schema of the tool functions.

        Returns:
            `list[dict]`:
                The formatted JSON schema.
        """

        # The schemas from ServiceToolkit is exactly the same with the format
        # that DashScope API expects, so we just return the input schemas.

        assert isinstance(
            schemas,
            list,
        ), f"Expect list of schemas, got {type(schemas)}."

        for schema in schemas:
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

        return schemas
