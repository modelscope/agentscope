# -*- coding: utf-8 -*-
""" Server of distributed agent"""
import threading
import traceback
from concurrent import futures
from loguru import logger

try:
    import dill
    import grpc
    from grpc import ServicerContext
    from google.protobuf.empty_pb2 import Empty
    from expiringdict import ExpiringDict
    import agentscope.rpc.rpc_agent_pb2 as agent_pb2
    from agentscope.rpc.rpc_agent_pb2_grpc import RpcAgentServicer
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    dill = ImportErrorReporter(import_error, "distribute")
    grpc = ImportErrorReporter(import_error, "distribute")
    Empty = ImportErrorReporter(  # type: ignore[misc]
        import_error,
        "distribute",
    )
    ServicerContext = ImportErrorReporter(import_error, "distribute")
    ExpiringDict = ImportErrorReporter(import_error, "distribute")
    # agent_pb2 = ImportErrorReporter(import_error, "distribute")
    RpcAgentServicer = ImportErrorReporter(import_error, "distribute")

from ..agents.agent import AgentBase
from ..message import (
    Msg,
    PlaceholderMessage,
    deserialize,
)


class AgentServerServicer(RpcAgentServicer):
    """A Servicer for RPC Agent Server (formerly RpcServerSideWrapper)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = None,
        max_pool_size: int = 8192,
        max_timeout_seconds: int = 1800,
    ):
        """Init the AgentServerServicer.

        Args:
            host (`str`, defaults to "localhost"):
                Hostname of the rpc agent server.
            port (`int`, defaults to `None`):
                Port of the rpc agent server.
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

    def is_alive(
        self,
        request: Empty,
        _: ServicerContext,
    ) -> agent_pb2.StatusResponse:
        """Check whether the server is alive."""
        return agent_pb2.StatusResponse(ok=True)

    def create_agent(
        self,
        request: agent_pb2.CreateAgentRequest,
        _: ServicerContext,
    ) -> agent_pb2.StatusResponse:
        """Create a new agent on the server."""
        agent_id = request.agent_id
        with self.agent_id_lock:
            if agent_id in self.agent_pool:
                return agent_pb2.StatusResponse(
                    ok=False,
                    message=f"Agent with agent_id [{agent_id}] already exists",
                )
            agent_configs = dill.loads(request.agent_init_args)
            if len(request.agent_source_code) > 0:
                exec(request.agent_source_code, globals())
                cls_name = (
                    request.agent_source_code.split("class ")[1]
                    .split(":")[0]
                    .split("(")[0]
                    .strip()
                )
                logger.info(
                    f"Load class [{cls_name}] from uploaded source code.",
                )
                cls = globals()[cls_name]
            else:
                cls_name = agent_configs["class_name"]
                cls = AgentBase.get_agent_class(cls_name)
            agent_instance = cls(
                *agent_configs["args"],
                **agent_configs["kwargs"],
            )
            agent_instance._agent_id = agent_id  # pylint: disable=W0212
            self.agent_pool[agent_id] = agent_instance
            logger.info(f"create agent instance <{cls_name}>[{agent_id}]")
            return agent_pb2.StatusResponse(ok=True)

    def delete_agent(
        self,
        request: agent_pb2.AgentIds,
        _: ServicerContext,
    ) -> agent_pb2.StatusResponse:
        """Delete agents from the server.

        Args:
            request (`AgentIds`): The `agent_ids` field is the agent_id of the
            agents to be deleted.
        """
        agent_ids = request.agent_ids
        with self.agent_id_lock:
            for aid in agent_ids:
                if aid in self.agent_pool:
                    agent = self.agent_pool.pop(aid)
                    logger.info(
                        f"delete agent instance <{agent.__class__.__name__}>"
                        f"[{aid}]",
                    )
                else:
                    logger.warning(
                        f"try to delete a non-existent agent [{aid}].",
                    )
            return agent_pb2.StatusResponse(ok=True)

    def clone_agent(
        self,
        request: agent_pb2.AgentIds,
        _: ServicerContext,
    ) -> agent_pb2.AgentIds:
        """Clone a new agent instance from the origin instance.

        Args:
            request (`AgentIds`): The `agent_ids` field is the agent_id of the
            agent to be cloned.

        Returns:
            `AgentIds`: The agent_id of generated agent. Empty if clone failed.
        """
        agent_id = request.agent_ids[0]
        with self.agent_id_lock:
            if agent_id not in self.agent_pool:
                logger.error(
                    f"try to clone a non-existent agent [{agent_id}].",
                )
                return agent_pb2.AgentIds()
            ori_agent = self.agent_pool[agent_id]
        new_agent = ori_agent.__class__(
            *ori_agent._init_settings["args"],  # pylint: disable=W0212
            **ori_agent._init_settings["kwargs"],  # pylint: disable=W0212
        )
        with self.agent_id_lock:
            self.agent_pool[new_agent.agent_id] = new_agent
        return agent_pb2.AgentIds(agent_ids=[new_agent.agent_id])

    def call_agent_func(  # pylint: disable=W0236
        self,
        request: agent_pb2.RpcMsg,
        context: ServicerContext,
    ) -> agent_pb2.RpcMsg:
        """Call the specific servicer function."""
        if not self.agent_exists(request.agent_id):
            return context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Agent [{request.agent_id}] not exists.",
            )
        if hasattr(self, request.target_func):
            return getattr(self, request.target_func)(request)
        else:
            # TODO: support other user defined method
            logger.error(f"Unsupported method {request.target_func}")
            return context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported method {request.target_func}",
            )

    def update_placeholder(
        self,
        request: agent_pb2.UpdatePlaceholderRequest,
        context: ServicerContext,
    ) -> agent_pb2.RpcMsg:
        """Update the value of a placeholder."""
        task_id = request.task_id
        while True:
            result = self.result_pool.get(task_id)
            if isinstance(result, threading.Condition):
                with result:
                    result.wait(timeout=1)
            else:
                break
        return agent_pb2.RpcMsg(value=result.serialize())

    def _reply(self, request: agent_pb2.RpcMsg) -> agent_pb2.RpcMsg:
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
        return agent_pb2.RpcMsg(
            value=Msg(  # type: ignore[arg-type]
                name=self.agent_pool[request.agent_id].name,
                content=None,
                task_id=task_id,
            ).serialize(),
        )

    def _observe(self, request: agent_pb2.RpcMsg) -> agent_pb2.RpcMsg:
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
        return agent_pb2.RpcMsg()

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
