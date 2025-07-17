# -*- coding: utf-8 -*-
"""Logging utilities."""
import json
import os
import sys
from typing import Optional, Literal

from loguru import logger


from .message import Msg
from .serialize import serialize
from .utils.common import (
    _map_string_to_color_mark,
)


LOG_LEVEL = Literal[
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
]

LEVEL_SAVE_LOG = "SAVE_LOG"
LEVEL_SAVE_MSG = "SAVE_MSG"

_DEFAULT_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{"
    "level: <8}</level> | <cyan>{name}</cyan>:<cyan>{"
    "function}</cyan>:<cyan>{line}</cyan> - <level>{"
    "message}</level>"
)

_PREFIX_DICT = {}


def _formatted_str(msg: Msg, colored: bool = False) -> str:
    """Return the formatted string of the message. If the message has an
    url, the url will be appended to the content.

    Args:
        msg (`Msg`):
            The message object to be formatted.
        colored (`bool`, defaults to `False`):
            Whether to color the name of the message

    Returns:
        `str`: The formatted string of the message.
    """
    if colored:
        m1, m2 = _map_string_to_color_mark(msg.name)
        name = f"{m1}{msg.name}{m2}"
    else:
        name = msg.name

    colored_strs = []

    for block in msg.get_content_blocks():
        if block["type"] == "text":
            colored_strs.append(f"{name}: {block.get('text')}")
        elif block["type"] in ["audio", "image", "video", "file"]:
            colored_strs.append(f"{name}: {block.get('url')}")
        elif block["type"] == "tool_result":
            colored_strs.append(
                f"{name}: Execute function {block['name']}:\n"
                f"{block['output']}",
            )

    # Tool use block
    tool_calls = msg.get_content_blocks("tool_use")
    if tool_calls:
        tool_calls_str = json.dumps(tool_calls, indent=4, ensure_ascii=False)
        if colored_strs:
            colored_strs.append(tool_calls_str)
        else:
            colored_strs.append(f"{name}: {tool_calls_str}")

    return "\n".join(colored_strs)


def log_stream_msg(msg: Msg, last: bool = True) -> None:
    """Print the message in different streams, including terminal, studio, and
    gradio if it is active.

    Args:
        msg (`Msg`):
            The message object to be printed.
        last (`bool`, defaults to `True`):
            True if this is the last message in the stream or a single message.
            Otherwise, False.
    """
    global _PREFIX_DICT

    # Print msg to terminal
    formatted_str = _formatted_str(msg, colored=True)

    print_str = formatted_str[_PREFIX_DICT.get(msg.id, 0) :]

    if last:
        # Remove the prefix from the dictionary
        if msg.id in _PREFIX_DICT:
            del _PREFIX_DICT[msg.id]

        print(print_str)
    else:
        # Update the prefix in the dictionary
        _PREFIX_DICT[msg.id] = len(formatted_str)

        print(print_str, end="")

    if last:
        # Save msg into chat file
        _save_msg(msg)


def _save_msg(msg: Msg) -> None:
    """Save the message into `logging.chat` and `logging.log` files.

    Args:
        msg (`Msg`):
            The message object to be saved.
    """
    # TODO: Unified into a manager rather than an indicated attribute here
    if hasattr(logger, "chat"):
        # Not initialize yet
        logger.log(
            LEVEL_SAVE_LOG,
            _formatted_str(msg, colored=False),
        )

        logger.log(
            LEVEL_SAVE_MSG,
            serialize(msg),
        )


def log_msg(msg: Msg) -> None:
    """Print the message and save it into files. Note the message should be a
    Msg object."""

    if not isinstance(msg, Msg):
        raise TypeError(f"Get type {type(msg)}, expect Msg object.")

    print(_formatted_str(msg, colored=True))

    # Save msg into chat file
    _save_msg(msg)


def _level_format(record: dict) -> str:
    """Format the log record."""
    # Display the chat message
    if record["level"].name == LEVEL_SAVE_LOG:
        return "{message}\n"
    else:
        return _DEFAULT_LOG_FORMAT + "\n"


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
    # set logging level
    logger.remove()

    # avoid reinit in subprocess
    if not hasattr(logger, "chat"):
        # add chat function for logger
        logger.level(LEVEL_SAVE_LOG, no=51)

        # save chat message into file
        logger.level(LEVEL_SAVE_MSG, no=53)
        logger.chat = log_msg

        # standard output for all logging except chat
        logger.add(
            sys.stdout,
            filter=lambda record: record["level"].name
            not in [LEVEL_SAVE_LOG, LEVEL_SAVE_MSG],
            format=_DEFAULT_LOG_FORMAT,
            enqueue=True,
            level=level,
        )

    if path_log is not None:
        os.makedirs(path_log, exist_ok=True)
        path_log_file = os.path.join(path_log, "logging.log")
        path_chat_file = os.path.join(
            path_log,
            "logging.chat",
        )

        # save all logging except LEVEL_SAVE_MSG into logging.log
        logger.add(
            path_log_file,
            filter=lambda record: record["level"].name != LEVEL_SAVE_MSG,
            format=_level_format,
            enqueue=True,
            level=level,
        )

        # save chat message into logging.chat
        logger.add(
            path_chat_file,
            format="{message}",
            enqueue=True,
            level=LEVEL_SAVE_MSG,  # The highest level to filter out all
            # other logs
        )
