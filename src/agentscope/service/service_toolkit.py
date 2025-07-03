# -*- coding: utf-8 -*-
"""Service Toolkit for service function usage."""
import json
from copy import deepcopy
from functools import partial
import inspect
from typing import (
    Callable,
    Any,
    Tuple,
    Union,
    Optional,
    Dict,
    Type,
)

from docstring_parser import parse
from loguru import logger
from pydantic import (
    Field,
    create_model,
    ConfigDict,
    BaseModel,
)

from ..exception import (
    JsonParsingError,
    FunctionNotFoundError,
    FunctionCallFormatError,
    FunctionCallError,
)
from .service_response import ServiceResponse
from .service_response import ServiceExecStatus
from .mcp_manager import MCPSessionHandler, sync_exec
from ..message import (
    Msg,
    ToolUseBlock,
    ToolResultBlock,
    ContentBlock,
)


class ServiceFunction:
    """The service function class."""

    name: str
    """The name of the service function."""

    original_func: Callable
    """The original function before processing."""

    processed_func: Callable
    """The processed function that can be called by the model directly."""

    extended_model: Union[Type[BaseModel], None]
    """The BaseModel class that extends the JSON schema of the current
    service function."""

    def __init__(
        self,
        name: str,
        original_func: Callable,
        processed_func: Callable,
        json_schema: dict,
    ) -> None:
        """Initialize the service function object."""

        self.name = name
        self.original_func = original_func
        self.processed_func = processed_func
        self._json_schema = json_schema

        self.extended_model = None

    @property
    def json_schema(self) -> dict:
        """The JSON schema of this tool function."""
        if self.extended_model is None:
            return self._json_schema

        # Merge the extended model with the original JSON schema
        extended_schema = self.extended_model.model_json_schema()

        merged_schema = deepcopy(self._json_schema)

        ServiceToolkit._remove_title_field(  # pylint: disable=protected-access
            extended_schema,
        )

        for key, value in extended_schema["properties"].items():
            if (
                key
                in self._json_schema["function"]["parameters"]["properties"]
            ):
                raise ValueError(
                    f"The field `{key}` already exists in the original "
                    f"function schema of `{self.name}`. Try to use a "
                    "different name.",
                )

            merged_schema["function"]["parameters"]["properties"][key] = value

            if key in extended_schema.get("required", []):
                merged_schema["function"]["parameters"]["required"].append(key)
        return merged_schema

    # json_schema的赋值
    @json_schema.setter
    def json_schema(self, value: dict) -> None:
        """Set the JSON schema of this tool function."""
        self._json_schema = value

        if value.get("type") != "function" or "function" not in value:
            raise ValueError(
                f"The JSON schema should be a function schema with type field "
                f"'function', but got {value.get('type')} instead.",
            )

        if self.extended_model is not None:
            logger.warning(
                f"The extended model of `{self.name}` is not None, when "
                "accessing the json_schema property, it will be merged with "
                "the extended model's schema. Please ensure that the "
                "json_schema property is as expected.",
            )


