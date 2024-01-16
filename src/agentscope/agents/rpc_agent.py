# -*- coding: utf-8 -*-
""" Base class for Rpc Agent """

from multiprocessing import Process
from multiprocessing import Event
from multiprocessing.synchronize import Event as EventClass
import socket
import threading
import time
import json
from queue import Queue
from typing import Any
from typing import Callable
from typing import Optional
from typing import Union
from typing import Type
from typing import Sequence
from concurrent import futures

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

from agentscope._init import _INIT_SETTINGS
from agentscope._init import init
from agentscope.agents.agent import AgentBase
from agentscope.rpc.rpc_agent_pb2 import RpcMsg  # pylint: disable=E0611
from agentscope.message import MessageBase
from agentscope.message import Msg
from agentscope.message import PlaceholderMessage
from agentscope.message import deserialize
from agentscope.message import serialize
from agentscope.utils.logging_utils import logger
from agentscope.rpc.rpc_agent_client import RpcAgentClient
from agentscope.rpc.rpc_agent_pb2_grpc import (
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


class RpcAgentBase(AgentBase, RpcAgentServicer):
    """Abstract service of RpcAgent, also act as AgentBase.

    Note:
        Please implement reply method based on the functionality of your
        agent.
    """

    def __init__(
        self,
        name: str,
        config: Optional[dict] = None,
        sys_prompt: Optional[str] = None,
        model: Optional[Union[Callable[..., Any], str]] = None,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
        host: str = "localhost",
        port: int = 80,
        max_pool_size: int = 100,
        max_timeout_seconds: int = 1800,
        launch_server: bool = True,
        local_mode: bool = True,
        lazy_launch: bool = True,
        is_servicer: bool = False,
    ) -> None:
        """Init a RpcAgentBase instance.

        Args:
            name (`str`):
                The name of the agent.
            config (`Optional[dict]`):
                The configuration of the agent, if provided, the agent will
                be initialized from the config rather than the other
                parameters.
            sys_prompt (`Optional[str]`):
                The system prompt of the agent, which can be passed by args
                or hard-coded in the agent.
            model (`Optional[Union[Callable[..., Any], str]]`, defaults to
            None):
                The callable model object or the model name, which is used to
                load model from configuration.
            use_memory (`bool`, defaults to `True`):
                Whether the agent has memory.
            memory_config (`Optional[dict]`):
                The config of memory.
            host (`str`, defaults to "localhost"):
                Hostname of the rpc agent server.
            port (`int`, defaults to `80`):
                Port of the rpc agent server.
            max_pool_size (`int`, defaults to `100`):
                The max number of task results that the server can
                accommodate. Note that the oldest result will be deleted
                after exceeding the pool size.
            max_timeout_seconds (`int`, defaults to `1800`):
                Timeout for task results. Note that expired results will be
                deleted.
            launch_server (`bool`, defaults to `True`):
                Launch a rpc server locally.
            local_mode (`bool`, defaults to `True`):
                The started server only listens to local requests.
            lazy_launch (`bool`, defaults to `True`):
                Only launch the server when the agent is called.
            is_servicer (`bool`, defaults to `False`):
                Used as a servicer of rpc server.
        """
        super().__init__(
            name,
            config,
            sys_prompt,
            model,
            use_memory,
            memory_config,
        )
        self.host = host
        self.port = port
        self.is_servicer = is_servicer

        # prohibit servicer object from launching a new server
        assert not (is_servicer and launch_server)
        # launch_server is True only in the main process
        if launch_server:
            self.server_launcher = RpcAgentServerLauncher(
                name=name,
                config=config,
                sys_prompt=sys_prompt,
                model=model,
                use_memory=use_memory,
                memory_config=memory_config,
                agent_class=self.__class__,
                host=host,
                port=port,
                max_pool_size=max_pool_size,
                max_timeout_seconds=max_timeout_seconds,
                local_mode=local_mode,
            )
            self.port = self.server_launcher.port
            self.client = None
            if not lazy_launch:
                self.server_launcher.launch()
                self.client = RpcAgentClient(host=self.host, port=self.port)
        else:
            self.server_launcher = None
        # is_servicer is True only in the rpc server process
        if is_servicer:
            self.result_pool = ExpiringDict(
                max_len=max_pool_size,
                max_age_seconds=max_timeout_seconds,
            )
            self.task_queue = Queue()
            self.worker_thread = threading.Thread(target=self.process_tasks)
            self.worker_thread.start()
            self.task_id_lock = threading.Lock()
            self.task_id_counter = 0

        # connect to an existing rpc server
        if not launch_server and not is_servicer:
            self.client = RpcAgentClient(host=self.host, port=self.port)

    def get_task_id(self) -> int:
        """Get the auto-increment task id."""
        with self.task_id_lock:
            self.task_id_counter += 1
            return self.task_id_counter

    def call_func(self, request: RpcMsg, _: ServicerContext) -> RpcMsg:
        if hasattr(self, request.target_func):
            return getattr(self, request.target_func)(request)
        else:
            logger.error(f"Unsupported method {request.target_func}")
            return RpcMsg(
                value=Msg(
                    name=self.name,
                    content=f"Unsupported method {request.target_func}",
                ).serialize(),
            )

    @rpc_servicer_method
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
                name=self.name,
                content=None,
                host=self.host,
                port=self.port,
                task_id=task_id,
            ).serialize(),
        )

    @rpc_servicer_method
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

    @rpc_servicer_method
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
        self.memory.add(msgs)
        return RpcMsg()

    def process_tasks(self) -> None:
        """Task processing thread."""
        while True:
            task_id, task_msg = self.task_queue.get()
            result = self.reply(task_msg)
            self.result_pool[task_id] = result

    def reply(self, x: dict = None) -> dict:
        """Reply function used in the rpc agent server process."""
        raise NotImplementedError(
            f"Agent [{type(self).__name__}] is missing the required "
            f'"reply" function.',
        )

    def observe(self, x: Union[dict, Sequence[dict]]) -> None:
        """Observe the input, store it in memory and don't response to it.

        Args:
            x (`Union[dict, Sequence[dict]]`):
                The input to be observed.
        """
        self.client.call_func(
            func_name="_observe",
            value=serialize(x),  # type: ignore [arg-type]
        )

    def __call__(self, *args: Any, **kwargs: Any) -> dict:
        """Call function used in the main process."""
        if args is not None and len(args) > 0:
            x = args[0]
        elif kwargs is not None and len(kwargs) > 0:
            x = kwargs["x"]
        else:
            x = None
        if x is not None:
            assert isinstance(x, MessageBase)
        if self.client is None:
            self.server_launcher.launch()
            self.client = RpcAgentClient(host=self.host, port=self.port)
        res_msg = self.client.call_func(
            func_name="_call",
            value=x.serialize() if x is not None else "",
        )
        res = PlaceholderMessage(
            **deserialize(res_msg),  # type: ignore [arg-type]
        )
        if self._audience is not None:
            self._broadcast_to_audience(res)
        return res

    def stop(self) -> None:
        """Stop the RpcAgent and the launched rpc server."""
        if self.server_launcher is not None:
            self.server_launcher.shutdown()

    def __del__(self) -> None:
        if self.server_launcher is not None:
            self.server_launcher.shutdown()


