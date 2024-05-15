# -*- coding: utf-8 -*-
""" Client of rpc agent server """

import threading
import base64
from typing import Optional
from loguru import logger

try:
    import dill
    import grpc
    from grpc import RpcError
    from agentscope.rpc.rpc_agent_pb2 import RpcMsg  # pylint: disable=E0611
    from agentscope.rpc.rpc_agent_pb2_grpc import RpcAgentStub
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    dill = ImportErrorReporter(import_error, "distribute")
    grpc = ImportErrorReporter(import_error, "distribute")
    RpcMsg = ImportErrorReporter(import_error, "distribute")
    RpcAgentStub = ImportErrorReporter(import_error, "distribute")
    RpcError = ImportError


class RpcAgentClient:
    """A client of Rpc agent server"""

    def __init__(self, host: str, port: int, agent_id: str = "") -> None:
        """Init a rpc agent client

        Args:
            host (`str`): the hostname of the rpc agent server which the
            client is connected.
            port (`int`): the port of the rpc agent server which the client
            is connected.
            agent_id (`str`): the agent id of the agent being called.
        """
        self.host = host
        self.port = port
        self.agent_id = agent_id

    def call_func(
        self,
        func_name: str,
        value: Optional[str] = None,
        timeout: int = 300,
    ) -> str:
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
                    agent_id=self.agent_id,
                ),
                timeout=timeout,
            )
            return result_msg.value

    def create_agent(self, agent_configs: dict) -> None:
        """Create a new agent for this client."""
        try:
            if self.agent_id is None or len(self.agent_id) == 0:
                return
            self.call_func(
                "_create_agent",
                base64.b64encode(dill.dumps(agent_configs)).decode("utf-8"),
            )
        except Exception as e:
            logger.error(
                f"Fail to create agent with id [{self.agent_id}]: {e}",
            )

    def delete_agent(self) -> None:
        """
        Delete the agent created by this client.
        """
        try:
            if self.agent_id is not None and len(self.agent_id) > 0:
                self.call_func("_delete_agent", timeout=5)
        except Exception:
            logger.warning(
                f"Fail to delete agent with id [{self.agent_id}]",
            )


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
    value: str,
    func_name: str,
) -> ResponseStub:
    """Call rpc function in a sub-thread.

    Args:
        client (`RpcAgentClient`): the rpc client.
        x (`str`): the value of the reqeust.
        func_name (`str`): the name of the function being called.

    Returns:
        `ResponseStub`: a stub to get the response.
    """
    stub = ResponseStub()

    def wrapper() -> None:
        try:
            resp = client.call_func(
                func_name=func_name,
                value=value,
            )
            stub.set_response(resp)  # type: ignore[arg-type]
        except RpcError as e:
            logger.error(f"Fail to call {func_name} in thread: {e}")
            stub.set_response(str(e))

    thread = threading.Thread(target=wrapper)
    thread.start()
    return stub
