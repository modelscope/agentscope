# -*- coding: utf-8 -*-
"""Utils"""
import asyncio

from typing import Any, Callable


def run_sync(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Run a function synchronously."""
    loop = asyncio.get_event_loop()

    if loop.is_running():
        # This block is for environments that already have a running event
        # loop, such as Jupyter notebooks or certain web servers.
        # It schedules the cleanup_tasks coroutine to run in the existing
        # event loop.
        results = asyncio.run_coroutine_threadsafe(
            func(*args, **kwargs),
            loop,
        ).result()
    else:
        # If there is no running event loop, we can simply run the coroutine
        # using run_until_complete.
        results = loop.run_until_complete(func(*args, **kwargs))
    return results
