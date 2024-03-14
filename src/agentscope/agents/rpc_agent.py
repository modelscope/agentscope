# -*- coding: utf-8 -*-
""" Base class for Rpc Agent """

from multiprocessing import (
    Process,
    Event,
    Pipe,
)
from multiprocessing.synchronize import Event as EventClass
import socket
import threading
import time
import json
from typing import Any
from typing import Optional
from typing import Union
from typing import Type
from typing import Sequence
from queue import Queue
from concurrent import futures
from loguru import logger

try:
    import grpc
    from grpc import ServicerContext
except ImportError:
    grpc = None
    ServicerContext = Any

try:
    from expiringdict import ExpiringDict
except ImportError:
    ExpiringDict = None

from agentscope._init import init_process, _INIT_SETTINGS
from agentscope.agents.agent import AgentBase
from agentscope.message import (
    Msg,
    PlaceholderMessage,
    deserialize,
    serialize,
)
from agentscope.rpc import (
    RpcAgentClient,
    RpcMsg,
    RpcAgentServicer,
    add_RpcAgentServicer_to_server,
)


def rpc_servicer_method(  # type: ignore [no-untyped-def]
    func,
):
    """A decorator used to identify that the specific method is an rpc agent
    servicer method, which can only be run in the rpc server process.
    """

    def inner(rpc_agent, msg):  # type: ignore [no-untyped-def]
        if not rpc_agent.is_servicer:
            error_msg = f"Detect main process try to use rpc servicer method \
                 [{func.__name__}]"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return func(rpc_agent, msg)

    return inner


class RpcAgent(AgentBase):
    """A wrapper to extend an AgentBase into a gRPC Client."""

    def __init__(
        self,
        name: str,
        agent_class: Type[AgentBase],
        agent_configs: dict,
        host: str = "localhost",
        port: int = None,
        max_pool_size: int = 100,
        max_timeout_seconds: int = 1800,
        launch_server: bool = True,
        local_mode: bool = True,
        lazy_launch: bool = True,
    ) -> None:
        """Initialize a RpcAgent instance.

        Args:
            agent_class (`Type[AgentBase]`, defaults to `None`):
                The AgentBase subclass encapsulated by this wrapper.
            agent_configs (`dict`): The args used to initialize the
                agent_class.
            name (`str`): Name of the agent.
            host (`str`, defaults to `"localhost"`):
                Hostname of the rpc agent server.
            port (`int`, defaults to `None`):
                Port of the rpc agent server.
            max_pool_size (`int`, defaults to `100`):
                Max number of task results that the server can accommodate.
            max_timeout_seconds (`int`, defaults to `1800`):
                Timeout for task results.
            local_mode (`bool`, defaults to `True`):
                Whether the started rpc server only listens to local
                requests.
            lazy_launch (`bool`, defaults to `True`):
                Only launch the server when the agent is called.
        """
        super().__init__(name=name)
        self.host = host
        self.port = port
        self.server_launcher = None
        self.client = None
        if launch_server:
            self.server_launcher = RpcAgentServerLauncher(
                agent_class=agent_class,
                agent_args=agent_configs["args"],
                agent_kwargs=agent_configs["kwargs"],
                host=host,
                port=port,
                max_pool_size=max_pool_size,
                max_timeout_seconds=max_timeout_seconds,
                local_mode=local_mode,
            )
            if not lazy_launch:
                self._launch_server()
        else:
            self.client = RpcAgentClient(host=self.host, port=self.port)

    def _launch_server(self) -> None:
        """Launch a rpc server and update the port and the client"""
        self.server_launcher.launch()
        self.port = self.server_launcher.port
        self.client = RpcAgentClient(host=self.host, port=self.port)

    def reply(self, x: dict = None) -> dict:
        if self.client is None:
            self._launch_server()
        res_msg = self.client.call_func(
            func_name="_call",
            value=x.serialize() if x is not None else "",
        )
        return PlaceholderMessage(
            **deserialize(res_msg),  # type: ignore [arg-type]
        )

    def observe(self, x: Union[dict, Sequence[dict]]) -> None:
        if self.client is None:
            self._launch_server()
        self.client.call_func(
            func_name="_observe",
            value=serialize(x),  # type: ignore [arg-type]
        )

    def stop(self) -> None:
        """Stop the RpcAgent and the launched rpc server."""
        if self.server_launcher is not None:
            self.server_launcher.shutdown()

    def __del__(self) -> None:
        if self.server_launcher is not None:
            self.server_launcher.shutdown()


