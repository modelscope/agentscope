# -*- coding: utf-8 -*-
"""Async related modules."""
from typing import Any
from concurrent.futures import Future
from loguru import logger

try:
    import cloudpickle as pickle
except ImportError as import_error:
    from agentscope.utils.common import ImportErrorReporter

    pickle = ImportErrorReporter(import_error, "distribtue")

from ..message import Msg
from .rpc_client import RpcClient
from ..utils.common import _is_web_url
from .retry_strategy import RetryBase, _DEAFULT_RETRY_STRATEGY


class AsyncResult:
    """Use this class to get the the async result from rpc server."""

    def __init__(
        self,
        host: str,
        port: int,
        task_id: int = None,
        stub: Future = None,
        retry: RetryBase = _DEAFULT_RETRY_STRATEGY,
    ) -> None:
        self._host = host
        self._port = port
        self._stub = None
        self._retry = retry
        self._task_id: int = None
        if task_id is not None:
            self._task_id = task_id
        else:
            self._stub = stub
        self._ready = False
        self._data = None

    def _fetch_result(
        self,
    ) -> None:
        """Fetch result from the server."""
        if self._task_id is None:
            self._task_id = self._get_task_id()
        self._data = pickle.loads(
            RpcClient(self._host, self._port).update_result(
                self._task_id,
                retry=self._retry,
            ),
        )
        # NOTE: its a hack here to download files
        # TODO: opt this
        self._check_and_download_files()
        self._ready = True

    def update_value(self) -> None:
        """Update the value. For compatibility with old version."""
        self._fetch_result()

    def _get_task_id(self) -> str:
        """get the task_id."""
        try:
            return self._stub.result()
        except Exception as e:
            logger.error(
                f"Failed to get task_id: {self._stub.result()}",
            )
            raise ValueError(
                f"Failed to get task_id: {self._stub.result()}",
            ) from e

    def _download(self, url: str) -> str:
        if not _is_web_url(url):
            client = RpcClient(self._host, self._port)
            return client.download_file(path=url)
        else:
            return url

    def _check_and_download_files(self) -> None:
        """Check whether the urls are accessible. If not, download them
        from rpc server."""
        if isinstance(self._data, Msg) and self._data.url:
            checked_urls = []
            if isinstance(self._data.url, str):
                self._data.url = self._download(self._data.url)
            else:
                checked_urls = []
                for url in self._data.url:
                    checked_urls.append(self._download(url))
                self._data.url = checked_urls

    def result(self) -> Any:
        """Get the result."""
        if not self._ready:
            self._fetch_result()
        return self._data

    def __getattr__(self, attr: str) -> Any:
        if not self._ready:
            self._fetch_result()

        return getattr(self._data, attr)

    def __getitem__(self, item: str) -> Any:
        if not self._ready:
            self._fetch_result()

        return self._data[item]  # type: ignore[index]

    def __reduce__(self) -> tuple:
        if self._task_id is None:
            self._task_id = self._get_task_id()
        if not self._ready:
            return (
                AsyncResult,
                (self._host, self._port, self._task_id),
            )
        else:
            return self._data.__reduce__()  # type: ignore[return-value]
