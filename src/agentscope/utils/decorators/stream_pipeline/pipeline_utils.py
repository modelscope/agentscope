# -*- coding: utf-8 -*-
""" Utils for pipeline decorator """
# pylint: disable=redefined-outer-name
import uuid
import threading
from functools import wraps
from typing import Callable, Any, Generator, Type


# mypy: disable-error-code="name-defined"
def pipeline(func: Callable) -> Callable:
    """
    A decorator that runs the given function in a separate thread and yields
    message instances as they are logged.
    This decorator is used to execute a function concurrently while providing a
    mechanism to yield messages produced during its execution. It leverages
    threading to run the function in parallel, yielding messages until the
    function completes.
    Args:
        func: The function to be executed in a separate thread.
    Returns:
        A wrapped function that, when called, returns a generator yielding
        message instances.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Generator:
        from ....agents import AgentBase
        from .hooks import (
            get_msg_instances,
            clear_msg_instances,
            pre_speak_msg_buffer_hook,
        )

        global AgentBase

        def _register_pre_speak_msg_buffer_hook(
            cls: Type[AgentBase],
        ) -> Type[AgentBase]:
            original_init = cls.__init__

            @wraps(original_init)
            def modified_init(self: Any, *args: Any, **kwargs: Any) -> None:
                original_init(self, *args, **kwargs)
                self.register_pre_speak_hook(
                    "pre_speak_msg_buffer_hook",
                    pre_speak_msg_buffer_hook,
                )

            cls.__init__ = modified_init
            return cls

        original_agent_base = AgentBase

        try:
            AgentBase = _register_pre_speak_msg_buffer_hook(AgentBase)

            thread_id = "pipeline" + str(uuid.uuid4())

            # Run the main function in a separate thread
            thread = threading.Thread(
                target=func,
                name=thread_id,
                args=args,
                kwargs=kwargs,
            )
            clear_msg_instances(thread_id=thread_id)
            thread.start()

            # Yield new Msg instances as they are logged
            for msg, msg_len in get_msg_instances(thread_id=thread_id):
                if msg:
                    yield msg
                # Break if the thread is dead and no more messages are expected
                if not thread.is_alive() and msg_len == 0:
                    break

            # Wait for the function to finish
            thread.join()
        finally:
            AgentBase = original_agent_base

    return wrapper
