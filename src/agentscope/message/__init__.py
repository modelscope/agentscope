# -*- coding: utf-8 -*-
"""The message module of AgentScope."""

from .msg import Msg, MessageBase
from .placeholder import PlaceholderMessage, deserialize, serialize

__all__ = [
    "Msg",
    "MessageBase",
    "deserialize",
    "serialize",
]