def setup_rcp_agent_server(
    port: int,
    servicer_class: Type[RpcAgentServicer],
    start_event: EventClass = None,
    stop_event: EventClass = None,
    max_workers: int = 4,
    local_mode: bool = True,
    init_settings: dict = None,
    kwargs: dict = None,
) -> None:
    """Setup gRPC server rpc agent.

    Args:
        port (`int`):
            The socket port monitored by grpc server.
        servicer_class (`Type[RpcAgentServicer]`):
            An implementation of RpcAgentBaseService.
        start_event (`EventClass`, defaults to `None`):
            An Event instance used to determine whether the child process
            has been started.
        stop_event (`EventClass`, defaults to `None`):
            The stop Event instance used to determine whether the child
            process has been stopped.
        max_workers (`int`, defaults to `4`):
            max worker number of grpc server.
        local_mode (`bool`, defaults to `None`):
            Only listen to local requests.
        init_settings (`dict`, defaults to `None`):
            Init settings.
    """

    if init_settings is not None:
        init(**init_settings)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    servicer = servicer_class(**kwargs)
    add_RpcAgentServicer_to_server(servicer, server)
    if local_mode:
        server.add_insecure_port(f"localhost:{port}")
    else:
        server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    logger.info(
        f"rpc server [{servicer_class.__name__}] at port [{port}] started "
        "successfully",
    )
    start_event.set()
    stop_event.wait()
    logger.info(
        f"Stopping rpc server [{servicer_class.__name__}] at port [{port}]",
    )
    server.stop(0)
    logger.info(
        f"rpc server [{servicer_class.__name__}] at port [{port}] stopped "
        "successfully",
    )


