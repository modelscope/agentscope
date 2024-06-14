# -*- coding: utf-8 -*-
""" Server of distributed agent"""
import threading
import base64
import json
import traceback
from concurrent import futures
from loguru import logger
import requests

try:
    import dill
    import grpc
    from grpc import ServicerContext
    from expiringdict import ExpiringDict
    from ..rpc.rpc_agent_pb2 import RpcMsg  # pylint: disable=E0611
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    dill = ImportErrorReporter(import_error, "distribute")
    grpc = ImportErrorReporter(import_error, "distribute")
    ServicerContext = ImportErrorReporter(import_error, "distribute")
    ExpiringDict = ImportErrorReporter(import_error, "distribute")
    RpcMsg = ImportErrorReporter(  # type: ignore[misc]
        import_error,
        "distribute",
    )

from .._runtime import _runtime
from ..studio._client import _studio_client
from ..agents.agent import AgentBase
from ..exception import StudioRegisterError
from ..rpc.rpc_agent_pb2_grpc import RpcAgentServicer
from ..message import (
    Msg,
    PlaceholderMessage,
    deserialize,
)


def _register_to_studio(
    studio_url: str,
    server_id: str,
    host: str,
    port: int,
) -> None:
    """Register a server to studio."""
    url = f"{studio_url}/api/servers/register"
    resp = requests.post(
        url,
        json={"server_id": server_id, "host": host, "port": port},
        timeout=10,  # todo: configurable timeout
    )
    if resp.status_code != 200:
        logger.error(f"Failed to register server: {resp.text}")
        raise StudioRegisterError(f"Failed to register server: {resp.text}")


