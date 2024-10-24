# -*- coding: utf-8 -*-
"""Test the async result pool."""
import unittest
import time
import pickle

from loguru import logger

from agentscope.rpc.rpc_object import _call_func_in_thread
from agentscope.server.async_result_pool import (
    AsyncResultPool,
    get_pool,
)


def test_set_func(oid: int, value: int, pool: AsyncResultPool) -> None:
    """A test function which set value to the pool"""
    time.sleep(2)
    pool.set(oid, pickle.dumps(value))


def test_get_func(oid: int, pool: AsyncResultPool) -> tuple:
    """A test function which get value from the pool"""
    st = time.time()
    value = pickle.loads(pool.get(oid))
    et = time.time()
    return value, et - st


class BasicResultPoolTest(unittest.TestCase):
    """Test cases for Result Pool"""

    def _test_result_pool(self, pool: AsyncResultPool) -> None:
        get_stubs = []
        set_stubs = []
        st = time.time()
        for target_value in range(10):
            oid = pool.prepare()
            get_stubs.append(
                _call_func_in_thread(
                    test_get_func,
                    oid=oid,
                    pool=pool,
                ),
            )
            set_stubs.append(
                _call_func_in_thread(
                    test_set_func,
                    oid=oid,
                    value=target_value,
                    pool=pool,
                ),
            )
        et = time.time()
        self.assertTrue((et - st) < 0.5)
        st = time.time()
        for target_value in range(10):
            set_stub = set_stubs[target_value]
            get_stub = get_stubs[target_value]
            value, runtime = get_stub.result()
            self.assertEqual(value, target_value)
            logger.info(f"runtime: {runtime}")
            self.assertTrue(runtime >= 1.5)
            self.assertTrue(runtime <= 2.5)
            set_stub.result()
        et = time.time()
        self.assertTrue(et - st < 2.5)

    def test_local_pool(self) -> None:
        """Test local pool"""
        pool = get_pool(pool_type="local", max_len=100, max_expire=3600)
        self._test_result_pool(pool)

    @unittest.skip(reason="redis is not installed")
    def test_redis_pool(self) -> None:
        """Test Redis pool"""
        pool = get_pool(
            pool_type="redis",
            redis_url="redis://localhost:6379",
            max_expire=3600,
        )
        self._test_result_pool(pool)
        self.assertRaises(
            ConnectionError,
            get_pool,
            pool_type="redis",
            redis_url="redis://test:1234",
        )
