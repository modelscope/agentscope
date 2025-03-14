# -*- coding: utf-8 -*-
"""The formatter for OpenAI models."""
from typing import Union

from loguru import logger

from agentscope.formatters import FormatterBase
from agentscope.message import Msg
from agentscope.utils.common import _to_openai_image_url


class OpenAIFormatter(FormatterBase):
    """The formatter for OpenAI models."""

    supported_model_regexes: list[str] = [
        "gpt-.*",
        "o1",
        "o1-mini",
        "o3-mini",
    ]

    @classmethod
    def format_chat(
        cls,
        *msgs: Union[Msg, list[Msg]],
    ) -> list[dict]:
        """Format the messages in chat scenario, where only one user and one
        assistant are involved.

        For OpenAI models, the `name` field can be used to distinguish
        different agents (even with the same role as `"assistant"`). So we
        simply reuse the `format_multi_agent` here.
        """
        return cls.format_multi_agent(*msgs)

    @classmethod
    def format_multi_agent(
        cls,
        *msgs: Union[Msg, list[Msg]],
    ) -> list[dict]:
        """Format the messages in multi-agent scenario, where multiple agents
        are involved.

        For OpenAI models, the `name` field can be used to distinguish
        different agents (even with the same role as `"assistant"`).
        """

        msgs = cls.check_and_flat_messages(*msgs)

        messages = []
        for msg in msgs:
            if msg is None:
                continue

            if isinstance(msg, Msg):
                content_blocks = []
                for block in msg.content:
                    typ = block.get("type")
                    if typ == "text":
                        content_blocks.append({**block})

                    elif typ == "tool_use":
                        content_blocks.append(
                            {
                                "id": block.get("id"),
                                "type": "function",
                                "function": {
                                    "name": block.get("name"),
                                    "arguments": block.get("input"),
                                },
                            },
                        )

                    elif typ == "tool_result":
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": block.get("id"),
                                "content": block.get("output"),
                            },
                        )

                    elif typ == "image":
                        content_blocks.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": _to_openai_image_url(
                                        str(block.get("url")),
                                    ),
                                },
                            },
                        )

                    else:
                        logger.warning(
                            f"Unsupported block type {typ} in the message, "
                            f"skipped.",
                        )

                    messages.append(
                        {
                            "role": msg.role,
                            "name": msg.name,
                            "content": content_blocks,
                        },
                    )

            elif isinstance(msg, list):
                messages.extend(
                    cls.format_multi_agent(
                        *msg,
                    ),
                )
            else:
                raise TypeError(
                    f"The input should be a Msg object or a list "
                    f"of Msg objects, got {type(msg)}.",
                )

        return messages
