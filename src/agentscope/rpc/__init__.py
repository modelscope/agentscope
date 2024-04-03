# -*- coding: utf-8 -*-
"""Import all rpc related modules in the package."""
from typing import Any
from .rpc_agent_client import RpcAgentClient, ResponseStub, call_in_thread

try:
    from .rpc_agent_pb2 import RpcMsg  # pylint: disable=E0611
except ModuleNotFoundError:
    RpcMsg = Any  # type: ignore[misc]
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
    "ResponseStub",
    "call_in_thread",
    "RpcMsg",
    "RpcAgentServicer",
    "RpcAgentStub",
    "add_RpcAgentServicer_to_server",
]
