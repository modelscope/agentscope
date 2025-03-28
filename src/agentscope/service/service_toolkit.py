# -*- coding: utf-8 -*-
"""Service Toolkit for service function usage."""
import json
from functools import partial
import inspect
from typing import (
    Callable,
    Any,
    Tuple,
    Union,
    Optional,
    Literal,
    get_args,
    get_origin,
    Dict,
)
from loguru import logger

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

try:
    from docstring_parser import parse
except ImportError:
    parse = None


def _get_type_str(cls: Any) -> Optional[Union[str, list]]:
    """Get the type string."""
    type_str = None
    if hasattr(cls, "__origin__"):
        # Typing class
        if cls.__origin__ is Union:
            type_str = [_get_type_str(_) for _ in get_args(cls)]
            clean_type_str = [_ for _ in type_str if _ != "null"]
            if len(clean_type_str) == 1:
                type_str = clean_type_str[0]
        elif cls.__origin__ in [list, tuple]:
            type_str = "array"
        else:
            type_str = str(cls.__origin__)
    else:
        # Normal class
        if cls is str:
            type_str = "string"
        elif cls in [float, int, complex]:
            type_str = "number"
        elif cls is bool:
            type_str = "boolean"
        elif cls in [list, tuple]:
            type_str = "array"
        elif cls is None.__class__:
            type_str = "null"
        elif cls is Any:
            type_str = "Any"
        else:
            type_str = cls.__name__

    return type_str  # type: ignore[return-value]


class ServiceFunction:
    """The service function class."""

    name: str
    """The name of the service function."""

    original_func: Callable
    """The original function before processing."""

    processed_func: Callable
    """The processed function that can be called by the model directly."""

    json_schema: dict
    """The JSON schema description of the service function."""

    require_args: bool
    """Whether calling the service function requests arguments. Some arguments
    may have default values, so it is not necessary to provide all arguments.
    """

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
        self.json_schema = json_schema

        self.require_args = (
            len(
                json_schema["function"]
                .get("parameters", {})
                .get("required", []),
            )
            != 0
        )


class ServiceToolkit:
    """A service toolkit class that turns service function into string
    prompt format."""

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

    def add(self, service_func: Callable[..., Any], **kwargs: Any) -> None:
        """Add a service function to the toolkit, which will be processed into
        a tool function that can be called by the model directly, and
        registered in processed_funcs.

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
            3. The execution results should be a `ServiceResponse` object.

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
            **kwargs,
        )

        # register the service function
        name = service_func.__name__
        if name in self.service_funcs:
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

    def add_mcp_servers(self, server_configs: Dict) -> None:
        """
        Add mcp servers to the toolkit.

        Parameters:
            server_configs (Dict): A dictionary containing the configuration
                for MCP servers. The configuration follows the Model Context
                Protocol specification and can be defined in TypeScript,
                but is available as JSON Schema for wider compatibility.

                Fields:
                   - "mcpServers": A dictionary where each key is the server
                   name and the value is its configuration.

                Field Details:
                   - "command": Specifies the command to execute,
                   which follows the stdio protocol for communication.
                   - "args": A list of arguments to be passed to the command.
                   - "url": Specifies the server's URL, which follows the
                   Server-Sent Events (SSE) protocol for data transmission.

                Example:
                    configs = {
                        "mcpServers": {
                            "xxxx": {
                                "command": "npx",
                                "args": [
                                    "-y",
                                    "@modelcontextprotocol/xxxx"
                                ]
                            },
                            "yyyy": {
                                "url": "http://xxx.xxx.xxx.xxx:xxxx/sse"
                            }
                        }
                    }
        """
        new_servers = [
            MCPSessionHandler(name, config)
            for name, config in server_configs["mcpServers"].items()
        ]

        # register the service function
        for sever in new_servers:
            for tool in sync_exec(sever.list_tools):
                name = tool.name
                if name in self.service_funcs:
                    logger.warning(
                        f"Service function `{name}` already exists, "
                        f"skip adding it.",
                    )
                else:
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

    @classmethod
    def get(
        cls,
        service_func: Callable[..., Any],
        **kwargs: Any,
    ) -> Tuple[Callable[..., Any], dict]:
        """Convert a service function into a tool function that agent can
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

            .. code-block:: python

                def bing_search(query: str, api_key: str, num_results: int=10):
                    '''Search the query in Bing search engine.

                    Args:
                        query (str):
                            The string query to search.
                        api_key (str):
                            The API key for Bing search.
                        num_results (int):
                            The number of results to return, default to 10.
                    '''
                    pass


        """
        # Get the function for agent to use
        tool_func = partial(service_func, **kwargs)

        # Obtain all arguments of the service function
        argsspec = inspect.getfullargspec(service_func)

        # Construct the mapping from arguments to their typings
        if parse is None:
            raise ImportError(
                "Missing required package `docstring_parser`"
                "Please install it by "
                "`pip install docstring_parser`.",
            )

        docstring = parse(service_func.__doc__)

        # Function description
        short_description = docstring.short_description or ""
        long_description = docstring.long_description or ""
        func_description = "\n\n".join([short_description, long_description])

        # The arguments that requires the agent to specify
        # to support class method, the self args are deprecated
        args_agent = set(argsspec.args) - set(kwargs.keys()) - {"self", "cls"}

        # Check if the arguments from agent have descriptions in docstring
        args_description = {
            _.arg_name: _.description for _ in docstring.params
        }

        # Prepare default values
        if argsspec.defaults is None:
            args_defaults = {}
        else:
            args_defaults = dict(
                zip(
                    reversed(argsspec.args),
                    reversed(argsspec.defaults),  # type: ignore
                ),
            )

        args_required = sorted(
            list(set(args_agent) - set(args_defaults.keys())),
        )

        # Prepare types of the arguments, remove the return type
        args_types = {
            k: v for k, v in argsspec.annotations.items() if k != "return"
        }

        # Prepare argument dictionary
        properties_field = {}
        for key in args_agent:
            arg_property = {}
            # type
            if key in args_types:
                try:
                    required_type = _get_type_str(args_types[key])
                    arg_property["type"] = required_type
                except Exception:
                    logger.warning(
                        f"Fail and skip to get the type of the "
                        f"argument `{key}`.",
                    )

                # For Literal type, add enum field
                if get_origin(args_types[key]) is Literal:
                    arg_property["enum"] = list(args_types[key].__args__)

            # description
            if key in args_description:
                arg_property["description"] = args_description[key]

            # default
            if key in args_defaults and args_defaults[key] is not None:
                arg_property["default"] = args_defaults[key]

            properties_field[key] = arg_property

        # Construct the JSON Schema for the service function
        func_dict = {
            "type": "function",
            "function": {
                "name": service_func.__name__,
                "description": func_description.strip(),
                "parameters": {
                    "type": "object",
                    "properties": properties_field,
                    "required": args_required,
                },
            },
        }

        return tool_func, func_dict
