# -*- coding: utf-8 -*-
""" Resource limiter module."""
import os
import math
import uuid
import time
from functools import wraps
from typing import Callable, Any

import redis
from loguru import logger

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))


def get_redis_client(
    host: str,
    port: int,
    db: int,
    retry_times: int = 1,
    delay: int = 1,
) -> redis.StrictRedis:
    """
    Connect to Redis server with retry logic.
    """
    for _ in range(retry_times):
        try:
            client = redis.StrictRedis(
                host=host,
                port=port,
                db=db,
            )
            client.ping()
            return client
        except redis.ConnectionError as e:
            logger.warning(
                f"[ResourceLimiter] Failed to connect to Redis:"
                f" {e}. Retrying in {delay} seconds...",
            )
            time.sleep(delay)
    # No redis found
    logger.warning(
        "[ResourceLimiter] No resource limits set. You could configure "
        "the environment variables `REDIS_HOST`, `REDIS_PORT`, and "
        "`REDIS_DB` for Redis to enable resource limiter.",
    )
    return None


redis_client = get_redis_client(REDIS_HOST, REDIS_PORT, REDIS_DB)


def resources_limit(function: Callable) -> Callable:
    """
    The decorated class must contain `self.resource_limit_number`
    and `self.resource_limit_type` (choose from `rate` and `capacity`).

    - `self.resource_limit_number`: An integer representing the resource limit.
      If `self.resource_limit_type` is `capacity`, it represents the maximum
      number of concurrent executions allowed.
      If `self.resource_limit_type` is `rate`, it represents the maximum number
      of executions allowed per minute.

    - `self.resource_limit_type`: A string that specifies the type of limit,
      either `rate` or `capacity`.

      When `self.resource_limit_type` is `rate`, the unit is counts per minute.
    """

    @wraps(function)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # No redis found
        if redis_client is None:
            return function(self, *args, **kwargs)

        # If some classes share the same resource limit
        if hasattr(self, "resource_limit_key") and isinstance(
            self.resources_limit_key,
            str,
        ):
            limit_key = self.resource_limit_key
        else:
            limit_key = type(self).__name__
        resources_limit_key = f"resource_limit_number_for_{limit_key}"
        queue_key = f"resources_queue_for_{limit_key}"

        request_id = str(uuid.uuid4())  # Use UUID for unique request IDs
        redis_client.lpush(queue_key, request_id)

        while True:
            available_resources = get_or_initialize_resource_cnt(
                self.resource_limit_type,
                resources_limit_key,
                self.resource_limit_number,
            )
            queue_size = redis_client.llen(queue_key)

            if available_resources > 0 and queue_size > 0:
                # Calculate how many requests can be processed in this batch
                process_count = min(available_resources, queue_size)
                queue_requests = redis_client.lrange(
                    queue_key,
                    0,
                    process_count - 1,
                )
                process_requests = [r.decode("utf-8") for r in queue_requests]

                logger.debug(f"[{limit_key}] {request_id}: {queue_requests}")

                if request_id in process_requests:
                    if self.resource_limit_type == "rate":
                        redis_client.zadd(
                            resources_limit_key,
                            {request_id: int(time.time())},
                        )
                    result = _process_request(
                        self,
                        function,
                        resources_limit_key,
                        queue_key,
                        request_id,
                        *args,
                        **kwargs,
                    )
                    # redis_client.lrem(queue_key, 1, request_id)
                    return result
            else:
                if self.resource_limit_type == "capacity":
                    logger.debug(
                        f"No resources available for {limit_key}. "
                        f"Waiting...\nNote: Max resource number is"
                        f" {self.resource_limit_number}, please consider "
                        f"increasing it!",
                    )
                else:
                    logger.debug(
                        f"Rate limit exceeded for {limit_key}. "
                        f"Waiting...\nNote: Max resource number is"
                        f" {self.resource_limit_number} per minute.",
                    )
            time.sleep(1)

    return wrapper


def get_or_initialize_resource_cnt(
    limit_type: str,
    key: str,
    initial_value: int,
) -> int:
    """
    Get or initialize resource count in Redis.
    """
    if limit_type == "capacity":
        value = redis_client.get(key)
        if value is None:
            if redis_client.setnx(key, initial_value):
                value = initial_value
            else:
                value = redis_client.get(key)
        return int(value)
    else:
        time_now = int(time.time())
        one_minute_ago = time_now - 60
        # Ensure the sorted set exists
        if not redis_client.exists(key):
            redis_client.zadd(key, {time_now: 0})

        # Remove expired timestamps
        redis_client.zremrangebyscore(key, 0, one_minute_ago)
        # Check the number of requests in the last minute
        request_count = redis_client.zcount(key, one_minute_ago, time_now)
        return int(initial_value - request_count)


