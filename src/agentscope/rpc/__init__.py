# -*- coding: utf-8 -*-
"""Import all rpc related modules in the package."""
from .rpc_agent_client import (
    RpcAgentClient,
    ResponseStub,
    call_func_in_thread,
)

from .rpc_config import DistConf, async_func

try:
    from .rpc_agent_pb2 import CallFuncRequest  # pylint: disable=E0611
    from .rpc_agent_pb2_grpc import RpcAgentServicer
    from .rpc_agent_pb2_grpc import RpcAgentStub
    from .rpc_agent_pb2_grpc import add_RpcAgentServicer_to_server
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    CallFuncRequest = ImportErrorReporter(import_error, "distribute")  # type: ignore[misc]
    RpcAgentServicer = ImportErrorReporter(import_error, "distribute")
    RpcAgentStub = ImportErrorReporter(import_error, "distribute")
    add_RpcAgentServicer_to_server = ImportErrorReporter(
        import_error,
        "distribute",
    )


__all__ = [
    "RpcAgentClient",
    "ResponseStub",
    "CallFuncRequest",
    "RpcAgentServicer",
    "RpcAgentStub",
    "DistConf",
    "async_func",
    "call_func_in_thread",
    "add_RpcAgentServicer_to_server",
]