class RpcAgentServerLauncher:
    """Launcher of rpc agent server."""

    def __init__(
        self,
        name: str,
        config: Optional[dict] = None,
        sys_prompt: Optional[str] = None,
        model: Optional[Union[Callable[..., Any], str]] = None,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
        agent_class: Type[RpcAgentBase] = None,
        host: str = "localhost",
        port: int = None,
        max_pool_size: int = 100,
        max_timeout_seconds: int = 1800,
        local_mode: bool = True,
        **kwargs: Any,
    ) -> None:
        """Init a rpc agent server launcher.

        Args:
            name (`str`):
                The name of the agent.
            config (`Optional[dict]`):
                The configuration of the agent, if provided, the agent will
                be initialized from the config rather than the other
                parameters.
            sys_prompt (`Optional[str]`):
                The system prompt of the agent, which can be passed by args
                or hard-coded in the agent.
            model (`Optional[Union[Callable[..., Any], str]]`, defaults to
            None):
                The callable model object or the model name, which is used to
                load model from configuration.
            use_memory (`bool`, defaults to `True`):
                Whether the agent has memory.
            memory_config (`Optional[dict]`):
                The config of memory.
            agent_class (`Type[RpcAgentBase]`, defaults to `None`):
                The RpcAgentBase class used in rpc agent server as a servicer.
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
        """
        self.name = name
        self.config = config
        self.sys_prompt = sys_prompt
        self.model = model
        self.use_memory = use_memory
        self.memory_config = memory_config
        self.agent_class = agent_class
        self.host = host
        self.port = self.check_port(port)
        self.max_pool_size = max_pool_size
        self.max_timeout_seconds = max_timeout_seconds
        self.local_model = local_mode
        self.server = None
        self.stop_event = None
        self.kwargs = kwargs

    def find_available_port(self) -> int:
        """Get an unoccupied socket port number."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def check_port(self, port: int) -> int:
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
            new_port = self.find_available_port()
            logger.warning(
                "gRpc server port is not provided, automatically select "
                f"[{new_port}] as the port number.",
            )
            return new_port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) == 0:
                new_port = self.find_available_port()
                logger.warning(
                    f"Port [{port}] is occupied, use [{new_port}] instead",
                )
                return new_port
        return port

    def launch(self) -> None:
        """launch a local rpc agent server."""
        self.stop_event = Event()
        logger.info(
            f"Starting rpc server [{self.agent_class.__name__}] at port"
            f" [{self.port}]...",
        )
        start_event = Event()
        server_process = Process(
            target=setup_rcp_agent_server,
            kwargs={
                "port": self.port,
                "servicer_class": self.agent_class,
                "start_event": start_event,
                "stop_event": self.stop_event,
                "local_mode": self.local_model,
                "init_settings": _INIT_SETTINGS,
                "kwargs": {
                    "name": self.name,
                    "config": self.config,
                    "sys_prompt": self.sys_prompt,
                    "model": self.model,
                    "use_memory": self.use_memory,
                    "memory_config": self.memory_config,
                    "host": self.host,
                    "port": self.port,
                    "max_pool_size": self.max_pool_size,
                    "max_timeout_seconds": self.max_timeout_seconds,
                    "launch_server": False,
                    "lazy_launch": False,
                    "is_servicer": True,
                    **self.kwargs,
                },
            },
        )
        server_process.start()
        start_event.wait()
        self.server = server_process

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
            self.server.terminate()
            self.server.join(timeout=5)
            if self.server.is_alive():
                self.server.kill()
                logger.info(
                    f"Rpc server [{self.agent_class.__name__}] at port"
                    f" [{self.port}] is killed.",
                )
            self.server = None
