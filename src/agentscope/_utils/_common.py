# -*- coding: utf-8 -*-
"""The common utilities for agentscope library."""
import asyncio
import base64
import functools
import inspect
import json
import os
import tempfile
import types
import typing
from datetime import datetime
from typing import Union, Any, Callable, Type, Dict

import requests
from json_repair import repair_json
from pydantic import BaseModel

from .._logging import logger

if typing.TYPE_CHECKING:
    from mcp.types import Tool
else:
    Tool = "mcp.types.Tool"


def _json_loads_with_repair(
    json_str: str,
) -> Union[dict, list, str, float, int, bool, None]:
    """The given json_str maybe incomplete, e.g. '{"key', so we need to
    repair and load it into a Python object.
    """
    repaired = json_str
    try:
        repaired = repair_json(json_str)
    except Exception:
        pass

    try:
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to decode JSON string `{json_str}` after repairing it "
            f"into `{repaired}`. Error: {e}",
        ) from e


def _is_accessible_local_file(url: str) -> bool:
    """Check if the given URL is a local URL."""
    return os.path.isfile(url)


def _get_timestamp(add_random_suffix: bool = False) -> str:
    """Get the current timestamp in the format YYYY-MM-DD HH:MM:SS.sss."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if add_random_suffix:
        # Add a random suffix to the timestamp
        timestamp += f"_{os.urandom(3).hex()}"

    return timestamp


async def _is_async_func(func: Callable) -> bool:
    """Check if the given function is an async function, including
    coroutine functions, async generators, and coroutine objects.
    """

    return (
        inspect.iscoroutinefunction(func)
        or inspect.isasyncgenfunction(func)
        or isinstance(func, types.CoroutineType)
        or isinstance(func, types.GeneratorType)
        and asyncio.iscoroutine(func)
        or isinstance(func, functools.partial)
        and await _is_async_func(func.func)
    )


async def _execute_async_or_sync_func(
    func: Callable,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Execute an async or sync function based on its type.

    Args:
        func (`Callable`):
            The function to be executed, which can be either async or sync.
        *args (`Any`):
            Positional arguments to be passed to the function.
        **kwargs (`Any`):
            Keyword arguments to be passed to the function.

    Returns:
        `Any`:
            The result of the function execution.
    """

    if await _is_async_func(func):
        return await func(*args, **kwargs)

    return func(*args, **kwargs)


def _get_bytes_from_web_url(
    url: str,
    max_retries: int = 3,
) -> str:
    """Get the bytes from a given URL.

    Args:
        url (`str`):
            The URL to fetch the bytes from.
        max_retries (`int`, defaults to `3`):
            The maximum number of retries.
    """
    for _ in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content.decode("utf-8")

        except UnicodeDecodeError:
            return base64.b64encode(response.content).decode("ascii")

        except Exception as e:
            logger.info(
                "Failed to fetch bytes from URL %s. Error %s. Retrying...",
                url,
                str(e),
            )

    raise RuntimeError(
        f"Failed to fetch bytes from URL `{url}` after {max_retries} retries.",
    )


def _save_base64_data(
    media_type: str,
    base64_data: str,
) -> str:
    """Save the base64 data to a temp file and return the file path. The
    extension is guessed from the MIME type.

    Args:
        media_type (`str`):
            The MIME type of the data, e.g. "image/png", "audio/mpeg".
        base64_data (`str):
            The base64 data to be saved.
    """
    extension = "." + media_type.split("/")[-1]

    with tempfile.NamedTemporaryFile(
        suffix=f".{extension}",
        delete=False,
    ) as temp_file:
        decoded_data = base64.b64decode(base64_data)
        temp_file.write(decoded_data)
        temp_file.close()
        return temp_file.name


def _extract_json_schema_from_mcp_tool(tool: Tool) -> dict[str, Any]:
    """Extract JSON schema from MCP tool."""

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema.get(
                    "properties",
                    {},
                ),
                "required": tool.inputSchema.get(
                    "required",
                    [],
                ),
            },
        },
    }


def _remove_title_field(schema: dict) -> None:
    """Remove the title field from the JSON schema to avoid
    misleading the LLM."""
    # The top level title field
    if "title" in schema:
        schema.pop("title")

    # properties
    if "properties" in schema:
        for prop in schema["properties"].values():
            if isinstance(prop, dict):
                _remove_title_field(prop)

    # items
    if "items" in schema and isinstance(schema["items"], dict):
        _remove_title_field(schema["items"])

    # additionalProperties
    if "additionalProperties" in schema and isinstance(
        schema["additionalProperties"],
        dict,
    ):
        _remove_title_field(
            schema["additionalProperties"],
        )


def _create_tool_from_base_model(
    structured_model: Type[BaseModel],
    tool_name: str = "generate_structured_output",
) -> Dict[str, Any]:
    """Create a function tool definition from a Pydantic BaseModel.
    This function converts a Pydantic BaseModel class into a tool definition
    that can be used with function calling API. The resulting tool
    definition includes the model's JSON schema as parameters, enabling
    structured output generation by forcing the model to call this function
    with properly formatted data.

    Args:
        structured_model (`Type[BaseModel]`):
            A Pydantic BaseModel class that defines the expected structure
            for the tool's output.
        tool_name (`str`, default `"format_output"`):
            The name to assign to the generated tool.

    Returns:
        `Dict[str, Any]`: A tool definition dictionary compatible with
            function calling API, containing type ("function") and
            function dictionary with name, description, and parameters
            (JSON schema).

    .. code-block:: python
        :caption: Example usage

        from pydantic import BaseModel

        class PersonInfo(BaseModel):
            name: str
            age: int
            email: str

        tool = _create_tool_from_base_model(PersonInfo, "extract_person")
        print(tool["function"]["name"])  # extract_person
        print(tool["type"])              # function

    .. note:: The function automatically removes the 'title' field from
        the JSON schema to ensure compatibility with function calling
        format. This is handled by the internal ``_remove_title_field()``
        function.
    """
    schema = structured_model.model_json_schema()

    _remove_title_field(schema)
    tool_definition = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": "Generate the required structured output with "
            "this function",
            "parameters": schema,
        },
    }
    return tool_definition
