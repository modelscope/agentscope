# -*- coding: utf-8 -*-
""" Enum for service execution status."""
from enum import IntEnum


class ServiceExecStatus(IntEnum):
    """Enum for service execution status."""

    SUCCESS = 1
    ERROR = -1
