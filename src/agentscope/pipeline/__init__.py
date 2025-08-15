# -*- coding: utf-8 -*-
"""The pipeline module in AgentScope, that provides syntactic sugar for
complex workflows and multi-agent conversations."""

from ._msghub import MsgHub
from ._class import SequentialPipeline
from ._functional import sequential_pipeline

__all__ = [
    "MsgHub",
    "SequentialPipeline",
    "sequential_pipeline",
]
