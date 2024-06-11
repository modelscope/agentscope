# -*- coding: utf-8 -*-
""" Server of distributed agent"""
import os
import threading
import traceback
import json
from concurrent import futures
from multiprocessing.synchronize import Event as EventClass
from typing import Any
from loguru import logger
import requests

try:
    import dill
    import psutil
    import grpc
    from grpc import ServicerContext
    from google.protobuf.empty_pb2 import Empty
    from expiringdict import ExpiringDict
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    dill = ImportErrorReporter(import_error, "distribute")
    psutil = ImportErrorReporter(import_error, "distribute")
    grpc = ImportErrorReporter(import_error, "distribute")
    ServicerContext = ImportErrorReporter(import_error, "distribute")
    Empty = ImportErrorReporter(  # type: ignore[misc]
        import_error,
        "distribute",
    )
    ExpiringDict = ImportErrorReporter(import_error, "distribute")

import agentscope.rpc.rpc_agent_pb2 as agent_pb2
from agentscope.agents.agent import AgentBase
from agentscope.models import read_model_configs
from agentscope.studio._client import _studio_client
from agentscope._runtime import _runtime
from agentscope.exception import StudioRegisterError
from agentscope.rpc.rpc_agent_pb2_grpc import RpcAgentServicer
from agentscope.message import (
    Msg,
    PlaceholderMessage,
    deserialize,
)


def _register_server_to_studio(
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
        stop_event: EventClass,
        host: str = "localhost",
        port: int = None,
        server_id: str = None,
        studio_url: str = None,
        max_pool_size: int = 8192,
        max_timeout_seconds: int = 1800,
    ):
        """Init the AgentServerServicer.

        Args:
            stop_event (`Event`): Event to stop the server.
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
            _register_server_to_studio(
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
        self.pid = os.getpid()
        self.stop_event = stop_event

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

    def get_agent(self, agent_id: str) -> AgentBase:
        """Get the agent by agent id.

        Args:
            agent_id (`str`): the agent id.

        Returns:
            AgentBase: the agent.
        """
        with self.agent_id_lock:
            return self.agent_pool.get(agent_id, None)

    def is_alive(
        self,
        request: Empty,
        _: ServicerContext,
    ) -> agent_pb2.StatusResponse:
        """Check whether the server is alive."""
        return agent_pb2.StatusResponse(ok=True)

    def stop(
        self,
        request: Empty,
        _: ServicerContext,
    ) -> agent_pb2.StatusResponse:
        """Stop the server."""
        self.stop_event.set()
        return agent_pb2.StatusResponse(ok=True)

    def create_agent(
        self,
        request: agent_pb2.CreateAgentRequest,
        context: ServicerContext,
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
                cls = dill.loads(request.agent_source_code)
                cls_name = cls.__name__
                logger.info(
                    f"Load class [{cls_name}] from uploaded source code.",
                )
            else:
                cls_name = agent_configs["class_name"]
                try:
                    cls = AgentBase.get_agent_class(cls_name)
                except ValueError as e:
                    logger.error(
                        f"Agent class [{cls_name}] not found: {str(e)}",
                    )
                    context.abort(
                        grpc.StatusCode.NOT_FOUND,
                        f"Agent class [{cls_name}] not found: {str(e)}",
                    )
            try:
                agent_instance = cls(
                    *agent_configs["args"],
                    **agent_configs["kwargs"],
                )
            except Exception as e:
                logger.error(
                    f"Failed to create agent instance <{cls_name}>: {str(e)}",
                )
                context.abort(
                    grpc.StatusCode.INTERNAL,
                    f"Failed to create agent instance <{cls_name}>: {str(e)}",
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

    def get_agent_id_list(
        self,
        request: Empty,
        context: ServicerContext,
    ) -> agent_pb2.AgentIds:
        """Get id of all agents on the server as a list."""
        with self.agent_id_lock:
            agent_ids = self.agent_pool.keys()
            return agent_pb2.AgentIds(agent_ids=agent_ids)

    def get_agent_info(
        self,
        request: agent_pb2.AgentIds,
        context: ServicerContext,
    ) -> agent_pb2.StatusResponse:
        """Get the agent information of the specific agent_id"""
        result = {}
        with self.agent_id_lock:
            for agent_id in request.agent_ids:
                if agent_id in self.agent_pool:
                    result[agent_id] = str(self.agent_pool[agent_id])
                else:
                    logger.warning(
                        f"Getting info of a non-existent agent [{agent_id}].",
                    )
            return agent_pb2.StatusResponse(
                ok=True,
                message=json.dumps(result),
            )

    def get_server_info(
        self,
        request: Empty,
        context: ServicerContext,
    ) -> agent_pb2.StatusResponse:
        """Get the agent server resource usage information."""
        status = {}
        status["pid"] = self.pid
        process = psutil.Process(self.pid)
        status["CPU Times"] = process.cpu_times()
        status["CPU Percent"] = process.cpu_percent()
        status["Memory Usage"] = process.memory_info().rss
        return agent_pb2.StatusResponse(ok=True, message=json.dumps(status))

    def set_model_configs(
        self,
        request: agent_pb2.JsonMsg,
        context: ServicerContext,
    ) -> agent_pb2.StatusResponse:
        """Set the model configs of the agent server."""
        model_configs = json.loads(request.value)
        try:
            read_model_configs(model_configs)
        except Exception as e:
            return agent_pb2.StatusResponse(
                ok=False,
                message=str(e),
            )
        return agent_pb2.StatusResponse(ok=True)

    def get_agent_memory(
        self,
        request: agent_pb2.AgentIds,
        context: ServicerContext,
    ) -> agent_pb2.JsonMsg:
        """Get the memory of a specific agent."""
        agent_id = request.agent_ids[0]
        agent = self.get_agent(agent_id=agent_id)
        if agent is None:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Agent [{agent_id}] not found",
            )
        if agent.memory is None:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Agent [{agent_id}] has no memory",
            )
        return agent_pb2.JsonMsg(
            value=json.dumps(agent.memory.get_memory()),
        )

    def download_file(
        self,
        request: agent_pb2.FileRequest,
        context: ServicerContext,
    ) -> Any:
        """Download file from local path."""
        filepath = request.path
        if not os.path.exists(filepath):
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"File {filepath} not found",
            )

        with open(filepath, "rb") as f:
            while True:
                piece = f.read(1024 * 1024)  # send 1MB each time
                if not piece:
                    break
                yield agent_pb2.FileResponse(data=piece)

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
            self._process_messages,
            task_id,
            request.agent_id,
            msg,  # type: ignore[arg-type]
        )
        return agent_pb2.RpcMsg(
            value=Msg(  # type: ignore[arg-type]
                name=self.get_agent(request.agent_id).name,
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

    def _process_messages(
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
        agent = self.get_agent(agent_id)
        try:
            result = agent.reply(task_msg)
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
