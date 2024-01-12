# -*- coding: utf-8 -*-
""" Enums for agentscope """

from enum import IntEnum


class ResponseFormat(IntEnum):
    """Enum for model response format."""

    NONE = 0
    JSON = 1


class ServiceExecStatus(IntEnum):
    """Enum for service execution status."""

    SUCCESS = 1
    ERROR = -1


class PromptType(IntEnum):
    """Enum for prompt types."""

    STRING = 0
    LIST = 1


class ShrinkPolicy(IntEnum):
    """Enum for shrink strategies when the prompt is too long."""

    TRUNCATE = 0
    SUMMARIZE = 1
