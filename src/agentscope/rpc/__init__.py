# -*- coding: utf-8 -*-
"""Import all rpc related modules in the package."""
from .rpc_agent_client import (
    RpcAgentClient,
    call_func_in_thread,
)

from .rpc_config import DistConf
from .rpc_async import async_func, AsyncResult
from .rpc_object import RpcObject

try:
    from .rpc_agent_pb2 import CallFuncRequest  # pylint: disable=E0611
    from .rpc_agent_pb2_grpc import RpcAgentServicer
    from .rpc_agent_pb2_grpc import RpcAgentStub
except ImportError as import_error:
    from agentscope.utils.common import ImportErrorReporter

    CallFuncRequest = ImportErrorReporter(import_error, "distribute")  # type: ignore[misc]
    RpcAgentServicer = ImportErrorReporter(import_error, "distribute")
    RpcAgentStub = ImportErrorReporter(import_error, "distribute")


__all__ = [
    "RpcAgentClient",
    "CallFuncRequest",
    "RpcAgentServicer",
    "RpcAgentStub",
    "RpcObject",
    "DistConf",
    "async_func",
    "AsyncResult",
    "call_func_in_thread",
]
