# -*- coding: utf-8 -*-
""" Import all pipeline related modules in the package. """
from .pipeline import (
    PipelineBase,
    SequentialPipeline,
    IfElsePipeline,
    SwitchPipeline,
    ForLoopPipeline,
    WhileLoopPipeline,
)

from .functional import (
    sequentialpipeline,
    ifelsepipeline,
    switchpipeline,
    forlooppipeline,
    whilelooppipeline,
)

__all__ = [
    "PipelineBase",
    "SequentialPipeline",
    "IfElsePipeline",
    "SwitchPipeline",
    "ForLoopPipeline",
    "WhileLoopPipeline",
    "sequentialpipeline",
    "ifelsepipeline",
    "switchpipeline",
    "forlooppipeline",
    "whilelooppipeline",
]
