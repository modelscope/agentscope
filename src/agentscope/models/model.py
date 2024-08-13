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

from .response import ModelResponse
from ..exception import ResponseParsingError

from ..manager import FileManager
from ..manager import MonitorManager
from ..message import Msg
from ..utils.tools import _get_timestamp, _convert_to_str
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
        model_name: str,
        **kwargs: Any,
    ) -> None:
        """Base class for model wrapper.

        All model wrappers should inherit this class and implement the
        `__call__` function.

        Args:
            config_name (`str`):
                The id of the model, which is used to extract configuration
                from the config file.
            model_name (`str`):
                The name of the model.
        """
        self.monitor = MonitorManager.get_instance()

        self.config_name = config_name
        self.model_name = model_name
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
        *args: Union[Msg, Sequence[Msg]],
    ) -> Union[List[dict], str]:
        """Format the input string or dict into the format that the model
        API required."""
        raise NotImplementedError(
            f"Model Wrapper [{type(self).__name__}]"
            f" is missing the required `format` method",
        )

    @staticmethod
    def format_for_common_chat_models(
        *args: Union[Msg, Sequence[Msg]],
    ) -> List[dict]:
        """A common format strategy for chat models, which will format the
        input messages into a user message.

        Note this strategy maybe not suitable for all scenarios,
        and developers are encouraged to implement their own prompt
        engineering strategies.

        The following is an example:

        .. code-block:: python

            prompt1 = model.format(
                Msg("system", "You're a helpful assistant", role="system"),
                Msg("Bob", "Hi, how can I help you?", role="assistant"),
                Msg("user", "What's the date today?", role="user")
            )

            prompt2 = model.format(
                Msg("Bob", "Hi, how can I help you?", role="assistant"),
                Msg("user", "What's the date today?", role="user")
            )

        The prompt will be as follows:

        .. code-block:: python

            # prompt1
            [
                {
                    "role": "user",
                    "content": (
                        "You're a helpful assistant\\n"
                        "\\n"
                        "## Conversation History\\n"
                        "Bob: Hi, how can I help you?\\n"
                        "user: What's the date today?"
                    )
                }
            ]

            # prompt2
            [
                {
                    "role": "user",
                    "content": (
                        "## Conversation History\\n"
                        "Bob: Hi, how can I help you?\\n"
                        "user: What's the date today?"
                    )
                }
            ]


        Args:
            args (`Union[Msg, Sequence[Msg]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `List[dict]`:
                The formatted messages.
        """
        if len(args) == 0:
            raise ValueError(
                "At least one message should be provided. An empty message "
                "list is not allowed.",
            )

        # Parse all information into a list of messages
        input_msgs = []
        for _ in args:
            if _ is None:
                continue
            if isinstance(_, Msg):
                input_msgs.append(_)
            elif isinstance(_, list) and all(isinstance(__, Msg) for __ in _):
                input_msgs.extend(_)
            else:
                raise TypeError(
                    f"The input should be a Msg object or a list "
                    f"of Msg objects, got {type(_)}.",
                )

        # record dialog history as a list of strings
        dialogue = []
        sys_prompt = None
        for i, unit in enumerate(input_msgs):
            if i == 0 and unit.role == "system":
                # if system prompt is available, place it at the beginning
                sys_prompt = _convert_to_str(unit.content)
            else:
                # Merge all messages into a conversation history prompt
                dialogue.append(
                    f"{unit.name}: {_convert_to_str(unit.content)}",
                )

        content_components = []
        # Add system prompt at the beginning if provided
        if sys_prompt is not None:
            if not sys_prompt.endswith("\n"):
                sys_prompt += "\n"
            content_components.append(sys_prompt)

        # The conversation history is added to the user message if not empty
        if len(dialogue) > 0:
            content_components.extend(["## Conversation History"] + dialogue)

        messages = [
            {
                "role": "user",
                "content": "\n".join(content_components),
            },
        ]

        return messages

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
