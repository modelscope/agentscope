# -*- coding: utf-8 -*-
"""Import all rpc related modules in the package."""
from typing import Any
from .rpc_agent_client import RpcAgentClient

try:
    from .rpc_agent_pb2 import RpcMsg  # pylint: disable=E0611
except ModuleNotFoundError:
    RpcMsg = Any
try:
    from .rpc_agent_pb2_grpc import RpcAgentServicer
    from .rpc_agent_pb2_grpc import RpcAgentStub
    from .rpc_agent_pb2_grpc import add_RpcAgentServicer_to_server
except ImportError:
    RpcAgentServicer = object
    RpcAgentStub = Any
    add_RpcAgentServicer_to_server = Any


__all__ = [
    "RpcAgentClient",
    "RpcMsg",
    "RpcAgentServicer",
    "RpcAgentStub",
    "add_RpcAgentServicer_to_server",
]