def setup_rcp_agent_server(
    agent_class: Type[AgentBase],
    agent_args: tuple,
    agent_kwargs: dict,
    host: str,
    port: int,
    init_settings: dict = None,
    start_event: EventClass = None,
    stop_event: EventClass = None,
    pipe: int = None,
    local_mode: bool = True,
    max_pool_size: int = 100,
    max_timeout_seconds: int = 1800,
    max_workers: int = 4,
) -> None:
    """Setup gRPC server rpc agent.

    Args:
        agent_class (`Type[AgentBase]`):
            A subclass of AgentBase.
        agent_args (`tuple`): The args tuple used to initialize the
            agent_class.
        agent_kwargs (`dict`): The args dict used to initialize the
            agent_class.
        host (`str`, defaults to `"localhost"`):
            Hostname of the rpc agent server.
        port (`int`):
            The socket port monitored by grpc server.
        init_settings (`dict`, defaults to `None`):
            Init settings for agentscope.init.
        start_event (`EventClass`, defaults to `None`):
            An Event instance used to determine whether the child process
            has been started.
        stop_event (`EventClass`, defaults to `None`):
            The stop Event instance used to determine whether the child
            process has been stopped.
        pipe (`int`, defaults to `None`):
            A pipe instance used to pass the actual port of the server.
        local_mode (`bool`, defaults to `None`):
            Only listen to local requests.
        max_pool_size (`int`, defaults to `100`):
            Max number of task results that the server can accommodate.
        max_timeout_seconds (`int`, defaults to `1800`):
            Timeout for task results.
        max_workers (`int`, defaults to `4`):
            max worker number of grpc server.
    """

    if init_settings is not None:
        init_process(**init_settings)
    servicer = RpcServerSideWrapper(
        agent_class(*agent_args, **agent_kwargs),
        host=host,
        port=port,
        max_pool_size=max_pool_size,
        max_timeout_seconds=max_timeout_seconds,
    )
    while True:
        try:
            port = check_port(port)
            servicer.port = port
            logger.info(
                f"Starting rpc server [{agent_class.__name__}] at port"
                f" [{port}]...",
            )
            server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=max_workers),
            )
            add_RpcAgentServicer_to_server(servicer, server)
            if local_mode:
                server.add_insecure_port(f"localhost:{port}")
            else:
                server.add_insecure_port(f"0.0.0.0:{port}")
            server.start()
            break
        except OSError:
            logger.warning(
                f"Failed to start rpc server at port [{port}]"
                f"try another port",
            )
    logger.info(
        f"rpc server [{agent_class.__name__}] at port [{port}] started "
        "successfully",
    )
    if start_event is not None:
        pipe.send(port)
        start_event.set()
        stop_event.wait()
    else:
        server.wait_for_termination()
    logger.info(
        f"Stopping rpc server [{agent_class.__name__}] at port [{port}]",
    )
    server.stop(0)
    logger.info(
        f"rpc server [{agent_class.__name__}] at port [{port}] stopped "
        "successfully",
    )


