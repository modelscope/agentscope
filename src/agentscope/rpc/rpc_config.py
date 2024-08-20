# -*- coding: utf-8 -*-
"""Configs for Distributed mode."""
from typing import Callable, Any
from concurrent.futures import Future
from loguru import logger

try:
    import cloudpickle as pickle
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    pickle = ImportErrorReporter(import_error, "distribtue")

from .rpc_agent_client import RpcAgentClient
from ..utils.tools import is_web_accessible


def async_func(func: Callable) -> Callable:
    """A decorator for async function.
    In distributed mode, async functions will return a placeholder message
    immediately.

    Args:
        func (`Callable`): The function to decorate.
    """

    func._is_async = True  # pylint: disable=W0212
    return func


class AsyncResult:
    """Use this class to get the the async result from rpc server."""

    def __init__(
        self,
        host: str,
        port: int,
        task_id: int = None,
        stub: Future = None,
    ) -> None:
        self.host = host
        self.port = port
        self.stub = None
        self.task_id: int = None
        if task_id is not None:
            self.task_id = task_id
        else:
            self.stub = stub

    def get_task_id(self) -> str:
        """get the task_id."""
        try:
            return pickle.loads(self.stub.result())
        except Exception as e:
            logger.error(
                f"Failed to get task_id: {self.stub.result()}",
            )
            raise ValueError(
                f"Failed to get task_id: {self.stub.result()}",
            ) from e

    def get(self) -> Any:
        """Get the value"""
        if self.task_id is None:
            self.task_id = self.get_task_id()
        return pickle.loads(
            RpcAgentClient(self.host, self.port).update_placeholder(
                self.task_id,
            ),
        )

    def check_and_download_files(self, urls: list[str]) -> list[str]:
        """Check whether the urls are accessible. If not, download them
        from rpc server."""
        checked_urls = []
        for url in urls:
            if not is_web_accessible(url):
                # TODO: download in sub-threads
                client = RpcAgentClient(self.host, self.port)
                checked_urls.append(client.download_file(path=url))
            else:
                checked_urls.append(url)
        return checked_urls

    def __getstate__(self) -> dict:
        if self.task_id is None:
            self.task_id = self.get_task_id()
        return {
            "host": self.host,
            "port": self.port,
            "task_id": self.task_id,
            "stub": None,
        }

    def __setstate__(self, state: dict) -> None:
        self.host = state["host"]
        self.port = state["port"]
        self.task_id = state["task_id"]
        self.stub = None


class DistConf(dict):
    """Distribution configuration for agents."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = None,
        max_pool_size: int = 8192,
        max_timeout_seconds: int = 7200,
        local_mode: bool = True,
        lazy_launch: bool = False,
    ):
        """Init the distributed configuration.

        Args:
            host (`str`, defaults to `"localhost"`):
                Hostname of the rpc agent server.
            port (`int`, defaults to `None`):
                Port of the rpc agent server.
            max_pool_size (`int`, defaults to `8192`):
                Max number of task results that the server can accommodate.
            max_timeout_seconds (`int`, defaults to `7200`):
                Timeout for task results.
            local_mode (`bool`, defaults to `True`):
                Whether the started rpc server only listens to local
                requests.
            lazy_launch (`bool`, defaults to `False`):
                Deprecated.
        """
        self["host"] = host
        self["port"] = port
        self["max_pool_size"] = max_pool_size
        self["max_timeout_seconds"] = max_timeout_seconds
        self["local_mode"] = local_mode
        if lazy_launch:
            logger.warning("lazy_launch is deprecated.")
