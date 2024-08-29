# -*- coding: utf-8 -*-
""" Client of rpc agent server """

import threading
import json
import os
from typing import Optional, Sequence, Union, Generator, Callable, Any
from concurrent.futures import Future
from loguru import logger

from ..message import Msg

try:
    import cloudpickle as pickle
    import grpc
    from google.protobuf.empty_pb2 import Empty
    from agentscope.rpc.rpc_agent_pb2_grpc import RpcAgentStub
    import agentscope.rpc.rpc_agent_pb2 as agent_pb2
except ImportError as import_error:
    from agentscope.utils.common import ImportErrorReporter

    pickle = ImportErrorReporter(import_error, "distribute")
    grpc = ImportErrorReporter(import_error, "distribute")
    agent_pb2 = ImportErrorReporter(import_error, "distribute")
    RpcAgentStub = ImportErrorReporter(import_error, "distribute")
    RpcError = ImportError

from ..utils.common import _generate_id_from_seed
from ..exception import AgentServerNotAliveError
from ..constants import _DEFAULT_RPC_OPTIONS
from ..exception import AgentCallError, AgentCreationError
from ..manager import FileManager


# TODO: rename to RpcClient
class RpcAgentClient:
    """A client of Rpc agent server"""

    _CHANNEL_POOL = {}

    def __init__(
        self,
        host: str,
        port: int,
    ) -> None:
        """Init a rpc agent client

        Args:
            host (`str`): The hostname of the rpc agent server which the
            client is connected.
            port (`int`): The port of the rpc agent server which the client
            is connected.
        """
        self.host = host
        self.port = port
        self.channel = RpcAgentClient._get_channel(host, port)

    @classmethod
    def _get_channel(
        cls,
        host: str,
        port: int,
    ) -> Any:
        """Get a channel from channel pool."""
        if f"{host}:{port}" not in RpcAgentClient._CHANNEL_POOL:
            RpcAgentClient._CHANNEL_POOL[
                f"{host}:{port}"
            ] = grpc.insecure_channel(
                f"{host}:{port}",
                options=_DEFAULT_RPC_OPTIONS,
            )
        return RpcAgentClient._CHANNEL_POOL[f"{host}:{port}"]

    def call_agent_func(
        self,
        func_name: str,
        agent_id: str,
        value: Optional[bytes] = None,
        timeout: int = 300,
    ) -> bytes:
        """Call the specific function of an agent running on the server.

        Args:
            func_name (`str`): The name of the function being called.
            value (`bytes`, optional): The serialized function input value.
            Defaults to None.
            timeout (`int`, optional): The timeout for the RPC call in seconds.
            Defaults to 300.

        Returns:
            bytes: serialized return data.
        """
        try:
            stub = RpcAgentStub(self.channel)
            result_msg = stub.call_agent_func(
                agent_pb2.CallFuncRequest(
                    target_func=func_name,
                    value=value,
                    agent_id=agent_id,
                ),
                timeout=timeout,
            )
            return result_msg.value
        except Exception as e:
            # check the server and raise a more reasonable error
            if not self.is_alive():
                raise AgentServerNotAliveError(
                    host=self.host,
                    port=self.port,
                    message=str(e),
                ) from e
            raise e

    def is_alive(self) -> bool:
        """Check if the agent server is alive.

        Returns:
            bool: Indicate whether the server is alive.
        """

        try:
            stub = RpcAgentStub(self.channel)
            status = stub.is_alive(Empty(), timeout=5)
            if not status.ok:
                raise AgentServerNotAliveError(
                    host=self.host,
                    port=self.port,
                )
            return status.ok
        except Exception:
            logger.info(
                f"Agent server [{self.host}:{self.port}] not alive.",
            )
            return False

    def stop(self) -> None:
        """Stop the agent server."""
        try:
            stub = RpcAgentStub(self.channel)
            logger.info(
                f"Stopping agent server at [{self.host}:{self.port}].",
            )
            resp = stub.stop(Empty(), timeout=5)
            if resp.ok:
                logger.info(
                    f"Agent server at [{self.host}:{self.port}] stopped.",
                )
            else:
                logger.error(
                    f"Fail to stop the agent server: {resp.message}",
                )
        except Exception as e:
            logger.error(
                f"Fail to stop the agent server: {e}",
            )

    def create_agent(
        self,
        agent_configs: dict,
        agent_id: str = None,
    ) -> bool:
        """Create a new agent for this client.

        Args:
            agent_configs (`dict`): Init configs of the agent, generated by
            `_AgentMeta`.
            agent_id (`str`): agent_id of the created agent.

        Returns:
            bool: Indicate whether the creation is successful
        """
        try:
            stub = RpcAgentStub(self.channel)
            status = stub.create_agent(
                agent_pb2.CreateAgentRequest(
                    agent_id=agent_id,
                    agent_init_args=pickle.dumps(agent_configs),
                ),
            )
            if not status.ok:
                logger.error(
                    f"Error when creating agent: {status.message}",
                )
            return status.ok
        except Exception as e:
            # check the server and raise a more reasonable error
            if not self.is_alive():
                raise AgentServerNotAliveError(
                    host=self.host,
                    port=self.port,
                    message=str(e),
                ) from e
            raise AgentCreationError(host=self.host, port=self.port) from e

    def delete_agent(
        self,
        agent_id: str = None,
    ) -> bool:
        """
        Delete agents with the specific agent_id.

        Args:
            agent_id (`str`): id of the agent to be deleted.

        Returns:
            bool: Indicate whether the deletion is successful
        """
        stub = RpcAgentStub(self.channel)
        status = stub.delete_agent(
            agent_pb2.StringMsg(value=agent_id),
        )
        if not status.ok:
            logger.error(f"Error when deleting agent: {status.message}")
        return status.ok

    def delete_all_agent(self) -> bool:
        """Delete all agents on the server."""
        stub = RpcAgentStub(self.channel)
        status = stub.delete_all_agents(Empty())
        if not status.ok:
            logger.error(f"Error when delete all agents: {status.message}")
        return status.ok

    def clone_agent(self, agent_id: str) -> Optional[str]:
        """Clone a new agent instance from the origin instance.

        Args:
            agent_id (`str`): The agent_id of the agent to be cloned.

        Returns:
            str: The `agent_id` of the generated agent.
        """
        stub = RpcAgentStub(self.channel)
        resp = stub.clone_agent(
            agent_pb2.StringMsg(value=agent_id),
        )
        if not resp.ok:
            logger.error(
                f"Error when clone agent [{agent_id}]: {resp.message}",
            )
            return None
        else:
            return resp.message

    def update_placeholder(self, task_id: int) -> str:
        """Update the placeholder value.

        Args:
            task_id (`int`): `task_id` of the PlaceholderMessage.

        Returns:
            bytes: Serialized message value.
        """
        stub = RpcAgentStub(self.channel)
        resp = stub.update_placeholder(
            agent_pb2.UpdatePlaceholderRequest(task_id=task_id),
        )
        if not resp.ok:
            raise AgentCallError(
                host=self.host,
                port=self.port,
                message=f"Failed to update placeholder: {resp.message}",
            )
        return resp.value

    def get_agent_list(self) -> Sequence[dict]:
        """
        Get the summary of all agents on the server as a list.

        Returns:
            Sequence[str]: list of agent summary information.
        """
        stub = RpcAgentStub(self.channel)
        resp = stub.get_agent_list(Empty())
        if not resp.ok:
            logger.error(f"Error when get agent list: {resp.message}")
            return []
        return [
            json.loads(agent_str) for agent_str in json.loads(resp.message)
        ]

    def get_server_info(self) -> dict:
        """Get the agent server resource usage information."""
        try:
            stub = RpcAgentStub(self.channel)
            resp = stub.get_server_info(Empty())
            if not resp.ok:
                logger.error(f"Error in get_server_info: {resp.message}")
                return {}
            return json.loads(resp.message)
        except Exception as e:
            logger.error(f"Error in get_server_info: {e}")
            return {}

    def set_model_configs(
        self,
        model_configs: Union[dict, list[dict]],
    ) -> bool:
        """Set the model configs of the server."""
        stub = RpcAgentStub(self.channel)
        resp = stub.set_model_configs(
            agent_pb2.StringMsg(value=json.dumps(model_configs)),
        )
        if not resp.ok:
            logger.error(f"Error in set_model_configs: {resp.message}")
            return False
        return True

    def get_agent_memory(self, agent_id: str) -> Union[list[Msg], Msg]:
        """Get the memory usage of the specific agent."""
        stub = RpcAgentStub(self.channel)
        resp = stub.get_agent_memory(
            agent_pb2.StringMsg(value=agent_id),
        )
        if not resp.ok:
            logger.error(f"Error in get_agent_memory: {resp.message}")
        return json.loads(resp.message)

    def download_file(self, path: str) -> str:
        """Download a file from a remote server to the local machine.

        Args:
        path (`str`): The path of the file to be downloaded. Note that
            it is the path on the remote server.

        Returns:
            `str`: The path of the downloaded file. Note that it is the path
            on the local machine.
        """

        file_manager = FileManager.get_instance()

        local_filename = (
            f"{_generate_id_from_seed(path, 5)}_{os.path.basename(path)}"
        )

        def _generator() -> Generator[bytes, None, None]:
            for resp in RpcAgentStub(self.channel).download_file(
                agent_pb2.StringMsg(value=path),
            ):
                yield resp.data

        return file_manager.save_file(_generator(), local_filename)

    def __reduce__(self) -> tuple:
        return (
            RpcAgentClient,
            (self.host, self.port),
        )


def call_func_in_thread(func: Callable) -> Future:
    """Call a function in a sub-thread.

    Args:
        func (`Callable`): The function to be called in sub-thread.

    Returns:
        `Future`: A stub to get the response.
    """
    future = Future()

    def wrapper() -> None:
        try:
            result = func()
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)

    thread = threading.Thread(target=wrapper)
    thread.start()

    return future
