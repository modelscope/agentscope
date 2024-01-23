# -*- coding: utf-8 -*-
"""Logging utilities."""
import os
import sys
from typing import Optional, Literal, Union, Any

from loguru import logger

from agentscope.constants import MSG_TOKEN

LOG_LEVEL = Literal[
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


class _Stream:
    """Redirect stderr to logging"""

    def write(self, message: str) -> None:
        """Redirect to logging.

        Args:
            message (`str`):
                The message to be logged.
        """
        logger.error(message, enqueue=True)

    def flush(self) -> None:
        """Flush the stream."""


_SPEAKER_COLORS = [
    ("<blue>", "</blue>"),
    ("<cyan>", "</cyan>"),
    ("<green>", "</green>"),
    ("<magenta>", "</magenta>"),
    ("<red>", "</red>"),
    ("<white>", "</white>"),
    ("<yellow>", "</yellow>"),
]

_SPEAKER_TO_COLORS = {}


def _get_speaker_color(speaker: str) -> tuple[str, str]:
    """Get the color markers for a speaker. If the speaker is new, assign a
    new color. Otherwise, return the color that was assigned to the speaker.

    Args:
        speaker (`str`):
            The speaker to be assigned a color.

    Returns:
        `tuple[str, str]`: A color marker tuple, e.g. ("<blue>", "</blue>").
    """
    global _SPEAKER_COLORS, _SPEAKER_TO_COLORS
    if speaker in _SPEAKER_TO_COLORS:
        return _SPEAKER_TO_COLORS[speaker]
    else:
        markers = _SPEAKER_COLORS[
            (len(_SPEAKER_TO_COLORS) + 1)
            % len(
                _SPEAKER_COLORS,
            )
        ]
        # Record the color for this speaker
        _SPEAKER_TO_COLORS[speaker] = markers
        return markers


# add chat function for logger
def _chat(message: Union[str, dict], *args: Any, **kwargs: Any) -> None:
    """Log a chat message with the format of"<speaker>: <content>".

    Args:
        message (`Union[str, dict]`):
            The message to be logged. If it is a string, it will be logged
            directly. If it's a dict, it should have "name"(or "role") and
            "content" keys, and the message will be logged as "<name/role>:
            <content>".
    """
    if isinstance(message, dict):
        contain_name_or_role = "name" in message or "role" in message
        contain_content = "content" in message
        contain_url = "url" in message

        # print content if contain name or role and contain content
        if contain_name_or_role and contain_content:
            speaker = message.get("name", None) or message.get("role", None)
            content = message["content"]
            (m1, m2) = _get_speaker_color(speaker)
            logger.log(
                "CHAT",
                f"{m1}<b>{speaker}</b>{m2}: {content}".replace(
                    "{",
                    "{{",
                ).replace("}", "}}"),
                *args,
                **kwargs,
            )

            if contain_url:
                # print url if contain name or role and contain url
                url = message["url"]
                (m1, m2) = _get_speaker_color(speaker)
                # print url one by one if url is a list
                if isinstance(url, list):
                    for each_url in url:
                        logger.log(
                            "CHAT",
                            f"{m1}<b>{speaker}</b>{m2}: {each_url}",
                            *args,
                            **kwargs,
                        )
                else:
                    logger.log(
                        "CHAT",
                        f"{m1}<b>{speaker}</b>{m2}: {url}",
                        *args,
                        **kwargs,
                    )

        # print raw message if not contain name
        if not contain_name_or_role or not contain_content:
            logger.log("CHAT", str(message), *args, **kwargs)
    else:
        # print other types of message directly
        logger.log("CHAT", message, *args, **kwargs)


def _level_format(record: dict) -> str:
    """Format the log record."""
    if record["level"].name == "CHAT":
        return record["message"] + "\n"
    else:
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{"
            "level: <8}</level> | <cyan>{name}</cyan>:<cyan>{"
            "function}</cyan>:<cyan>{line}</cyan> - <level>{"
            "message}</level>\n"
        )


def _level_format_with_special_tokens(record: dict) -> str:
    """Format the log record."""
    if record["level"].name == "CHAT":
        return MSG_TOKEN + record["message"] + MSG_TOKEN + "\n"
    else:
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{"
            "level: <8}</level> | <cyan>{name}</cyan>:<cyan>{"
            "function}</cyan>:<cyan>{line}</cyan> - <level>{"
            "message}</level>\n"
        )


def setup_logger(
    path_log: Optional[str] = None,
    level: LOG_LEVEL = "INFO",
) -> None:
    r"""Setup `loguru.logger` and redirect stderr to logging.

    Args:
        path_log (`str`, defaults to `""`):
            The directory of log files.
        level (`str`, defaults to `"INFO"`):
            The logging level, which is one of the following: `"TRACE"`,
            `"DEBUG"`, `"INFO"`, `"SUCCESS"`, `"WARNING"`, `"ERROR"`,
            `"CRITICAL"`.
    """
    # avoid reinit in subprocess
    if hasattr(logger, "chat"):
        return

    # redirect stderr to record errors in logging
    sys.stderr = _Stream()

    # add chat function for logger
    logger.level("CHAT", no=21, color="<yellow>")
    logger.chat = _chat

    # set logging level
    logger.remove()
    # standard output for all logging except chat
    logger.add(sys.stdout, format=_level_format, enqueue=True, level=level)

    if path_log is not None:
        if not os.path.exists(path_log):
            os.makedirs(path_log)
        path_log_file = os.path.join(path_log, "all.log")
        path_log_file_only_chat = os.path.join(
            path_log,
            "chat.log",
        )

        # save all logging into file
        logger.add(
            path_log_file,
            format=_level_format_with_special_tokens,
            enqueue=True,
            level=level,
        )
        logger.add(
            path_log_file_only_chat,
            format=_level_format,
            enqueue=True,
            level="CHAT",
        )
