# -*- coding: utf-8 -*-
""" Server of distributed agent"""
import os
import asyncio
import signal
import argparse
import time
from multiprocessing import Process, Event, Pipe
from multiprocessing.synchronize import Event as EventClass
from typing import Type
from concurrent import futures
from loguru import logger

try:
    import grpc
    from agentscope.rpc.rpc_agent_pb2_grpc import (
        add_RpcAgentServicer_to_server,
    )
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    grpc = ImportErrorReporter(import_error, "distribute")
    add_RpcAgentServicer_to_server = ImportErrorReporter(
        import_error,
        "distribute",
    )
import agentscope
from agentscope.server.servicer import AgentServerServicer
from agentscope.agents.agent import AgentBase
from agentscope.utils.tools import check_port, generate_id_from_seed


def _setup_agent_server(
    host: str,
    port: int,
    server_id: str,
    init_settings: dict = None,
    start_event: EventClass = None,
    stop_event: EventClass = None,
    pipe: int = None,
    local_mode: bool = True,
    max_pool_size: int = 8192,
    max_timeout_seconds: int = 1800,
    studio_url: str = None,
    custom_agents: list = None,
) -> None:
    """Setup agent server.

    Args:
        host (`str`, defaults to `"localhost"`):
            Hostname of the agent server.
        port (`int`):
            The socket port monitored by the agent server.
        server_id (`str`):
            The id of the server.
        init_settings (`dict`, defaults to `None`):
            Init settings for _init_server.
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
        max_pool_size (`int`, defaults to `8192`):
            Max number of agent replies that the server can accommodate.
        max_timeout_seconds (`int`, defaults to `1800`):
            Timeout for agent replies.
        studio_url (`str`, defaults to `None`):
            URL of the AgentScope Studio.
        custom_agents (`list`, defaults to `None`):
            A list of custom agent classes that are not in `agentscope.agents`.
    """
    asyncio.run(
        _setup_agent_server_async(
            host=host,
            port=port,
            server_id=server_id,
            init_settings=init_settings,
            start_event=start_event,
            stop_event=stop_event,
            pipe=pipe,
            local_mode=local_mode,
            max_pool_size=max_pool_size,
            max_timeout_seconds=max_timeout_seconds,
            studio_url=studio_url,
            custom_agents=custom_agents,
        ),
    )


async def _setup_agent_server_async(
    host: str,
    port: int,
    server_id: str,
    init_settings: dict = None,
    start_event: EventClass = None,
    stop_event: EventClass = None,
    pipe: int = None,
    local_mode: bool = True,
    max_pool_size: int = 8192,
    max_timeout_seconds: int = 1800,
    studio_url: str = None,
    custom_agents: list = None,
) -> None:
    """Setup agent server in an async way.

    Args:
        host (`str`, defaults to `"localhost"`):
            Hostname of the agent server.
        port (`int`):
            The socket port monitored by the agent server.
        server_id (`str`):
            The id of the server.
        init_settings (`dict`, defaults to `None`):
            Init settings for _init_server.
        start_event (`EventClass`, defaults to `None`):
            An Event instance used to determine whether the child process
            has been started.
        stop_event (`EventClass`, defaults to `None`):
            The stop Event instance used to determine whether the child
            process has been stopped.
        pipe (`int`, defaults to `None`):
            A pipe instance used to pass the actual port of the server.
        local_mode (`bool`, defaults to `None`):
            If `True`, only listen to requests from "localhost", otherwise,
            listen to requests from all hosts.
        max_pool_size (`int`, defaults to `8192`):
            The max number of agent reply messages that the server can
            accommodate. Note that the oldest message will be deleted
            after exceeding the pool size.
        max_timeout_seconds (`int`, defaults to `1800`):
            Maximum time for reply messages to be cached in the server.
            Note that expired messages will be deleted.
        studio_url (`str`, defaults to `None`):
            URL of the AgentScope Studio.
        custom_agents (`list`, defaults to `None`):
            A list of custom agent classes that are not in `agentscope.agents`.
    """
    from agentscope._init import init_process

    if init_settings is not None:
        init_process(**init_settings)
    servicer = AgentServerServicer(
        host=host,
        port=port,
        server_id=server_id,
        studio_url=studio_url,
        max_pool_size=max_pool_size,
        max_timeout_seconds=max_timeout_seconds,
    )
    # update agent registry
    if custom_agents is not None:
        for agent_class in custom_agents:
            AgentBase.register_agent_class(agent_class=agent_class)

    async def shutdown_signal_handler() -> None:
        logger.info(
            f"Received shutdown signal. Gracefully stopping the server at "
            f"[{host}:{port}].",
        )
        await server.stop(grace=5)

    loop = asyncio.get_running_loop()
    if os.name != "nt":
        # windows does not support add_signal_handler
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(shutdown_signal_handler()),
            )
    while True:
        try:
            port = check_port(port)
            servicer.port = port
            server = grpc.aio.server(
                futures.ThreadPoolExecutor(max_workers=None),
            )
            add_RpcAgentServicer_to_server(servicer, server)
            if local_mode:
                server.add_insecure_port(f"localhost:{port}")
            else:
                server.add_insecure_port(f"0.0.0.0:{port}")
            await server.start()
            break
        except OSError:
            logger.warning(
                f"Failed to start agent server at port [{port}]"
                f"try another port",
            )
    logger.info(
        f"agent server [{server_id}] at {host}:{port} started successfully",
    )
    if start_event is not None:
        pipe.send(port)
        start_event.set()
        while not stop_event.is_set():
            await asyncio.sleep(1)
        logger.info(
            f"Stopping agent server at [{host}:{port}]",
        )
        await server.stop(grace=10.0)
    else:
        await server.wait_for_termination()
    logger.info(
        f"agent server [{server_id}] at {host}:{port} stopped successfully",
    )


