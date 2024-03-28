# -*- coding: utf-8 -*-
""" Client of rpc agent server """

import json
import threading
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

    def call_func(self, func_name: str, value: Optional[str] = None) -> str:
        """Call the specific function of rpc server.

        Args:
            func_name (`str`): the name of the function being called.
            x (`str`, optional): the seralized input value. Defaults to None.

        Returns:
            str: serialized return data.
        """
        with grpc.insecure_channel(f"{self.host}:{self.port}") as channel:
            stub = RpcAgentStub(channel)
            result_msg = stub.call_func(
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


class ResponseStub:
    """A stub used to save the response of an rpc call in a sub-thread."""

    def __init__(self) -> None:
        self.response = None
        self.condition = threading.Condition()

    def set_response(self, response: str) -> None:
        """Set the message."""
        with self.condition:
            self.response = response
            self.condition.notify_all()

    def get_response(self) -> str:
        """Get the message."""
        with self.condition:
            while self.response is None:
                self.condition.wait()
            return self.response


def call_in_thread(
    client: RpcAgentClient,
    x: dict,
    func_name: str,
) -> ResponseStub:
    """Call rpc function in a sub-thread.

    Args:
        client (`RpcAgentClient`): the rpc client.
        x (`dict`): the value of the reqeust.
        func_name (`str`): the name of the function being called.

    Returns:
        _type_: _description_
    """
    stub = ResponseStub()

    def wrapper() -> None:
        resp = client.call_func(
            func_name=func_name,
            value=x.serialize() if x is not None else "",
        )
        stub.set_response(resp)  # type: ignore[arg-type]

    thread = threading.Thread(target=wrapper)
    thread.start()
    return stub
