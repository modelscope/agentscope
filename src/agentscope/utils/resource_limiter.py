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
    Decorator that limits the number of concurrent executions of a function
    based on available resources.
    """

    @wraps(function)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # No redis or no limit
        if redis_client is None or self.resource_count == math.inf:
            return function(self, *args, **kwargs)

        class_name = type(self).__name__
        resources_limit_key = f"resources_limit_count_for_{class_name}"
        queue_key = f"resources_queue_for_{class_name}"

        request_id = str(uuid.uuid4())  # Use UUID for unique request IDs
        redis_client.lpush(queue_key, request_id)

        while True:
            available_resources = get_or_initialize_resource_cnt(
                resources_limit_key,
                self.resource_count,
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

                logger.debug(f"[{class_name}] {request_id}: {queue_requests}")

                if request_id in process_requests:
                    result = _process_request(
                        self,
                        function,
                        resources_limit_key,
                        *args,
                        **kwargs,
                    )
                    redis_client.lrem(queue_key, 1, request_id)
                    return result
            else:
                logger.debug(
                    f"No resources available for {class_name}. Waiting...\n"
                    f"Note: Max resource number is {self.resource_count}, "
                    f"please consider increasing it!",
                )
            time.sleep(1)

    return wrapper


def get_or_initialize_resource_cnt(key: str, initial_value: int) -> int:
    """
    Get or initialize resource count in Redis.
    """
    value = redis_client.get(key)
    if value is None:
        if redis_client.setnx(key, initial_value):
            value = initial_value
        else:
            value = redis_client.get(key)
    return int(value)


def _process_request(
    self: Any,
    function: Callable,
    resources_limit_key: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Process the actual function call.
    """
    redis_client.decr(resources_limit_key)
    try:
        result = function(self, *args, **kwargs)
    except Exception as e:
        redis_client.incr(resources_limit_key)
        logger.error(f"Exception occurred: {e}")
        raise

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

        def __init__(self, exec_time: int, resource_count: int) -> None:
            self.exec_time = exec_time
            self.resource_count = resource_count

        @resources_limit
        def test_method(self, x: int, y: int) -> int:
            """
            Test methdo for @resources_limit
            """
            result = x + y
            logger.debug(f"Processing request: {x} + {y} = {result}")
            time.sleep(self.exec_time)
            return result

    exc_time = int(input("Input function execute time:"))
    num_task = int(input("Input number of total task:"))
    resource_num = int(input("Input number of resource:"))
    sim_mode = input("Choose testing mode `threading` or `multiprocessing`")

    # Init for debug
    c_name = TestClass.__name__
    r_limit_key = f"resources_limit_count_for_{c_name}"
    q_key = f"resources_queue_for_{c_name}"

    if redis_client:
        redis_client.set(r_limit_key, resource_num)
        redis_client.delete(q_key)
        logger.debug(
            f"{r_limit_key}:" f" {int(redis_client.get(r_limit_key))}",
        )

    simulation_time = math.ceil(num_task / resource_num) * exc_time

    input(
        f"The simulation time takes for about: "
        f"{simulation_time}\nType enter to start...",
    )
    start_time = time.time()
    test_instance = TestClass(exec_time=exc_time, resource_count=resource_num)

    def make_request(instance: TestClass, x: int, y: int) -> None:
        """
        Make request.
        """
        result = instance.test_method(x, y)
        print(f"Result of {x} + {y} = {result}")

    if sim_mode == "multiprocessing":
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