class RpcAgentServerLauncher:
    """The launcher of AgentServer."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = None,
        max_pool_size: int = 8192,
        max_timeout_seconds: int = 1800,
        local_mode: bool = False,
        custom_agents: list = None,
        server_id: str = None,
        studio_url: str = None,
        agent_class: Type[AgentBase] = None,
        agent_args: tuple = (),
        agent_kwargs: dict = None,
    ) -> None:
        """Init a launcher of agent server.

        Args:
            host (`str`, defaults to `"localhost"`):
                Hostname of the agent server.
            port (`int`, defaults to `None`):
                Socket port of the agent server.
            max_pool_size (`int`, defaults to `8192`):
                The max number of agent reply messages that the server can
                accommodate. Note that the oldest message will be deleted
                after exceeding the pool size.
            max_timeout_seconds (`int`, defaults to `1800`):
                Maximum time for reply messages to be cached in the server.
                Note that expired messages will be deleted.
            local_mode (`bool`, defaults to `False`):
                If `True`, only listen to requests from "localhost", otherwise,
                listen to requests from all hosts.
            custom_agents (`list`, defaults to `None`):
                A list of custom agent classes that are not in
                `agentscope.agents`.
            server_id (`str`, defaults to `None`):
                The id of the agent server. If not specified, a random id
                will be generated.
            studio_url (`Optional[str]`, defaults to `None`):
                The url of the agentscope studio.
            agent_class (`Type[AgentBase]`, deprecated):
                The AgentBase subclass encapsulated by this wrapper.
            agent_args (`tuple`, deprecated): The args tuple used to
                initialize the agent_class.
            agent_kwargs (`dict`, deprecated): The args dict used to
                initialize the agent_class.
        """
        self.host = host
        self.port = check_port(port)
        self.max_pool_size = max_pool_size
        self.max_timeout_seconds = max_timeout_seconds
        self.local_mode = local_mode
        self.server = None
        self.stop_event = None
        self.parent_con = None
        self.custom_agents = custom_agents
        self.server_id = (
            RpcAgentServerLauncher.generate_server_id(self.host, self.port)
            if server_id is None
            else server_id
        )
        self.studio_url = studio_url
        if (
            agent_class is not None
            or len(agent_args) > 0
            or agent_kwargs is not None
        ):
            logger.warning(
                "`agent_class`, `agent_args` and `agent_kwargs` is deprecated"
                " in `RpcAgentServerLauncher`",
            )

    @classmethod
    def generate_server_id(cls, host: str, port: int) -> str:
        """Generate server id"""
        return generate_id_from_seed(f"{host}:{port}:{time.time()}", length=8)

    def _launch_in_main(self) -> None:
        """Launch agent server in main-process"""
        logger.info(
            f"Launching agent server at [{self.host}:{self.port}]...",
        )
        asyncio.run(
            _setup_agent_server_async(
                host=self.host,
                port=self.port,
                server_id=self.server_id,
                max_pool_size=self.max_pool_size,
                max_timeout_seconds=self.max_timeout_seconds,
                local_mode=self.local_mode,
                custom_agents=self.custom_agents,
                studio_url=self.studio_url,
            ),
        )

    def _launch_in_sub(self) -> None:
        """Launch an agent server in sub-process."""
        from agentscope._init import _INIT_SETTINGS

        self.stop_event = Event()
        self.parent_con, child_con = Pipe()
        start_event = Event()
        server_process = Process(
            target=_setup_agent_server,
            kwargs={
                "host": self.host,
                "port": self.port,
                "server_id": self.server_id,
                "init_settings": _INIT_SETTINGS,
                "start_event": start_event,
                "stop_event": self.stop_event,
                "pipe": child_con,
                "max_pool_size": self.max_pool_size,
                "max_timeout_seconds": self.max_timeout_seconds,
                "local_mode": self.local_mode,
                "studio_url": self.studio_url,
                "custom_agents": self.custom_agents,
            },
        )
        server_process.start()
        self.port = self.parent_con.recv()
        start_event.wait()
        self.server = server_process
        logger.info(
            f"Launch agent server at [{self.host}:{self.port}] success",
        )

    def launch(self, in_subprocess: bool = True) -> None:
        """launch an agent server.

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
        """Shutdown the agent server."""
        if self.server is not None:
            if self.stop_event is not None:
                self.stop_event.set()
                self.stop_event = None
            self.server.join()
            if self.server.is_alive():
                self.server.kill()
                logger.info(
                    f"Agent server at port [{self.port}] is killed.",
                )
            self.server = None