class ServiceToolkit:
    """A toolkit class that maintains a list of tool functions, extracts JSON
    schema automatically, and provides a robust way to call these functions."""

    service_funcs: dict[str, ServiceFunction]
    """The registered functions in the service toolkit."""

    _tools_instruction_format: str = (
        "## Tool Functions:\n"
        "The following tool functions are available in the format of\n"
        "```\n"
        "{{index}}. {{function name}}: {{function description}}\n"
        "{{argument1 name}} ({{argument type}}): {{argument description}}\n"
        "{{argument2 name}} ({{argument type}}): {{argument description}}\n"
        "...\n"
        "```\n\n"
        "{function_prompt}\n"
    )
    """The instruction template for the tool functions."""

    _tools_calling_format: str = (
        '[{"name": "{function name}", "arguments": {"{argument1 name}": xxx,'
        ' "{argument2 name}": xxx}}]'
    )
    """The format of the tool function call."""

    _tools_execution_format: str = (
        "{index}. Execute function {function_name}\n"
        "   [ARGUMENTS]:\n"
        "       {arguments}\n"
        "   [RESULT]: {result}\n"
    )
    """The prompt template for the execution results."""

    def __init__(self) -> None:
        """Initialize the service toolkit with a list of service functions."""
        self.service_funcs = {}

    def remove(self, func_name: str) -> None:
        """Remove a service function from the current toolkit.

        Args:
            func_name (`str`):
                The name of the service function to be removed.
        """
        if func_name in self.service_funcs:
            del self.service_funcs[func_name]
        else:
            logger.warning(
                f"Service function `{func_name}` does not exist, "
                f"skip removing it.",
            )

    def extend_function_schema(
        self,
        func_name: str,
        model: Type[BaseModel],
    ) -> None:
        """Add an extra schema model to the existing service function's
        JSON schema.

        .. note:: You need to ensure that the function accepts the extra
         keywords via `**kwargs` in its definition, otherwise error will be
         raised when calling the function.

        Args:
            func_name (`str`):
                The name of the service function to be added.
            model (`Type[BaseModel]`):
                The extra schema model to be added to the service function's
                JSON schema.
        """
        if func_name not in self.service_funcs:
            raise FunctionNotFoundError(
                f"Cannot find a service function named `{func_name}`.",
            )

        if not issubclass(model, BaseModel):
            raise TypeError(
                f"The model should be a subclass of BaseModel, "
                f"but got {type(model)} instead.",
            )

        self.service_funcs[func_name].extended_model = model

    def restore_function_schema(self, func_name: str) -> None:
        """Restore the original JSON schema of a function to its original
        state, removing any extensions that were added previously.

        Args:
            func_name (`str`):
                The name of the service function whose schema is to be
                restored.
        """
        if func_name not in self.service_funcs:
            raise FunctionNotFoundError(
                f"Cannot find a service function named `{func_name}`.",
            )
        self.service_funcs[func_name].extended_model = None

    def add(
        self,
        service_func: Callable[..., Any],
        func_description: Optional[str] = None,
        include_long_description: bool = True,
        include_var_positional: bool = False,
        include_var_keyword: bool = False,
        overwrite_if_exists: bool = False,
        **kwargs: Any,
    ) -> None:
        """Add a service function to the toolkit, which will be processed into
        a tool function that can be called by the model directly, and
        registered in processed_funcs.

        Args:
            service_func (`Callable[..., Any]`):
                The service function to be called.
            func_description (`Optional[str]`, defaults to `None`):
                The function description. If not provided, the description
                will be extracted from the docstring automatically.
            include_long_description (`bool`, defaults to `True`):
                When extracting function description from the docstring, if
                the long description will be included.
            include_var_positional (`bool`, defaults to `False`):
                Whether to include the variable positional arguments (`*args`)
                in the function schema.
            include_var_keyword (`bool`, defaults to `False`):
                Whether to include the variable keyword arguments (`**kwargs`)
                in the function schema.
            overwrite_if_exists (`bool`, defaults to `False`):
                Whether to overwrite if the function with the same name
                already exists in the toolkit. If `False`, the function will
                be skipped if it already exists.
            **kwargs (`Any`):
                The keyword arguments that preset by developers, which will
                not be exposed to the agent

        Returns:
            `Tuple(Callable[..., Any], dict)`: A tuple of tool function and
            a dict in JSON Schema format to describe the function.

        .. note:: The description of the function and arguments are extracted
         from its docstring automatically, which should be well-formatted in
         **Google style**. Otherwise, their descriptions in the returned
         dictionary will be empty.

        .. tips::
         1. The name of the service function should be self-explanatory,
         so that the agent can understand the function and use it properly.
         2. The typing of the arguments should be provided when defining
         the function (e.g. `def func(a: int, b: str, c: bool)`), so that
         the agent can specify the arguments properly.

        Example:

            .. code-block:: python

                def bing_search(query: str, api_key: str, num_results=10):
                    \"""Search the query in Bing search engine.

                        Args:
                            query: (`str`):
                                The string query to search.
                            api_key: (`str`):
                                The API key for Bing search.
                            num_results: (`int`, optional):
                                The number of results to return, default to 10.
                    \"""

                    # ... Your implementation here ...
                    return ServiceResponse(status, output)

        """

        # TODO: hotfix for workstation, will be removed in the future
        if isinstance(service_func, partial):
            self.add(service_func.func, **service_func.keywords)
            return

        processed_func, json_schema = ServiceToolkit.get(
            service_func,
            func_description=func_description,
            include_long_description=include_long_description,
            include_var_positional=include_var_positional,
            include_var_keyword=include_var_keyword,
            **kwargs,
        )

        # register the service function
        name = service_func.__name__
        if name in self.service_funcs and not overwrite_if_exists:
            logger.warning(
                f"Service function `{name}` already exists, "
                f"skip adding it.",
            )
        else:
            self.service_funcs[name] = ServiceFunction(
                name=name,
                original_func=service_func,
                processed_func=processed_func,
                json_schema=json_schema,
            )

    def add_mcp_servers(
        self,
        server_configs: dict,
        enable_funcs: Optional[list[str]] = None,
        disable_funcs: Optional[list[str]] = None,
    ) -> None:
        """Connect MCP servers according to the given configurations and
        add their tool functions into the toolkit.

        Args:
            server_configs (`dict`):
                A config dictionary that follows the Model Context Protocol
                specification.
            enable_funcs (`Optional[list[str]]`, defaults to `None`):
                The functions to be added into the toolkit. If `None`, all
                tool functions within the MCP servers will be added.
            disable_funcs (`Optional[list[str]]`, defaults to `None`)
                The functions that will be filtered out. If `None`, no
                tool functions will be filtered out.

        Example:
            One example for the `server_configs`:

                .. code-block:: json

                    {
                        "mcpServers": {
                            "{server1_name}": {
                                "command": "npx",
                                "args": [
                                    "-y",
                                    "@modelcontextprotocol/xxxx"
                                ]
                            },
                            "{server2_name}": {
                                "url": "http://xxx.xxx.xxx.xxx:xxxx/sse"
                            }
                        }
                    }

            Fields:
               - "mcpServers": A dictionary where each key is the server
               name and the value is its configuration.

            Field Details:
               - "command": Specifies the command to execute,
               which follows the stdio protocol for communication.
               - "args": A list of arguments to be passed to the command.
               - "url": Specifies the server's URL, which follows the
               Server-Sent Events (SSE) protocol for data transmission.
        """
        # Check arguments for enable_funcs and disabled_funcs
        if enable_funcs is not None and disable_funcs is not None:
            assert isinstance(enable_funcs, list) and all(
                isinstance(_, str) for _ in enable_funcs
            ), (
                "Enable functions should be a list of strings, but got "
                f"{enable_funcs}."
            )

            assert isinstance(disable_funcs, list) and all(
                isinstance(_, str) for _ in disable_funcs
            ), (
                "Disable functions should be a list of strings, but got "
                f"{disable_funcs}."
            )
            intersection = set(enable_funcs).intersection(set(disable_funcs))
            assert len(intersection) == 0, (
                f"The functions in enable_funcs and disable_funcs "
                f"should not overlap, but got {intersection}."
            )

        new_servers = [
            MCPSessionHandler(name, config)
            for name, config in server_configs["mcpServers"].items()
        ]

        # register the service function
        for sever in new_servers:
            added_funcs = []
            for tool in sync_exec(sever.list_tools):
                name = tool.name

                # Skip the functions that are not in the enable_funcs if
                # enable_funcs is not None
                if enable_funcs is not None and name not in enable_funcs:
                    continue

                # Skip the disabled functions
                if disable_funcs is not None and name in disable_funcs:
                    continue

                # Skip the existing functions
                if name in self.service_funcs:
                    logger.warning(
                        f"Service function `{name}` already exists, "
                        f"skip adding it.",
                    )
                    continue

                added_funcs.append(name)

                json_schema = {
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
                self.service_funcs[tool.name] = ServiceFunction(
                    name=tool.name,
                    original_func=partial(
                        sync_exec,
                        sever.execute_tool,
                    ),
                    processed_func=partial(
                        sync_exec,
                        sever.execute_tool,
                        tool.name,
                    ),
                    json_schema=json_schema,
                )

            logger.info(
                f"Added tool functions from MCP server `{sever.name}`: "
                f"{', '.join(added_funcs)}.",
            )

    @property
    def json_schemas(self) -> dict:
        """The json schema descriptions of the processed service funcs."""
        return {k: v.json_schema for k, v in self.service_funcs.items()}

    @property
    def tools_calling_format(self) -> str:
        """The calling format of the tool functions."""
        return self._tools_calling_format

    @property
    def tools_instruction(self) -> str:
        """The instruction of the tool functions."""
        tools_prompt = []
        for i, (func_name, desc) in enumerate(self.json_schemas.items()):
            func_desc = desc["function"]["description"]
            args_desc = desc["function"]["parameters"]["properties"]

            args_list = [f"{i + 1}. {func_name}: {func_desc}"]
            for args_name, args_info in args_desc.items():
                if "type" in args_info:
                    args_line = (
                        f'\t{args_name} ({args_info["type"]}): '
                        f'{args_info.get("description", "")}'
                    )
                else:
                    args_line = (
                        f'\t{args_name}: {args_info.get("description", "")}'
                    )
                args_list.append(args_line)

            func_prompt = "\n".join(args_list)
            tools_prompt.append(func_prompt)

        tools_description = "\n".join(tools_prompt)

        if tools_description == "":
            # No tools are provided
            return ""
        else:
            return self._tools_instruction_format.format_map(
                {"function_prompt": tools_description},
            )

    def _check_tool_use_block(
        self,
        tool_call: ToolUseBlock,
    ) -> None:
        """Parsing and check the format of the function calling text."""
        # --- Semantic Check: if the input is a list of dicts with
        # required fields
        if not isinstance(tool_call, dict):
            # Not list, raise parsing error
            raise JsonParsingError(
                f"tool_call should be a dict, but got {tool_call}.",
            )

        # --- Check the format of the command ---
        if "name" not in tool_call:
            raise FunctionCallFormatError(
                "The field 'name' is required in the dictionary.",
            )

        # Obtain the service function
        func_name = tool_call["name"]

        # Cannot find the service function
        if func_name not in self.service_funcs:
            raise FunctionNotFoundError(
                f"Cannot find a tool function named `{func_name}`.",
            )

        # If it is json(str) convert to json(dict)
        if isinstance(tool_call["input"], str):
            try:
                tool_call["input"] = json.loads(tool_call["input"])
            except json.decoder.JSONDecodeError:
                logger.debug(
                    f"Fail to parse the arguments: {tool_call['input']}",
                )

        # Type error for the arguments
        if not isinstance(tool_call["input"], dict):
            raise FunctionCallFormatError(
                "Except a dictionary for the arguments, but got "
                f"{type(tool_call['input'])} instead.",
            )

        # Leaving the type checking and required checking to the runtime
        # error reporting during execution

    def _execute_func(self, tool_call: ToolUseBlock) -> ToolResultBlock:
        """Execute the function with the arguments.

        Args:
            tool_call (`ToolUseBlock`):
                A tool use block indicating the called function and arguments.

        Returns:
            `ToolResultBlock`:
                The result block of the function execution.
        """

        func = self.service_funcs[tool_call["name"]]
        kwargs = tool_call["input"]

        try:
            func_res = func.processed_func(**kwargs)
        except Exception as e:
            func_res = ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=str(e),
            )

        return ToolResultBlock(
            type="tool_result",
            id=tool_call["id"],
            name=tool_call["name"],
            output=func_res.content,
        )

    def parse_and_call_func(
        self,
        tool_calls: Union[ToolUseBlock, list[ToolUseBlock]],
        tools_api_mode: bool = False,
        raise_exception: bool = False,
    ) -> Msg:
        """Execute the tool functions with the given arguments, and return the
        execution results.

        Args:
            tool_calls (`Union[ToolUseBlock, list[ToolUseBlock]]`):
                A or a list of tool use blocks indicating the function calls.
            tools_api_mode (`bool`, defaults to `False`):
                If `False`, the execution results will be combined into a
                string content. If `True`, the results will be `ContentBlock`
                objects.
            raise_exception (`bool`, defaults to `False`):
                Whether to raise exceptions when the function call fails. If
                set to `False`, the error message will be wrapped in the
                `ToolResultBlock` and returned.

        Returns:
            `list[ToolResultBlock]`:
                A list of tool result blocks indicating the results of the
                function calls.
        """
        if isinstance(tool_calls, dict):
            tool_calls = [tool_calls]

        assert isinstance(tool_calls, list) and all(
            isinstance(_, dict) for _ in tool_calls
        ), f"tool_calls should be a list of dict, but got {tool_calls}."

        tool_results: list[ContentBlock] = []
        for tool_call in tool_calls:
            try:
                # --- Step 1: Parse the text according to the tools_call_format
                self._check_tool_use_block(tool_call)

                # --- Step 2: Call the service function ---
                tool_results.append(
                    self._execute_func(tool_call),
                )

            except FunctionCallError as e:
                if raise_exception:
                    raise e from None

                tool_results.append(
                    ToolResultBlock(
                        type="tool_result",
                        id=str(tool_call["id"]),
                        name=str(tool_call["name"]),
                        output=str(e),
                    ),
                )

        if not tools_api_mode:
            # When you're managing tools calling prompt manually, the blocks
            # should be transformed into string format. So that in the format
            # function (both chat and multi-agent scenarios) it will be
            # displayed as a string.

            content = "\n".join(
                [
                    self._tools_execution_format.format(
                        index=i + 1,
                        function_name=_["name"],
                        arguments=json.dumps(
                            tool_calls[i]["input"],
                            ensure_ascii=False,
                        ),
                        result=_["output"],
                    )
                    for i, _ in enumerate(tool_results)
                ],
            )

            return Msg(
                "system",
                content=content,
                role="system",
            )
        else:
            # When you're using tools API, you need to keep the blocks in the
            # content. So that in the format function, the blocks will be
            # formatted to the required dictionary format.
            return Msg(
                "system",
                content=tool_results,
                role="system",
            )

    @staticmethod
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
                    ServiceToolkit._remove_title_field(prop)

        # items
        if "items" in schema and isinstance(schema["items"], dict):
            ServiceToolkit._remove_title_field(schema["items"])

        # additionalProperties
        if "additionalProperties" in schema and isinstance(
            schema["additionalProperties"],
            dict,
        ):
            ServiceToolkit._remove_title_field(
                schema["additionalProperties"],
            )

    @classmethod
    def get(
        cls,
        service_func: Callable[..., Any],
        func_description: Optional[str] = None,
        include_long_description: bool = True,
        include_var_positional: bool = False,
        include_var_keyword: bool = False,
        **kwargs: Any,
    ) -> Tuple[Callable[..., Any], dict]:
        """Convert a service function into a tool function that agent can
        use, and generate a dictionary in JSON Schema format that can be
        used in OpenAI API directly. While for open-source model, developers
        should handle the conversation from json dictionary to prompt.

        Args:
            service_func (`Callable[..., Any]`):
                The service function to be called.
            func_description (`Optional[str]`, defaults to `None`)
                The function description. If not provided, the description
                will be extracted from the docstring automatically.
            include_long_description (`bool`, defaults to `True`):
                When extracting function description from the docstring, if
                the long description will be included.
            include_var_positional (`bool`, defaults to `False`):
                Whether to include the variable positional arguments (`*args`)
                in the function schema.
            include_var_keyword (`bool`, defaults to `False`):
                Whether to include the variable keyword arguments (`**kwargs`)
                in the function schema.
            **kwargs (`Any`):
                The keyword arguments that preset by developers, which will
                not be exposed to the agent

        Returns:
            `Tuple(Callable[..., Any], dict)`:
                A tuple of tool function and a dict in JSON Schema format to
                describe the function.

        .. note:: The description of the function and arguments are extracted
         from its docstring automatically, which should be well-formatted in
         **Google style**. Otherwise, their descriptions in the returned
         dictionary will be empty.

        .. tips::
         1. The name of the service function should be self-explanatory,
         so that the agent can understand the function and use it properly.
         2. The typing of the arguments should be provided when defining
         the function (e.g. `def func(a: int, b: str, c: bool)`), so that
         the agent can specify the arguments properly.

        Example:

            .. code-block:: python

                def bing_search(query: str, api_key: str, num_results: int=10):
                    '''Search the query in Bing search engine.

                    Args:
                        query (`str`):
                            The string query to search.
                        api_key (`str`):
                            The API key for Bing search.
                        num_results (`int`):
                            The number of results to return, default to 10.
                    '''
                    pass

        """
        # Get the function for agent to use
        tool_func = partial(service_func, **kwargs)

        docstring = parse(service_func.__doc__)
        params_docstring = {
            _.arg_name: _.description for _ in docstring.params
        }

        # Function description
        if func_description is None:
            descriptions = []
            if docstring.short_description is not None:
                descriptions.append(docstring.short_description)

            if (
                include_long_description
                and docstring.long_description is not None
            ):
                descriptions.append(docstring.long_description)

            if len(descriptions) > 0:
                func_description = "\n\n".join(descriptions)

        fields = {}
        for name, param in inspect.signature(service_func).parameters.items():
            if name in kwargs or name in ["self", "cls"]:
                # Skip the given keyword arguments and self/cls
                continue

            # Handle `**kwargs`
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                if not include_var_keyword:
                    continue
                fields[name] = (
                    Dict[str, Any]
                    if param.annotation == inspect.Parameter.empty
                    else Dict[str, param.annotation],  # type: ignore
                    Field(
                        description=params_docstring.get(
                            f"**{name}",
                            params_docstring.get(name, None),
                        ),
                        default={}
                        if param.default is param.empty
                        else param.default,
                    ),
                )
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                if not include_var_positional:
                    continue
                fields[name] = (
                    list[Any]
                    if param.annotation == inspect.Parameter.empty
                    else list[param.annotation],  # type: ignore
                    Field(
                        description=params_docstring.get(
                            f"*{name}",
                            params_docstring.get(name, None),
                        ),
                        default=[]
                        if param.default is param.empty
                        else param.default,
                    ),
                )
            else:
                fields[name] = (
                    Any
                    if param.annotation == inspect.Parameter.empty
                    else param.annotation,
                    Field(
                        description=params_docstring.get(name, None),
                        default=...
                        if param.default is param.empty
                        else param.default,
                    ),
                )

        base_model = create_model(
            "_StructuredOutputDynamicClass",
            __config__=ConfigDict(arbitrary_types_allowed=True),
            **fields,
        )
        json_schema = base_model.model_json_schema()

        # Remove the title from the json schema
        ServiceToolkit._remove_title_field(json_schema)

        # Overwrite the function description if provided
        extracted_func_description = (
            func_description
            if func_description
            else json_schema.pop("description", None)
        )

        func_schema: dict = {
            "type": "function",
            "function": {
                "name": service_func.__name__,
                "parameters": json_schema,
            },
        }

        if extracted_func_description not in [None, ""]:
            func_schema["function"]["description"] = extracted_func_description

        return tool_func, func_schema
