# -*- coding: utf-8 -*-
"""Service factory for model prompt."""
import collections.abc
from functools import partial
import inspect
from typing import (
    Callable,
    Any,
    Tuple,
    Union,
    Literal,
    get_args,
    get_origin
)

from docstring_parser import parse
from loguru import logger

from agentscope.service import bing_search


def  _get_type_str(cls):
    """Get the type string."""
    if hasattr(cls, "__origin__"):
        # Typing class
        if cls.__origin__ is Union:
            return [_get_type_str(_) for _ in get_args(cls)]
        elif cls.__origin__ is collections.abc.Sequence:
            return "array"
        else:
            return str(cls.__origin__)
    else:
        # Normal class
        if cls is str:
            return "string"
        elif cls in [float, int, complex]:
            return "number"
        elif cls is bool:
            return "boolean"
        elif cls is collections.abc.Sequence:
            return "array"
        elif cls is None.__class__:
            return "null"
        else:
            return cls.__name__



class ServiceFactory:
    """A service factory class that turns service function into string
    prompt format."""

    @classmethod
    def get(self, service_func: Callable[..., Any], **kwargs: Any) -> Tuple[
        Callable[..., Any], dict]:
        """Covnert a service function into a tool function that agent can
        use, and generate a dictionary in JSON Schema format that can be
        used in OpenAI API directly. While for open-source model, developers
        should handle the conversation from json dictionary to prompt.

        Args:
            service_func (`Callable[..., Any]`):
                The service function to be called.
            kwargs (`Any`):
                The arguments to be passed to the service function.

        Returns:
            `Tuple(Callable[..., Any], dict)`: A tuple of tool function and
            a dict in JSON Schema format to describe the function.

        Note:
            The description of the function and arguments are extracted from
            its docstring automatically, which should be well-formatted in
            **Google style**. Otherwise, their descriptions in the returned
            dictionary will be empty.

        Suggestions:
            1. The name of the service function should be self-explanatory,
            so that the agent can understand the function and use it properly.
            2. The typing of the arguments should be provided when defining
            the function (e.g. `def func(a: int, b: str, c: bool)`), so that
            the agent can specify the arguments properly.

        Example:

        """
        # Get the function for agent to use
        tool_func = partial(service_func, **kwargs)

        # Obtain all arguments of the service function
        argsspec = inspect.getfullargspec(service_func)

        # Construct the mapping from arguments to their typings
        docstring = parse(service_func.__doc__)

        # Function description
        func_description = (docstring.short_description or
                            docstring.long_description)

        # The arguments that requires the agent to specify
        args_agent = set(argsspec.args) - set(kwargs.keys())

        # Check if the arguments from agent have descriptions in docstring
        args_description = {_.arg_name: _.description  for _ in
                            docstring.params}

        # Prepare default values
        args_defaults = {k: v for k, v in zip(reversed(argsspec.args),
                                              reversed(argsspec.defaults))}
        args_required = list(set(args_agent) - set(args_defaults.keys()))

        # Prepare types of the arguments, remove the return type
        args_types = {k: v for k, v in argsspec.annotations.items() if k !=
                      "return"}

        # Prepare argument dictionary
        properties_field = dict()
        for key in args_agent:
            property = dict()
            # type
            if key in args_types:
                try:
                    required_type = _get_type_str(args_types[key])
                    property["type"] = required_type
                except Exception:
                    logger.warning(f"Fail and skip to get the type of the "
                                   f"argument `{key}`.")


                # For Literal type, add enum field
                if get_origin(args_types[key]) is Literal:
                    property["enum"] = list(args_types[key].__args__)

            # description
            if key in args_description:
                property["description"] = args_description[key]

            # default
            if key in args_defaults and args_defaults[key] is not None:
                property["default"] = args_defaults[key]

            properties_field[key] = property

        # Construct the JSON Schema for the service function
        func_dict = {
            "type": "function",
            "function": {
                "name": service_func.__name__,
                "description": func_description,
                "parameters": {
                    "type": "object",
                    "properties": properties_field,
                    "required": args_required
                }
            }
        }

        return tool_func, func_dict
