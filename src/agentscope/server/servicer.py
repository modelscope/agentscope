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
    import cloudpickle as pickle
    import psutil
    import grpc
    from grpc import ServicerContext
    from google.protobuf.empty_pb2 import Empty
    from expiringdict import ExpiringDict
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    pickle = ImportErrorReporter(import_error, "distribute")
    psutil = ImportErrorReporter(import_error, "distribute")
    grpc = ImportErrorReporter(import_error, "distribute")
    ServicerContext = ImportErrorReporter(import_error, "distribute")
    Empty = ImportErrorReporter(  # type: ignore[misc]
        import_error,
        "distribute",
    )
    ExpiringDict = ImportErrorReporter(import_error, "distribute")

import agentscope.rpc.rpc_agent_pb2 as agent_pb2
from agentscope.manager import ModelManager
from agentscope.manager import ASManager
from agentscope.studio._client import _studio_client
from agentscope.exception import StudioRegisterError
from agentscope.rpc.rpc_agent_pb2_grpc import RpcAgentServicer
from agentscope.rpc.rpc_agent_client import RpcAgentClient
from agentscope.message import (
    PlaceholderMessage,
)


class TaskResult:
    """Use this class to get the the result from rpc server."""

    # TODO: merge into placeholder

    def __init__(self, host: str, port: int, task_id: int) -> None:
        self.host = host
        self.port = port
        self.task_id = task_id

    def get(self) -> Any:
        """Get the value"""
        return pickle.loads(
            RpcAgentClient(self.host, self.port).update_placeholder(
                self.task_id,
            ),
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
        json={
            "server_id": server_id,
            "host": host,
            "port": port,
        },
        timeout=10,  # todo: configurable timeout
    )
    if resp.status_code != 200:
        logger.error(f"Failed to register server: {resp.text}")
        raise StudioRegisterError(f"Failed to register server: {resp.text}")


