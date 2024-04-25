# -*- coding: utf-8 -*-
"""The configuration file should contain one or a list of model configs,
and each model config should follow the following format.

.. code-block:: python

    {
        "config_name": "{config_name}",
        "model_type": "openai_chat" | "post_api" | ...,
        ...
    }

After that, you can specify model by {config_name}.

Note:
    The parameters for different types of models are different. For OpenAI API,
    the format is:

        .. code-block:: python

            {
                "config_name": "{id of your model}",
                "model_type": "openai_chat",
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
                "config_name": "{config_name}",
                "model_type": "post_api",
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
from __future__ import annotations
import inspect
import time
from abc import ABCMeta
from functools import wraps
from typing import Sequence, Any, Callable, Union, List, Type

from loguru import logger

from agentscope.utils import QuotaExceededError
from .response import ModelResponse
from ..exception import ResponseParsingError

from ..file_manager import file_manager
from ..message import MessageBase
from ..utils import MonitorFactory
from ..utils.monitor import get_full_name
from ..utils.tools import _get_timestamp
from ..constants import _DEFAULT_MAX_RETRIES
from ..constants import _DEFAULT_RETRY_INTERVAL


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
        max_retries = kwargs.pop("max_retries", None) or _DEFAULT_MAX_RETRIES

        # Step2: Call the model and parse the response
        # Return the response directly if parse_func is not provided
        if parse_func is None:
            return model_call(self, *args, **kwargs)

        # Otherwise, try to parse the response
        for itr in range(1, max_retries + 1):
            # Call the model
            response = model_call(self, *args, **kwargs)

            # Parse the response if needed
            try:
                return parse_func(response)
            except ResponseParsingError as e:
                if itr < max_retries:
                    logger.warning(
                        f"Fail to parse response ({itr}/{max_retries}):\n"
                        f"{response}.\n"
                        f"{e.__class__.__name__}: {e}",
                    )
                    time.sleep(_DEFAULT_RETRY_INTERVAL * itr)
                else:
                    if fault_handler is not None and callable(fault_handler):
                        return fault_handler(response)
                    else:
                        raise
        return {}

    return checking_wrapper


class _ModelWrapperMeta(ABCMeta):
    """A meta call to replace the model wrapper's __call__ function with
    wrapper about error handling."""

    def __new__(mcs, name: Any, bases: Any, attrs: Any) -> Any:
        if "__call__" in attrs:
            attrs["__call__"] = _response_parse_decorator(attrs["__call__"])
        return super().__new__(mcs, name, bases, attrs)

    def __init__(cls, name: Any, bases: Any, attrs: Any) -> None:
        if not hasattr(cls, "_registry"):
            cls._registry = {}
            cls._type_registry = {}
            cls._deprecated_type_registry = {}
        else:
            cls._registry[name] = cls
            if hasattr(cls, "model_type"):
                cls._type_registry[cls.model_type] = cls
                if hasattr(cls, "deprecated_model_type"):
                    cls._deprecated_type_registry[
                        cls.deprecated_model_type
                    ] = cls
        super().__init__(name, bases, attrs)


class ModelWrapperBase(metaclass=_ModelWrapperMeta):
    """The base class for model wrapper."""

    model_type: str
    """The type of the model wrapper, which is to identify the model wrapper
    class in model configuration."""

    config_name: str
    """The name of the model configuration."""

    model_name: str
    """The name of the model, which is used in model api calling."""

    def __init__(
        self,  # pylint: disable=W0613
        config_name: str,
        **kwargs: Any,
    ) -> None:
        """Base class for model wrapper.

        All model wrappers should inherit this class and implement the
        `__call__` function.

        Args:
            config_name (`str`):
                The id of the model, which is used to extract configuration
                from the config file.
        """
        self.monitor = MonitorFactory.get_monitor()

        self.config_name = config_name
        logger.info(f"Initialize model by configuration [{config_name}]")

    @classmethod
    def get_wrapper(cls, model_type: str) -> Type[ModelWrapperBase]:
        """Get the specific model wrapper"""
        if model_type in cls._type_registry:
            return cls._type_registry[model_type]  # type: ignore[return-value]
        elif model_type in cls._registry:
            return cls._registry[model_type]  # type: ignore[return-value]
        elif model_type in cls._deprecated_type_registry:
            deprecated_cls = cls._deprecated_type_registry[model_type]
            logger.warning(
                f"Model type [{model_type}] will be deprecated in future "
                f"releases, please use [{deprecated_cls.model_type}] instead.",
            )
            return deprecated_cls  # type: ignore[return-value]
        else:
            return None  # type: ignore[return-value]

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        """Processing input with the model."""
        raise NotImplementedError(
            f"Model Wrapper [{type(self).__name__}]"
            f" is missing the required `__call__`"
            f" method.",
        )

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> Union[List[dict], str]:
        """Format the input string or dict into the format that the model
        API required."""
        raise NotImplementedError(
            f"Model Wrapper [{type(self).__name__}]"
            f" is missing the required `format` method",
        )

    def _save_model_invocation(
        self,
        arguments: dict,
        response: Any,
    ) -> None:
        """Save model invocation."""
        model_class = self.__class__.__name__
        timestamp = _get_timestamp("%Y%m%d-%H%M%S")

        invocation_record = {
            "model_class": model_class,
            "timestamp": timestamp,
            "arguments": arguments,
            "response": response,
        }

        file_manager.save_api_invocation(
            f"model_{model_class}_{timestamp}",
            invocation_record,
        )

    def _register_budget(self, model_name: str, budget: float) -> None:
        """Register the budget of the model by model_name."""
        self.monitor.register_budget(
            model_name=model_name,
            value=budget,
            prefix=model_name,
        )

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""

    def _metric(self, metric_name: str) -> str:
        """Add the class name and model name as prefix to the metric name.

        Args:
            metric_name (`str`):
                The metric name.

        Returns:
            `str`: Metric name of this wrapper.
        """

        if hasattr(self, "model_name"):
            return get_full_name(name=metric_name, prefix=self.model_name)
        else:
            return get_full_name(name=metric_name)

    def update_monitor(self, **kwargs: Any) -> None:
        """Update the monitor with the given values.

        Args:
            kwargs (`dict`):
                The values to be updated to the monitor.
        """
        if hasattr(self, "model_name"):
            prefix = self.model_name
        else:
            prefix = None

        try:
            self.monitor.update(
                kwargs,
                prefix=prefix,
            )
        except QuotaExceededError as e:
            logger.error(e.message)
