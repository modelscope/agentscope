# -*- coding: utf-8 -*-
"""The configuration file should contain one or a list of model configs,
and each model config should follow the following format.

.. code-block:: python

    {
        "type": "openai" | "post_api",
        "name": "{model_name}",
        ...
    }

After that, you can specify model by {model_name}.

Note:
    The parameters for different types of models are different. For OpenAI API,
    the format is:

        .. code-block:: python

            {
                "type": "openai",
                "name": "{name of your model}",
                "model_name": "{model_name_for_openai, e.g. gpt-3.5-turbo}",
                "api_key": "{your_api_key}",
                "organization": "{your_organization, if needed}",
                "client_args": {
                    # ...
                },
                "generate_args": {
                    # ...
                }
            }


    For Post API, toking huggingface inference API as an example, its format
    is:

        .. code-block:: python

            {
                "type": "post_api",
                "name": "{model_name}",
                "api_url": "{api_url}",
                "headers": {"Authorization": "Bearer {API_TOKEN}"},
                "max_length": {max_length_of_model},
                "timeout": {timeout},
                "max_retries": {max_retries},
                "generate_args": {
                    "temperature": 0.5,
                    # ...
                }
            }

"""
import inspect
import time
from abc import ABCMeta
from functools import wraps
from typing import Union, Any, Callable

from loguru import logger

from ..file_manager import file_manager
from ..utils.tools import _get_timestamp

# TODO: move default values into a single file
DEFAULT_MAX_RETRIES = 1


def _response_parse_decorator(
    model_call: Callable,
) -> Callable:
    """A decorator for parsing the response of model call. It will take
    `parse_func`, `fault_handler` and `max_retries` as arguments. The
    detailed process is as follows:

        1. If `parse_func` is provided, then the response will be parsed first.

        2. If the parsing fails (throws an exception), then response generation
        will be repeated for `max_retries` times and parsed again.

        3. After `max_retries` times, if the parsing still fails, then if
        `fault_handler` is provided, the response will be processed by
        `fault_handler`.
    """

    # check if the decorated `model_call` function uses the default
    # arguments of this decorator.
    parameters = inspect.signature(model_call).parameters

    for name in parameters.keys():
        if name in ["parse_func", "max_retries"]:
            logger.warning(
                f"The argument {name} is used by the decorator, "
                f"which will not be passed to the model call "
                f"function.",
            )

    @wraps(model_call)
    def checking_wrapper(self: Any, *args: Any, **kwargs: Any) -> dict:
        # Step1: Extract parse_func and fault_handler
        parse_func = kwargs.pop("parse_func", None)
        fault_handler = kwargs.pop("fault_handler", None)
        max_retries = kwargs.pop("max_retries", None) or DEFAULT_MAX_RETRIES
        # Step2: Call the model and parse the response
        # Return the response directly if parse_func is not provided
        if parse_func is None:
            return model_call(self, *args, **kwargs)

        # Otherwise, try to parse the response
        response = None
        for itr in range(1, max_retries + 1):
            # Call the model
            response = model_call(self, *args, **kwargs)

            # Parse the response if needed
            try:
                return parse_func(response)
            except Exception as e:
                logger.warning(
                    f"Fail to parsing response: "
                    f"{response}.\n Exception: {e}, "
                    f"\t Attempt {itr} / {max_retries}",
                )
                time.sleep(0.5 * itr)

        if fault_handler is not None and callable(fault_handler):
            return fault_handler(response)
        else:
            raise ValueError(
                f"fail to parsing response with: "
                f"{parse_func.__name__}. \n  "
                f"\t Attempts fails {max_retries} times",
            )

    return checking_wrapper


class _ModelWrapperMeta(ABCMeta):
    """A meta call to replace the model wrapper's __call__ function with
    wrapper about error handling."""

    def __new__(mcs, name: Any, bases: Any, attrs: Any) -> Any:
        if "__call__" in attrs:
            attrs["__call__"] = _response_parse_decorator(attrs["__call__"])
        return super().__new__(mcs, name, bases, attrs)


class ModelWrapperBase(metaclass=_ModelWrapperMeta):
    """The base class for model wrapper."""

    def __init__(
        self,
        name: str,
    ) -> None:
        r"""Base class for model wrapper.

        All model wrappers should inherit this class and implement the
        `__call__` function.

        Args:
            name (`str`):
                The name of the model, which is used to extract configuration
                from the config file.
        """
        self.name = name

    def __call__(self, *args: Any, **kwargs: Any) -> Union[str, dict, list]:
        """Processing input with the model."""
        raise NotImplementedError(
            f"Model Wrapper [{type(self).__name__}]"
            f" is missing the  the required `__call__`"
            f" method.",
        )

    def _save_model_invocation(
        self,
        arguments: dict,
        json_response: Any,
    ) -> None:
        """Save model invocation."""
        model_class = self.__class__.__name__
        timestamp = _get_timestamp("%Y%m%d-%H%M%S")

        invocation_record = {
            "model_class": model_class,
            "timestamp": timestamp,
            "arguments": arguments,
            "json_response": json_response,
        }

        file_manager.save_api_invocation(
            f"model_{model_class}_{timestamp}",
            invocation_record,
        )