class _AgentError:
    """Use this class to represent an error when calling agent funcs."""

    def __init__(self, agent_id: str, err_msg: str) -> None:
        self.agent_id = agent_id
        self.err_msg = err_msg

    def __repr__(self) -> str:
        return f"Agent[{self.agent_id}] error: {self.err_msg}"


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
        max_timeout_seconds: int = 7200,
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
            max_timeout_seconds (`int`, defaults to `7200`):
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
            run_id = ASManager.get_instance().run_id
            _studio_client.initialize(run_id, studio_url)

        self.result_pool = ExpiringDict(
            max_len=max_pool_size,
            max_age_seconds=max_timeout_seconds,
        )
        self.executor = futures.ThreadPoolExecutor(max_workers=None)
        self.task_id_lock = threading.Lock()
        self.agent_id_lock = threading.Lock()
        self.task_id_counter = 0
        self.agent_pool: dict[str, Any] = {}
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

    def get_agent(self, agent_id: str) -> Any:
        """Get the object by agent id.

        Args:
            agent_id (`str`): the agent id.

        Returns:
            Any: the object.
        """
        with self.agent_id_lock:
            return self.agent_pool.get(agent_id, None)

    def is_alive(
        self,
        request: Empty,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Check whether the server is alive."""
        return agent_pb2.GeneralResponse(ok=True)

    def stop(
        self,
        request: Empty,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Stop the server."""
        self.stop_event.set()
        return agent_pb2.GeneralResponse(ok=True)

    def create_agent(
        self,
        request: agent_pb2.CreateAgentRequest,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Create a new agent on the server."""
        agent_id = request.agent_id
        agent_configs = pickle.loads(request.agent_init_args)
        type_name = agent_configs["type"]
        cls_name = agent_configs["class_name"]
        try:
            if type_name == "agent":
                from agentscope.agents import AgentBase, RpcAgent

                cls = AgentBase.get_agent_class(cls_name)
                rpc_cls = RpcAgent
            elif type_name == "env":
                from agentscope.environment import Env, RpcEnv

                cls = Env.get_env_class(cls_name)
                rpc_cls = RpcEnv
            else:
                raise ValueError("Unknown type: {type_name}")
        except ValueError as e:
            err_msg = (f"Class [{cls_name}] not found: {str(e)}",)
            logger.error(err_msg)
            return agent_pb2.GeneralResponse(ok=False, message=err_msg)
        try:
            instance = cls(
                *agent_configs["args"],
                **agent_configs["kwargs"],
            )
        except Exception as e:
            err_msg = (
                f"Failed to create agent instance <{cls_name}>: {str(e)}",
            )
            logger.error(err_msg)
            return agent_pb2.GeneralResponse(ok=False, message=err_msg)

        # Reset the __reduce_ex__ method of the instance
        # With this method, all objects stored in agent_pool will be serialized
        # into their Rpc version
        rpc_init_cfg = (
            instance.name,
            cls,
            self.host,
            self.port,
            agent_id,
            True,
        )
        instance._dist_config = {  # pylint: disable=W0212
            "cls": rpc_cls,
            "args": rpc_init_cfg,
        }

        def to_rpc(obj, _) -> tuple:  # type: ignore[no-untyped-def]
            return (
                obj._dist_config["cls"],  # pylint: disable=W0212
                obj._dist_config["args"],  # pylint: disable=W0212
            )

        instance.__reduce_ex__ = to_rpc.__get__(  # pylint: disable=E1120
            instance,
        )
        instance._agent_id = agent_id  # pylint: disable=W0212

        with self.agent_id_lock:
            if agent_id in self.agent_pool:
                return agent_pb2.GeneralResponse(
                    ok=False,
                    message=f"Agent with agent_id [{agent_id}] already exists",
                )
            self.agent_pool[agent_id] = instance
        logger.info(f"create agent instance <{cls_name}>[{agent_id}]")
        return agent_pb2.GeneralResponse(ok=True)

    def delete_agent(
        self,
        request: agent_pb2.StringMsg,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Delete agents from the server.

        Args:
            request (`StringMsg`): The `value` field is the agent_id of the
            agents to be deleted.
        """
        aid = request.value
        with self.agent_id_lock:
            if aid in self.agent_pool:
                agent = self.agent_pool.pop(aid)
                logger.info(
                    f"delete agent instance <{agent.__class__.__name__}>"
                    f"[{aid}]",
                )
                return agent_pb2.GeneralResponse(ok=True)
            else:
                logger.warning(
                    f"try to delete a non-existent agent [{aid}].",
                )
                return agent_pb2.GeneralResponse(
                    ok=False,
                    message=f"try to delete a non-existent agent [{aid}].",
                )

    def clone_agent(
        self,
        request: agent_pb2.StringMsg,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Clone a new agent instance from the origin instance.

        Args:
            request (`StringMsg`): The `value` field is the agent_id of the
            agent to be cloned.

        Returns:
            `GeneralResponse`: The agent_id of generated agent.
            Empty if clone failed.
        """
        agent_id = request.value
        with self.agent_id_lock:
            if agent_id not in self.agent_pool:
                logger.error(
                    f"Try to clone a non-existent agent [{agent_id}].",
                )
                return agent_pb2.GeneralResponse(
                    ok=False,
                    message=f"Try to clone a non-existent agent [{agent_id}].",
                )
            ori_agent = self.agent_pool[agent_id]
        new_agent = ori_agent.__class__(
            *ori_agent._init_settings["args"],  # pylint: disable=W0212
            **ori_agent._init_settings["kwargs"],  # pylint: disable=W0212
        )
        with self.agent_id_lock:
            self.agent_pool[new_agent.agent_id] = new_agent
        return agent_pb2.GeneralResponse(ok=True, message=new_agent.agent_id)

    def delete_all_agents(
        self,
        request: Empty,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        with self.agent_id_lock:
            self.agent_pool.clear()
            logger.info(
                "Deleting all agent instances on the server",
            )
        return agent_pb2.GeneralResponse(ok=True)

    def call_agent_func(  # pylint: disable=W0236
        self,
        request: agent_pb2.CallFuncRequest,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Call the specific servicer function."""
        if not self.agent_exists(request.agent_id):
            return context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Agent [{request.agent_id}] not exists.",
            )
        if hasattr(self, request.target_func):
            return getattr(self, request.target_func)(request)
        else:
            return self.call_custom_func(
                request.agent_id,
                request.target_func,
                request.value,
            )

    def call_custom_func(
        self,
        agent_id: str,
        func_name: str,
        raw_value: bytes,
    ) -> agent_pb2.GeneralResponse:
        """Call a custom function"""
        agent = self.get_agent(agent_id)
        if not agent:
            return agent_pb2.GeneralResponse(
                success=False,
                message=f"Agent [{agent_id}] not exists.",
            )
        func = getattr(agent, func_name)
        if (
            hasattr(func, "_is_async")
            and func._is_async  # pylint: disable=W0212
        ):  # pylint: disable=W0212
            task_id = self.get_task_id()
            self.result_pool[task_id] = threading.Condition()
            self.executor.submit(
                self._process_messages,
                task_id,
                agent_id,
                func_name,
                raw_value,
            )
            return agent_pb2.CallFuncResponse(
                ok=True,
                value=pickle.dumps(
                    TaskResult(
                        host=self.host,
                        port=self.port,
                        task_id=task_id,
                    ),
                ),
            )
        args = pickle.loads(raw_value)
        res = getattr(agent, func_name)(
            *args.get("args", ()),
            **args.get("kwargs", {}),
        )
        return agent_pb2.CallFuncResponse(
            ok=True,
            value=pickle.dumps(res),
        )

    def update_placeholder(
        self,
        request: agent_pb2.UpdatePlaceholderRequest,
        context: ServicerContext,
    ) -> agent_pb2.CallFuncResponse:
        """Update the value of a placeholder."""
        task_id = request.task_id
        while True:
            result = self.result_pool.get(task_id)
            if isinstance(result, threading.Condition):
                with result:
                    result.wait(timeout=1)
            else:
                break
        if isinstance(result, _AgentError):
            return agent_pb2.CallFuncResponse(
                ok=False,
                message=result.err_msg,
            )
        else:
            return agent_pb2.CallFuncResponse(
                ok=True,
                value=pickle.dumps(result),
            )

    def get_agent_list(
        self,
        request: Empty,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Get id of all agents on the server as a list."""
        with self.agent_id_lock:
            summaries = []
            for agent in self.agent_pool.values():
                summaries.append(str(agent))
            return agent_pb2.GeneralResponse(
                ok=True,
                message=json.dumps(summaries),
            )

    def get_server_info(
        self,
        request: Empty,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Get the agent server resource usage information."""
        status = {}
        status["pid"] = self.pid
        status["id"] = self.server_id
        process = psutil.Process(self.pid)
        status["cpu"] = process.cpu_percent(interval=1)
        status["mem"] = process.memory_info().rss / (1024**2)
        status["size"] = len(self.agent_pool)
        return agent_pb2.GeneralResponse(ok=True, message=json.dumps(status))

    def set_model_configs(
        self,
        request: agent_pb2.StringMsg,
        context: ServicerContext,
    ) -> agent_pb2.GeneralResponse:
        """Set the model configs of the agent server."""
        model_configs = json.loads(request.value)
        try:
            ModelManager.get_instance().load_model_configs(model_configs)
        except Exception as e:
            return agent_pb2.GeneralResponse(
                ok=False,
                message=str(e),
            )
        return agent_pb2.GeneralResponse(ok=True)

    def get_agent_memory(
        self,
        request: agent_pb2.StringMsg,
        context: ServicerContext,
    ) -> agent_pb2.StringMsg:
        """Get the memory of a specific agent."""
        agent_id = request.value
        agent = self.get_agent(agent_id=agent_id)
        if agent is None:
            return agent_pb2.GeneralResponse(
                ok=False,
                message="Agent [{agent_id}] has not found",
            )
        if agent.memory is None:
            return agent_pb2.GeneralResponse(
                ok=False,
                message="Agent [{agent_id}] has no memory",
            )
        return agent_pb2.GeneralResponse(
            ok=True,
            message=json.dumps(agent.memory.get_memory()),
        )

    def download_file(
        self,
        request: agent_pb2.StringMsg,
        context: ServicerContext,
    ) -> Any:
        """Download file from local path."""
        filepath = request.value
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
                yield agent_pb2.ByteMsg(data=piece)

    def _reply(
        self,
        request: agent_pb2.CallFuncRequest,
    ) -> agent_pb2.CallFuncResponse:
        """Call function of RpcAgentService

        Args:
            request (`CallFuncRequest`):
                Message containing input parameters or input parameter
                placeholders.

        Returns:
            `CallFuncRequest`: A serialized Msg instance with attributes name,
            host, port and task_id
        """
        task_id = self.get_task_id()
        self.result_pool[task_id] = threading.Condition()
        self.executor.submit(
            self._process_messages,
            task_id,
            request.agent_id,
            "reply",
            request.value,
        )
        return agent_pb2.CallFuncResponse(
            ok=True,
            value=pickle.dumps(
                task_id,
            ),
        )

    def _observe(
        self,
        request: agent_pb2.CallFuncRequest,
    ) -> agent_pb2.CallFuncResponse:
        """Observe function of the original agent.

        Args:
            request (`CallFuncRequest`):
                The serialized input to be observed.

        Returns:
            `CallFuncRequest`: Empty CallFuncRequest.
        """
        msgs = pickle.loads(request.value)
        if not isinstance(msgs, list):
            msgs = [msgs]
        for msg in msgs:
            if isinstance(msg, PlaceholderMessage):
                msg.update_value()
        self.agent_pool[request.agent_id].observe(msgs)
        return agent_pb2.CallFuncResponse(ok=True)

    def _process_messages(
        self,
        task_id: int,
        agent_id: str,
        target_func: str,
        raw_msg: bytes,
    ) -> None:
        """Processing an input message and generate its reply message.

        Args:
            task_id (`int`): task id of the input message, .
            agent_id (`str`): the id of the agent that accepted the message.
            target_func (`str`): the name of the function that will be called.
            raw_msg (`bytes`): the input serialized message.
        """
        if raw_msg is not None:
            msg = pickle.loads(raw_msg)
        else:
            msg = None
        cond = self.result_pool[task_id]
        agent = self.get_agent(agent_id)
        if isinstance(msg, PlaceholderMessage):
            msg.update_value()
        try:
            if target_func == "reply":
                result = getattr(agent, target_func)(msg)
            else:
                result = getattr(agent, target_func)(
                    *msg.get("args", ()),
                    **msg.get("kwargs", {}),
                )
            self.result_pool[task_id] = result
        except Exception:
            error_msg = traceback.format_exc()
            logger.error(f"Error in agent [{agent_id}]:\n{error_msg}")
            self.result_pool[task_id] = _AgentError(agent_id, error_msg)
        with cond:
            cond.notify_all()