class AgentServerServicer(RpcAgentServicer):
    """A Servicer for RPC Agent Server (formerly RpcServerSideWrapper)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = None,
        server_id: str = None,
        studio_url: str = None,
        max_pool_size: int = 8192,
        max_timeout_seconds: int = 1800,
    ):
        """Init the AgentServerServicer.

        Args:
            host (`str`, defaults to "localhost"):
                Hostname of the rpc agent server.
            port (`int`, defaults to `None`):
                Port of the rpc agent server.
            server_id (`str`, defaults to `None`):
                Server id of the rpc agent server.
            studio_url (`str`, defaults to `None`):
                URL of the AgentScope Studio.
            max_pool_size (`int`, defaults to `8192`):
                The max number of agent reply messages that the server can
                accommodate. Note that the oldest message will be deleted
                after exceeding the pool size.
            max_timeout_seconds (`int`, defaults to `1800`):
                Maximum time for reply messages to be cached in the server.
                Note that expired messages will be deleted.
        """
        self.host = host
        self.port = port
        self.server_id = server_id
        self.studio_url = studio_url
        if studio_url is not None:
            _register_to_studio(
                studio_url=studio_url,
                server_id=server_id,
                host=host,
                port=port,
            )
            _studio_client.initialize(_runtime.runtime_id, studio_url)

        self.result_pool = ExpiringDict(
            max_len=max_pool_size,
            max_age_seconds=max_timeout_seconds,
        )
        self.executor = futures.ThreadPoolExecutor(max_workers=None)
        self.task_id_lock = threading.Lock()
        self.agent_id_lock = threading.Lock()
        self.task_id_counter = 0
        self.agent_pool: dict[str, AgentBase] = {}

    def get_task_id(self) -> int:
        """Get the auto-increment task id.
        Each reply call will get a unique task id."""
        with self.task_id_lock:
            self.task_id_counter += 1
            return self.task_id_counter

    def agent_exists(self, agent_id: str) -> bool:
        """Check whether the agent exists.

        Args:
            agent_id (`str`): the agent id.

        Returns:
            bool: whether the agent exists.
        """
        return agent_id in self.agent_pool

    def check_and_generate_agent(
        self,
        agent_id: str,
        agent_configs: dict,
    ) -> None:
        """
        Check whether the agent exists, and create new agent instance
        for new agent.

        Args:
            agent_id (`str`): the agent id.
            agent_configs (`dict`): configuration used to initialize the agent,
                with three fields (generated in `_AgentMeta`):

                .. code-block:: python

                    {
                        "class_name": {name of the agent}
                        "args": {args in tuple type to init the agent}
                        "kwargs": {args in dict type to init the agent}
                    }

        """
        with self.agent_id_lock:
            if agent_id not in self.agent_pool:
                agent_class_name = agent_configs["class_name"]
                agent_instance = AgentBase.get_agent_class(agent_class_name)(
                    *agent_configs["args"],
                    **agent_configs["kwargs"],
                )
                agent_instance._agent_id = agent_id  # pylint: disable=W0212
                self.agent_pool[agent_id] = agent_instance
                logger.info(f"create agent instance [{agent_id}]")

    def check_and_delete_agent(self, agent_id: str) -> None:
        """
        Check whether the agent exists, and delete the agent instance
        for the agent_id.

        Args:
            agent_id (`str`): the agent id.
        """
        with self.agent_id_lock:
            if agent_id in self.agent_pool:
                self.agent_pool.pop(agent_id)
                logger.info(f"delete agent instance [{agent_id}]")

    def call_func(  # pylint: disable=W0236
        self,
        request: RpcMsg,
        context: ServicerContext,
    ) -> RpcMsg:
        """Call the specific servicer function."""
        if hasattr(self, request.target_func):
            if request.target_func not in ["_create_agent", "_get"]:
                if not self.agent_exists(request.agent_id):
                    return context.abort(
                        grpc.StatusCode.INVALID_ARGUMENT,
                        f"Agent [{request.agent_id}] not exists.",
                    )
            return getattr(self, request.target_func)(request)
        else:
            # TODO: support other user defined method
            logger.error(f"Unsupported method {request.target_func}")
            return context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported method {request.target_func}",
            )

    def _reply(self, request: RpcMsg) -> RpcMsg:
        """Call function of RpcAgentService

        Args:
            request (`RpcMsg`):
                Message containing input parameters or input parameter
                placeholders.

        Returns:
            `RpcMsg`: A serialized Msg instance with attributes name, host,
            port and task_id
        """
        if request.value:
            msg = deserialize(request.value)
        else:
            msg = None
        task_id = self.get_task_id()
        self.result_pool[task_id] = threading.Condition()
        self.executor.submit(
            self.process_messages,
            task_id,
            request.agent_id,
            msg,  # type: ignore[arg-type]
        )
        return RpcMsg(
            value=Msg(  # type: ignore[arg-type]
                name=self.agent_pool[request.agent_id].name,
                content=None,
                task_id=task_id,
            ).serialize(),
        )

    def _get(self, request: RpcMsg) -> RpcMsg:
        """Get a reply message with specific task_id.

        Args:
            request (`RpcMsg`):
                The task id that generated this message, with json format::

                {
                    'task_id': int
                }

        Returns:
            `RpcMsg`: Concrete values of the specific message (or part of it).
        """
        msg = json.loads(request.value)
        while True:
            result = self.result_pool.get(msg["task_id"])
            if isinstance(result, threading.Condition):
                with result:
                    result.wait(timeout=1)
            else:
                break
        return RpcMsg(value=result.serialize())

    def _observe(self, request: RpcMsg) -> RpcMsg:
        """Observe function of the original agent.

        Args:
            request (`RpcMsg`):
                The serialized input to be observed.

        Returns:
            `RpcMsg`: Empty RpcMsg.
        """
        msgs = deserialize(request.value)
        for msg in msgs:
            if isinstance(msg, PlaceholderMessage):
                msg.update_value()
        self.agent_pool[request.agent_id].observe(msgs)
        return RpcMsg()

    def _create_agent(self, request: RpcMsg) -> RpcMsg:
        """Create a new agent instance with the given agent_id.

        Args:
            request (RpcMsg): request message with a `agent_id` field.
        """
        self.check_and_generate_agent(
            request.agent_id,
            agent_configs=(
                dill.loads(base64.b64decode(request.value))
                if request.value
                else None
            ),
        )
        return RpcMsg()

    def _clone_agent(self, request: RpcMsg) -> RpcMsg:
        """Clone a new agent instance from the origin instance.

        Args:
            request (RpcMsg): The `agent_id` field is the agent_id of the
            agent to be cloned.

        Returns:
            `RpcMsg`: The `value` field contains the agent_id of generated
            agent.
        """
        agent_id = request.agent_id
        with self.agent_id_lock:
            if agent_id not in self.agent_pool:
                raise ValueError(f"Agent [{agent_id}] not exists")
            ori_agent = self.agent_pool[agent_id]
        new_agent = ori_agent.__class__(
            *ori_agent._init_settings["args"],  # pylint: disable=W0212
            **ori_agent._init_settings["kwargs"],  # pylint: disable=W0212
        )
        with self.agent_id_lock:
            self.agent_pool[new_agent.agent_id] = new_agent
        return RpcMsg(value=new_agent.agent_id)  # type: ignore[arg-type]

    def _delete_agent(self, request: RpcMsg) -> RpcMsg:
        """Delete the agent instance of the specific agent_id.

        Args:
            request (RpcMsg): request message with a `agent_id` field.
        """
        self.check_and_delete_agent(request.agent_id)
        return RpcMsg()

    def process_messages(
        self,
        task_id: int,
        agent_id: str,
        task_msg: dict = None,
    ) -> None:
        """Processing an input message and generate its reply message.

        Args:
            task_id (`int`): task id of the input message, .
            agent_id (`str`): the id of the agent that accepted the message.
            task_msg (`dict`): the input message.
        """
        if isinstance(task_msg, PlaceholderMessage):
            task_msg.update_value()
        cond = self.result_pool[task_id]
        try:
            result = self.agent_pool[agent_id].reply(task_msg)
            self.result_pool[task_id] = result
        except Exception:
            error_msg = traceback.format_exc()
            logger.error(f"Error in agent [{agent_id}]:\n{error_msg}")
            self.result_pool[task_id] = Msg(
                name="ERROR",
                role="assistant",
                __status="ERROR",
                content=f"Error in agent [{agent_id}]:\n{error_msg}",
            )
        with cond:
            cond.notify_all()
