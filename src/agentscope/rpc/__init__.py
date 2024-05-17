# -*- coding: utf-8 -*-
"""Import all rpc related modules in the package."""
from .rpc_agent_client import RpcAgentClient, ResponseStub, call_in_thread

try:
    from .rpc_agent_pb2 import RpcMsg  # pylint: disable=E0611
    from .rpc_agent_pb2_grpc import RpcAgentServicer
    from .rpc_agent_pb2_grpc import RpcAgentStub
    from .rpc_agent_pb2_grpc import add_RpcAgentServicer_to_server
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    RpcMsg = ImportErrorReporter(import_error, "distribute")  # type: ignore[misc]
    RpcAgentServicer = ImportErrorReporter(import_error, "distribute")
    RpcAgentStub = ImportErrorReporter(import_error, "distribute")
    add_RpcAgentServicer_to_server = ImportErrorReporter(
        import_error,
        "distribute",
    )


__all__ = [
    "RpcAgentClient",
    "ResponseStub",
    "RpcMsg",
    "RpcAgentServicer",
    "RpcAgentStub",
    "call_in_thread",
    "add_RpcAgentServicer_to_server",
]