def _process_request(
    self: Any,
    function: Callable,
    resources_limit_key: str,
    queue_key: str,
    request_id: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Process the actual function call.
    """
    if self.resource_limit_type == "capacity":
        redis_client.decr(resources_limit_key)
    redis_client.lrem(queue_key, 1, request_id)
    try:
        result = function(self, *args, **kwargs)
    except Exception as e:
        if self.resource_limit_type == "capacity":
            redis_client.incr(resources_limit_key)
        logger.error(f"Exception occurred: {e}")
        raise

    if self.resource_limit_type == "capacity":
        redis_client.incr(resources_limit_key)
        logger.debug(
            f"Current resources number:"
            f" {int(redis_client.get(resources_limit_key))}",
        )
    return result


if __name__ == "__main__":
    import threading
    from multiprocessing import Process

    class TestClass:
        """
        Test Class
        """

        def __init__(
            self,
            exec_time: int,
            resource_limit_number: int,
            resource_limit_type: str,
        ) -> None:
            self.exec_time = exec_time
            self.resource_limit_number = resource_limit_number
            self.resource_limit_type = resource_limit_type

        @resources_limit
        def test_method(self, x: int, y: int) -> int:
            """
            Test method for @resources_limit
            """
            result = x + y
            logger.debug(f"Processing request: {x} + {y} = {result}")
            time.sleep(self.exec_time)
            return result

    resource_limit_mode = input(
        "Input resource limit type: `rate` or `capacity`: ",
    )
    exc_time = int(input("Input function execute time: "))
    num_task = int(input("Input number of total task: "))
    resource_num = int(input("Input number of resource: "))
    sim_mode = input("Choose testing mode `threading` or `multiprocessing`: ")

    # Init for debug
    c_name = TestClass.__name__
    r_limit_key = f"resource_limit_number_for_{c_name}"
    q_key = f"resources_queue_for_{c_name}"

    if redis_client:
        redis_client.delete(r_limit_key)
        if resource_limit_mode == "capacity":
            redis_client.set(r_limit_key, resource_num)
        else:
            redis_client.zadd(r_limit_key, {time.time(): 0})
        redis_client.delete(q_key)

        key_type = redis_client.type(r_limit_key).decode("utf-8")
        logger.debug(f"Type of {r_limit_key}: {key_type}")

        # Log the value based on the type of key
        if key_type == "string":
            logger.debug(f"{r_limit_key}: {redis_client.get(r_limit_key)}")
        elif key_type == "zset":
            logger.debug(
                f"{r_limit_key}:"
                f" {redis_client.zrange(r_limit_key, 0, -1, withscores=True)}",
            )
        else:
            logger.warning(f"{r_limit_key} has an unexpected type: {key_type}")

    if resource_limit_mode == "capacity":
        simulation_time = math.ceil(num_task / resource_num) * exc_time
    else:
        simulation_time = (
            math.ceil(num_task / resource_num) - 1
        ) * 60 + exc_time

    input(
        f"The simulation time takes for about: "
        f"{simulation_time}\nType enter to start...",
    )
    start_time = time.time()
    test_instance = TestClass(
        exec_time=exc_time,
        resource_limit_number=resource_num,
        resource_limit_type=resource_limit_mode,
    )

    def make_request(instance: TestClass, x: int, y: int) -> None:
        """
        Make request.
        """
        result = instance.test_method(x, y)
        print(f"Result of {x} + {y} = {result}")

    if sim_mode in ["multiprocessing", "p"]:
        processes = []
        for i in range(num_task):
            p = Process(target=make_request, args=(test_instance, i, i + 1))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()
    else:
        threads = []
        for i in range(num_task):
            t = threading.Thread(
                target=make_request,
                args=(test_instance, i, i + 1),
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    # The simulation time might be larger due to GIL and database delay
    logger.debug(
        f"Simulation time: {time.time() - start_time}\n "
        f"Expected simulation time: {simulation_time}",
    )
