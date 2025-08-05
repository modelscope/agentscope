# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors
"""The content blocks of messages"""
from typing import Literal, Union, Optional
from typing_extensions import TypedDict, Required


class ToolUseBlock(TypedDict, total=False):
    """The tool use block."""

    type: Required[Literal["tool_use"]]
    """The type of the block, must be `tool_use`"""
    id: Required[str]
    """The identity of the tool call"""
    name: Required[str]
    """The name of the tool"""
    input: Required[dict[str, object]]
    """The input of the tool"""


class ToolResultBlock(TypedDict, total=False):
    """The tool result block."""

    type: Required[Literal["tool_result"]]
    """The type of the block"""
    id: Required[str]
    """The identity of the tool call result"""
    output: Required[object]
    """The output of the tool function"""
    name: Optional[str]
    """The name of the tool function"""


class TextBlock(TypedDict, total=False):
    """The text block."""

    type: Required[Literal["text"]]
    """The type of the block"""
    text: str
    """The text content"""


class ImageBlock(TypedDict, total=False):
    """The image block"""

    type: Required[Literal["image"]]
    """The type of the block"""
    url: str
    """The url of the image"""


class AudioBlock(TypedDict, total=False):
    """The audio block"""

    type: Required[Literal["audio"]]
    """The type of the block"""
    url: str
    """The url of the audio"""


class VideoBlock(TypedDict, total=False):
    """The video block"""

    type: Required[Literal["video"]]
    """The type of the block"""
    url: str
    """The url of the video"""


class FileBlock(TypedDict, total=False):
    """The file block"""

    type: Required[Literal["file"]]
    """The type of the block"""
    url: str
    """The url of the file"""


ContentBlock = Union[
    ToolUseBlock,
    ToolResultBlock,
    TextBlock,
    ImageBlock,
    AudioBlock,
    VideoBlock,
    FileBlock,
]
