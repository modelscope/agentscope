# -*- coding: utf-8 -*-
"""A pool used to store the async result."""
import threading
import time
from abc import ABC, abstractmethod

try:
    import redis
    import expiringdict
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    redis = ImportErrorReporter(import_error, "distribute")


class AsyncResultPool(ABC):
    """Interface of Async Result Pool, used to store async results."""

    @abstractmethod
    def prepare(self) -> int:
        """Prepare a slot for the async result.

        Returns:
            `int`: The key of the async result.
        """

    @abstractmethod
    def set(self, key: int, value: bytes) -> None:
        """Set a value to the pool.

        Args:
            key (`int`): The key of the value.
            value (`bytes`): The value to be set.
        """

    @abstractmethod
    def get(self, key: int) -> bytes:
        """Get a value from the pool.

        Args:
            key (`int`): The key of the value

        Returns:
            `bytes`: The value
        """


class LocalPool(AsyncResultPool):
    """Local pool for storing results."""

    def __init__(self, max_len: int, max_timeout: int) -> None:
        self.pool = expiringdict.ExpiringDict(
            max_len=max_len,
            max_age_seconds=max_timeout,
        )
        self.object_id_cnt = 0
        self.object_id_lock = threading.Lock()

    def _get_object_id(self) -> int:
        with self.object_id_lock:
            self.object_id_cnt += 1
            return self.object_id_cnt

    def prepare(self) -> int:
        oid = self._get_object_id()
        self.pool[oid] = threading.Condition()
        return oid

    def set(self, key: int, value: bytes) -> None:
        cond = self.pool[key]
        self.pool[key] = value
        with cond:
            cond.notify_all()

    def get(self, key: int) -> bytes:
        while True:
            value = self.pool.get(key)
            if isinstance(value, threading.Condition):
                with value:
                    value.wait(timeout=1)
            else:
                break
        return value


class RedisPool(AsyncResultPool):
    """Redis pool for storing results."""

    def __init__(
        self,
        host: str,
        port: int,
        max_timeout: int,
    ) -> None:
        """
        Init redis pool.

        Args:
            host (`str`): The host of the redis server.
            port (`int`): The port of the redis server.
            max_timeout (`int`): The max timeout of the result in the pool,
            when it is reached, the oldest item will be removed.
        """
        self.pool = redis.Redis(host=host, port=port, db=0)
        self.max_timeout = max_timeout

    def _get_object_id(self) -> int:
        return self.pool.incr("global_object_id")

    def prepare(self) -> int:
        return self._get_object_id()

    def set(self, key: int, value: bytes) -> None:
        self.pool.set(key, value, ex=self.max_timeout)

    def get(self, key: int) -> bytes:
        while True:
            result = self.pool.get(key)
            if result:
                return result
            time.sleep(0.01)


def get_pool(
    pool_type: str = "local",
    max_timeout: int = 7200,
    max_len: int = 8192,
    host: str = "localhost",
    port: int = 6379,
) -> AsyncResultPool:
    """Get the pool according to the type.

    Args:
        pool_type (`str`): The type of the pool, can be `local` or `redis`,
            default is `local`.
        max_timeout (`int`): The max timeout of the result in the pool,
            when it is reached, the oldest item will be removed.
        max_len (`int`): The max length of the pool.
        host (`str`): The host of the redis server.
        port (`int`): The port of the redis server.
    """
    if pool_type == "redis":
        return RedisPool(host=host, port=port, max_timeout=max_timeout)
    else:
        return LocalPool(max_len=max_len, max_timeout=max_timeout)
