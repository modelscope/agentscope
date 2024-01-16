# -*- coding: utf-8 -*-
""" Import all agent related modules in the package. """
from typing import Callable
from .agent import AgentBase
from .rpc_agent import RpcAgentBase
from .dialog_agent import DialogAgent
from .dict_dialog_agent import DictDialogAgent
from .state_agent import StateAgent
from .user_agent import UserAgent

# todo: convert Operator to a common base class for AgentBase and PipelineBase
_Operator = Callable[..., dict]

__all__ = [
    "AgentBase",
    "_Operator",
    "RpcAgentBase",
    "DialogAgent",
    "DictDialogAgent",
    "StateAgent",
    "UserAgent",
]
