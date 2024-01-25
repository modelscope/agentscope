# -*- coding: utf-8 -*-
""" Client of rpc agent server """

from typing import Any

try:
    import grpc
except ImportError:
    grpc = None

try:
    from agentscope.rpc.rpc_agent_pb2 import RpcMsg  # pylint: disable=E0611
    from agentscope.rpc.rpc_agent_pb2_grpc import RpcAgentStub
except ModuleNotFoundError:
    RpcMsg = Any
    RpcAgentStub = Any


class RpcAgentClient:
    """A client of Rpc agent server"""

    def __init__(self, host: str, port: int) -> None:
        """Init a rpc agent client

        Args:
            host (str): the hostname of the rpc agent server which the
            client is connected.
            port (int): the port of the rpc agent server which the client
            is connected.
        """
        self.host = host
        self.port = port

    def call_func(self, func_name: str, value: str = None) -> str:
        """Call the specific function of rpc server.

        Args:
            func_name (str): the name of the function being called.
            x (str, optional): the seralized input value. Defaults to None.

        Returns:
            str: serialized return data.
        """
        with grpc.insecure_channel(f"{self.host}:{self.port}") as channel:
            stub = RpcAgentStub(channel)
            result_msg = stub.call_func(
                RpcMsg(value=value, target_func=func_name),
            )
            return result_msg.value
