# -*- coding: utf-8 -*-
""" Client of rpc agent server """

import json
from typing import Any, Optional
from loguru import logger

try:
    import grpc
except ImportError:
    grpc = None

try:
    from agentscope.rpc.rpc_agent_pb2 import RpcMsg  # pylint: disable=E0611
    from agentscope.rpc.rpc_agent_pb2_grpc import RpcAgentStub
except ModuleNotFoundError:
    RpcMsg = Any  # type: ignore[misc]
    RpcAgentStub = Any


class RpcAgentClient:
    """A client of Rpc agent server"""

    def __init__(self, host: str, port: int, session_id: str = "") -> None:
        """Init a rpc agent client

        Args:
            host (`str`): the hostname of the rpc agent server which the
            client is connected.
            port (`int`): the port of the rpc agent server which the client
            is connected.
            session_id (`str`): the session id of the agent being called.
        """
        self.host = host
        self.port = port
        self.session_id = session_id
        self.channel = grpc.insecure_channel(f"{self.host}:{self.port}")
        self.stub = RpcAgentStub(self.channel)

    def call_func(self, func_name: str, value: Optional[str] = None) -> str:
        """Call the specific function of rpc server.

        Args:
            func_name (`str`): the name of the function being called.
            x (`str`, optional): the seralized input value. Defaults to None.

        Returns:
            str: serialized return data.
        """
        result_msg = self.stub.call_func(
            RpcMsg(
                value=value,
                target_func=func_name,
                session_id=self.session_id,
            ),
        )
        return result_msg.value

    def create_session(self, agent_configs: Optional[dict]) -> None:
        """Create a new session for this client."""
        try:
            if self.session_id is None or len(self.session_id) == 0:
                return
            self.call_func(
                func_name="_create_session",
                value=(
                    None
                    if agent_configs is None
                    else json.dumps(agent_configs)
                ),
            )
        except Exception as e:
            logger.warning(e)
            logger.warning(
                f"Fail to create session with id [{self.session_id}]",
            )

    def delete_session(self) -> None:
        """
        Delete the session created by this client.
        """
        try:
            if self.session_id is not None and len(self.session_id) > 0:
                self.call_func("_delete_session")
        except Exception:
            return
