# -*- coding: utf-8 -*-
"""The model wrapper base class."""

from __future__ import annotations
import inspect
import time
from functools import wraps
from typing import Any, Callable, Union, List, Optional

from loguru import logger

from .response import ModelResponse
from ..exception import ResponseParsingError

from ..manager import FileManager
from ..manager import MonitorManager
from ..message import Msg
from ..utils.common import _get_timestamp
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


class ModelWrapperBase:
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
        config_name: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Base class for model wrapper.

        All model wrappers should inherit this class and implement the
        `__call__` function.

        Args:
            config_name (`Optional[str]`, defaults to `None`):
                The id of the model, which is used to extract configuration
                from the config file.
            model_name (`Optional[str]`, defaults to `None`):
                The name of the model.
        """
        self.monitor = MonitorManager.get_instance()

        self.config_name = config_name

        if model_name is None:
            raise ValueError(
                "Model name should be provided for model "
                f"configuration [{config_name}].",
            )

        self.model_name = model_name

        logger.debug(f"Initialize model by configuration [{config_name}]")

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        """Processing input with the model."""
        raise NotImplementedError(
            f"Model Wrapper [{type(self).__name__}]"
            f" is missing the required `__call__`"
            f" method.",
        )

    def format(
        self,
        *args: Union[Msg, list[Msg]],
    ) -> Union[List[dict], str]:
        """Format the input messages into the format that the model
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

        FileManager.get_instance().save_api_invocation(
            f"model_{model_class}_{timestamp}",
            invocation_record,
        )
