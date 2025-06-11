# -*- coding: utf-8 -*-
""" Hooks for stream output """
# pylint: disable=unused-argument
import time
import threading
from collections import defaultdict
from typing import Union, Optional, Generator

from ....agents import AgentBase
from ....message import Msg

_MSG_INSTANCE = defaultdict(list)
_LOCKS = defaultdict(threading.Lock)


def pre_speak_msg_buffer_hook(
    self: AgentBase,
    x: Msg,
    stream: bool,
    last: bool,
) -> Union[Msg, None]:
    """Hook for pre speak msg buffer"""
    thread_id = threading.current_thread().name
    if thread_id.startswith("pipeline"):
        with _LOCKS[thread_id]:
            _MSG_INSTANCE[thread_id].append(x)
    return x


def clear_msg_instances(thread_id: Optional[str] = None) -> None:
    """
    Clears all message instances for a specific thread ID.
    This function removes all message instances associated with a given
    thread ID (`thread_id`). It ensures thread safety through the use of a
    threading lock when accessing the shared message instance list. This
    prevents race conditions in concurrent environments.
    Args:
        thread_id (optional): The thread ID for which to clear message
        instances. If `None`, the function will do nothing.
    Notes:
        - It assumes the existence of a global `_LOCKS` for synchronization and
        a dictionary `_MSG_INSTANCE` where each thread ID maps to a list of
        message instances.
    """
    if not thread_id:
        return

    with _LOCKS[thread_id]:
        _MSG_INSTANCE[thread_id].clear()


def get_msg_instances(thread_id: Optional[str] = None) -> Generator:
    """
    A generator function that yields message instances for a specific thread ID
    This function is designed to continuously monitor and yield new message
    instances associated with a given thread ID (`thread_id`). It ensures
    thread safety through the use of a threading lock when accessing the shared
    message instance list. This prevents race conditions in concurrent
    environments.
    Args:
        thread_id (optional): The thread ID for which to monitor and yield
        message instances. If `None`, the function will yield `None` and
        terminate.
    Yields:
        The next available message instance for the specified thread ID. If no
        message is available, it will wait and check periodically.
    Notes:
        - The function uses a small delay (`time.sleep(0.1)`) to prevent busy
        waiting. This ensures efficient CPU usage while waiting for new
        messages.
        - It assumes the existence of a global `_LOCK` for synchronization and
        a dictionary `_MSG_INSTANCE` where each thread ID maps to a list of
        message instances.
    Example:
        for msg in get_msg_instances(thread_id=123):
            process_message(msg)
    """
    if not thread_id:
        yield
        return

    while True:
        with _LOCKS[thread_id]:
            if _MSG_INSTANCE[thread_id]:
                yield _MSG_INSTANCE[thread_id].pop(0), len(
                    _MSG_INSTANCE[thread_id],
                )
            else:
                yield None, None
        time.sleep(0.1)  # Avoid busy waiting