def as_server() -> None:
    """Launch an agent server with terminal command.

    Note:

        The arguments of `as_server` are listed as follows:

        * `--host`: the hostname of the server.
        * `--port`: the socket port of the server.
        * `--max-pool-size`: max number of agent reply messages that the server
          can accommodate. Note that the oldest message will be deleted
          after exceeding the pool size.
        * `--max-timeout-seconds`: max time for reply messages to be cached
          in the server. Note that expired messages will be deleted.
        * `--local-mode`: whether the started agent server only listens to
          local requests.
        * `--model-config-path`: the path to the model config json file

        In most cases, you only need to specify the `--host`, `--port` and
        `--model-config-path`.

        .. code-block:: shell

            as_server --host localhost --port 12345 --model-config-path config.json

    """  # noqa
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="hostname of the server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=12310,
        help="socket port of the server",
    )
    parser.add_argument(
        "--max-pool-size",
        type=int,
        default=8192,
        help=(
            "max number of agent reply messages that the server "
            "can accommodate. Note that the oldest message will be deleted "
            "after exceeding the pool size."
        ),
    )
    parser.add_argument(
        "--max-timeout-seconds",
        type=int,
        default=1800,
        help=(
            "max time for agent reply messages to be cached"
            "in the server. Note that expired messages will be deleted."
        ),
    )
    parser.add_argument(
        "--local-mode",
        type=bool,
        default=False,
        help=(
            "if `True`, only listen to requests from 'localhost', otherwise, "
            "listen to requests from all hosts."
        ),
    )
    parser.add_argument(
        "--model-config-path",
        type=str,
        help="path to the model config json file",
    )
    parser.add_argument(
        "--server-id",
        type=str,
        default=None,
        help="id of the server, used to register to the studio, generated"
        " randomly if not specified.",
    )
    parser.add_argument(
        "--studio-url",
        type=str,
        default=None,
        help="the url of agentscope studio",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="whether to disable log",
    )
    parser.add_argument(
        "--save-api-invoke",
        action="store_true",
        help="whether to save api invoke",
    )
    parser.add_argument(
        "--use-monitor",
        action="store_true",
        help="whether to use monitor",
    )
    args = parser.parse_args()
    agentscope.init(
        project="agent_server",
        name=f"server_{args.host}:{args.port}",
        save_log=not args.no_log,
        save_api_invoke=args.save_api_invoke,
        model_configs=args.model_config_path,
        use_monitor=args.use_monitor,
    )
    launcher = RpcAgentServerLauncher(
        host=args.host,
        port=args.port,
        server_id=args.server_id,
        max_pool_size=args.max_pool_size,
        max_timeout_seconds=args.max_timeout_seconds,
        local_mode=args.local_mode,
        studio_url=args.studio_url,
    )
    launcher.launch(in_subprocess=False)
    launcher.wait_until_terminate()
