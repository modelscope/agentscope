# -*- coding: utf-8 -*-
"""Some utilities"""
import datetime
import random
import string
import tiktoken


def create_timestamp(format_: str = "%Y-%m-%d-%H-%M-%S") -> str:
    """Get current timestamp"""
    return (
        datetime.datetime.now().strftime(format_)
        + "-"
        + "".join([random.choice(string.ascii_lowercase) for _ in range(6)])
    )


def calculate_latency_parallel(sub_latencies: list, p: int) -> float:
    """Simulate latency with parallelism degree p"""
    k = len(sub_latencies)
    p = int(p)
    num_parallel_group = k // p if k % p == 0 else k // p + 1
    sub_latencies_parallel = [
        max(sub_latencies[i * p : min((i + 1) * p, k)])
        for i in range(num_parallel_group)
    ]
    return float(sum(sub_latencies_parallel))


def num_tokens_from_string(
    input_string: str,
    encoding_name: str = "cl100k_base",
) -> int:
    """Returns the number of tokens in a text string.

    Ref:
    https://github.com/openai/openai-cookbook/blob/main/examples/
    How_to_count_tokens_with_tiktoken.ipynb
    """
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(input_string))
    return num_tokens


def divide_string_into_chunks(
    request_string: str,
    window_size: int,
    step_size: int,
) -> list:
    """Divide a string into chunks"""

    n = len(request_string)
    if (window_size > n) or (window_size <= 0):
        window_size = n
        print("WARNING: reset chunking window size to n.")
    sub_requests = []
    idx0, idx1 = 0, window_size
    while idx1 <= n:
        sub_requests.append(request_string[round(idx0) : round(idx1)])
        if idx1 == n:
            break
        idx0 = idx0 + step_size
        idx1 = min(idx1 + step_size, n)
    return sub_requests