def find_available_port() -> int:
    """Get an unoccupied socket port number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def check_port(port: Optional[int] = None) -> int:
    """Check if the port is available.

    Args:
        port (`int`):
            the port number being checked.

    Returns:
        `int`: the port number that passed the check. If the port is found
        to be occupied, an available port number will be automatically
        returned.
    """
    if port is None:
        new_port = find_available_port()
        logger.warning(
            "gRpc server port is not provided, automatically select "
            f"[{new_port}] as the port number.",
        )
        return new_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("localhost", port)) == 0:
            new_port = find_available_port()
            logger.warning(
                f"Port [{port}] is occupied, use [{new_port}] instead",
            )
            return new_port
    return port


class RpcAgentServerLauncher:
    """Launcher of rpc agent server."""

    def __init__(
        self,
        agent_class: Type[AgentBase] = None,
        agent_args: tuple = (),
        agent_kwargs: dict = None,
        host: str = "localhost",
        port: int = None,
        max_pool_size: int = 100,
        max_timeout_seconds: int = 1800,
        local_mode: bool = False,
    ) -> None:
        """Init a rpc agent server launcher.

        Args:
            agent_class (`Type[AgentBase]`, defaults to `None`):
                The AgentBase subclass encapsulated by this wrapper.
            agent_args (`tuple`): The args tuple used to initialize the
                agent_class.
            agent_kwargs (`dict`): The args dict used to initialize the
                agent_class.
            host (`str`, defaults to `"localhost"`):
                Hostname of the rpc agent server.
            port (`int`, defaults to `None`):
                Port of the rpc agent server.
            max_pool_size (`int`, defaults to `100`):
                Max number of task results that the server can accommodate.
            max_timeout_seconds (`int`, defaults to `1800`):
                Timeout for task results.
            local_mode (`bool`, defaults to `False`):
                Whether the started rpc server only listens to local
                requests.
        """
        self.agent_class = agent_class
        self.agent_args = agent_args
        self.agent_kwargs = agent_kwargs
        self.host = host
        self.port = check_port(port)
        self.max_pool_size = max_pool_size
        self.max_timeout_seconds = max_timeout_seconds
        self.local_mode = local_mode
        self.server = None
        self.stop_event = None
        self.parent_con = None

    def _launch_in_main(self) -> None:
        """Launch gRPC server in main-process"""
        server_thread = threading.Thread(
            target=setup_rcp_agent_server,
            kwargs={
                "agent_class": self.agent_class,
                "agent_args": self.agent_args,
                "agent_kwargs": self.agent_kwargs,
                "host": self.host,
                "port": self.port,
                "max_pool_size": self.max_pool_size,
                "max_timeout_seconds": self.max_timeout_seconds,
                "local_mode": self.local_mode,
            },
        )
        server_thread.start()
        logger.info(
            f"Launch [{self.agent_class.__name__}] server at "
            f"[{self.host}:{self.port}] success",
        )
        server_thread.join()

    def _launch_in_sub(self) -> None:
        """Launch gRPC server in sub-process."""
        self.stop_event = Event()
        self.parent_con, child_con = Pipe()
        start_event = Event()
        server_process = Process(
            target=setup_rcp_agent_server,
            kwargs={
                "agent_class": self.agent_class,
                "agent_args": self.agent_args,
                "agent_kwargs": self.agent_kwargs,
                "host": self.host,
                "port": self.port,
                "init_settings": _INIT_SETTINGS,
                "start_event": start_event,
                "stop_event": self.stop_event,
                "pipe": child_con,
                "max_pool_size": self.max_pool_size,
                "max_timeout_seconds": self.max_timeout_seconds,
                "local_mode": self.local_mode,
            },
        )
        server_process.start()
        self.port = self.parent_con.recv()
        start_event.wait()
        self.server = server_process
        logger.info(
            f"Launch [{self.agent_class.__name__}] server at "
            f"[{self.host}:{self.port}] success",
        )

    def launch(self, in_subprocess: bool = True) -> None:
        """launch a rpc agent server.

        Args:
            in_subprocess (bool, optional): launch the server in subprocess.
                Defaults to True. For agents that need to obtain command line
                input, such as UserAgent, please set this value to False.
        """
        if in_subprocess:
            self._launch_in_sub()
        else:
            self._launch_in_main()

    def wait_until_terminate(self) -> None:
        """Wait for server process"""
        if self.server is not None:
            self.server.join()

    def shutdown(self) -> None:
        """Shutdown the rpc agent server."""
        if self.server is not None:
            if self.stop_event is not None:
                self.stop_event.set()
                self.stop_event = None
            self.server.join(timeout=5)
            self.server.terminate()
            if self.server.is_alive():
                self.server.kill()
                logger.info(
                    f"Rpc server [{self.agent_class.__name__}] at port"
                    f" [{self.port}] is killed.",
                )
            self.server = None


class RpcServerSideWrapper(RpcAgentServicer):
    """A wrapper to extend an AgentBase into a gRPC Servicer."""

    def __init__(
        self,
        agent_instance: AgentBase,
        host: str = "localhost",
        port: int = None,
        max_pool_size: int = 100,
        max_timeout_seconds: int = 1800,
    ):
        """Init the service side wrapper.

        Args:
            agent_instance (`AgentBase`): an instance of `AgentBase`.
            host (`str`, defaults to "localhost"):
                Hostname of the rpc agent server.
            port (`int`, defaults to `None`):
                Port of the rpc agent server.
            max_pool_size (`int`, defaults to `100`):
                The max number of task results that the server can
                accommodate. Note that the oldest result will be deleted
                after exceeding the pool size.
            max_timeout_seconds (`int`, defaults to `1800`):
                Timeout for task results. Note that expired results will be
                deleted.
        """
        self.host = host
        self.port = port
        self.result_pool = ExpiringDict(
            max_len=max_pool_size,
            max_age_seconds=max_timeout_seconds,
        )
        self.task_queue = Queue()
        self.worker_thread = threading.Thread(target=self.process_tasks)
        self.worker_thread.start()
        self.task_id_lock = threading.Lock()
        self.task_id_counter = 0
        self.agent = agent_instance

    def get_task_id(self) -> int:
        """Get the auto-increment task id."""
        with self.task_id_lock:
            self.task_id_counter += 1
            return self.task_id_counter

    def call_func(self, request: RpcMsg, _: ServicerContext) -> RpcMsg:
        """Call the specific servicer function."""
        if hasattr(self, request.target_func):
            return getattr(self, request.target_func)(request)
        else:
            logger.error(f"Unsupported method {request.target_func}")
            return RpcMsg(
                value=Msg(
                    name=self.agent.name,
                    content=f"Unsupported method {request.target_func}",
                ).serialize(),
            )

    def _call(self, request: RpcMsg) -> RpcMsg:
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
        self.task_queue.put((task_id, msg))
        return RpcMsg(
            value=Msg(
                name=self.agent.name,
                content=None,
                host=self.host,
                port=self.port,
                task_id=task_id,
            ).serialize(),
        )

    def _get(self, request: RpcMsg) -> RpcMsg:
        """Get function of RpcAgentService

        Args:
            request (`RpcMsg`):
                Identifier of message, with json format::

                {
                    'task_id': int
                }

        Returns:
            `RpcMsg`: Concrete values of the specific message (or part of it).
        """
        # todo: add format specification of request
        msg = json.loads(request.value)
        # todo: implement the waiting in a more elegant way, add timeout
        while True:
            result = self.result_pool.get(msg["task_id"], None)
            if result is not None:
                return RpcMsg(value=result.serialize())
            time.sleep(0.1)

    def _observe(self, request: RpcMsg) -> RpcMsg:
        """Observe function of RpcAgentService

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
        self.agent.observe(msgs)
        return RpcMsg()

    def process_tasks(self) -> None:
        """Task processing thread."""
        while True:
            task_id, task_msg = self.task_queue.get()
            # TODO: optimize this and avoid blocking
            if isinstance(task_msg, PlaceholderMessage):
                task_msg.update_value()
            result = self.agent.reply(task_msg)
            self.result_pool[task_id] = result
