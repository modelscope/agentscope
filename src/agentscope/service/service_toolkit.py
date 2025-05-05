# -*- coding: utf-8 -*-
"""Service Toolkit for service function usage."""
import json
import os
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
from .mcp_search_utils import (
    search_mcp_server,
    model_free_recommend_mcp,
    build_mcp_server_config,
    CHOOSE_MCP_PROMPT,
    HUMAN_CHOOSE_PROMPT,
)
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

    def __init__(
        self,
        mcp_search_allow: bool = False,
        auto_install_mcp: bool = False,
        mcp_search_url: str = "https://registry.npmjs.org/-/v1/search",
        mcp_detail_url: str = "https://registry.npmjs.org",
        mcp_search_candidates: int = 20,
    ) -> None:
        """Initialize the service toolkit with a list of service functions.
        Args:
            mcp_search_allow (bool): Whether to enable
                searching for new MCP server online. Defaults to False.
            auto_install_mcp (bool): Whether to encourage agent
                processing MCP server install without human intervention.
                Defaults to False.
            mcp_search_url (str): The URL of the MCP server search API
            mcp_detail_url (str): The URL of the MCP server detail API
            mcp_search_candidates (int): the number of candidates return
                by the MCP server search API. Defaults to 20.
        """
        self.service_funcs = {}

        if mcp_search_allow:
            self.add(
                self.search_new_tool,
                search_url=mcp_search_url,
                mcp_search_candidates=mcp_search_candidates,
            )
            self.add(self.remove_auto_added_tool)
            self.add(
                self.get_mcp_server_config_template,
                query_detail_api=mcp_detail_url,
            )
            self.add(self.install_mcp_server_for_new_tools)
        self.auto_install_mcp = auto_install_mcp
        self.auto_added_mcp_servers = []

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

    def add_mcp_servers(
        self,
        server_configs: Dict,
    ) -> tuple[list[MCPSessionHandler], list[dict]]:
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
            Return:
                `tuple[list[MCPSessionHandler], list[dict]]`: A list of
                    MCP session handlers and a list of new functions/tools
        """
        new_servers = [
            MCPSessionHandler(name, config)
            for name, config in server_configs["mcpServers"].items()
        ]
        new_functions = []

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
                    new_functions.append(json_schema)

        return new_servers, new_functions

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

    def search_new_tool(
        self,
        desired_functionality: str,
        mcp_search_candidates: int = 20,
        search_url: str = "https://registry.npmjs.org/-/v1/search",
    ) -> ServiceResponse:
        """
        Automatically search for appropriate MCP servers as tools to
        solve a task.
        Args:
            desired_functionality (str):
                One or two keywords for the desired functionality/software.
                ONLY ONE OR TWO KEYWORD as the functionality.
                Examples: "web search", "file search", "GitHub access"
            mcp_search_candidates: the maximum number of MCP servers to return.
            search_url (str): URL for Searching appropriate MCP server.
                    By Default, it depends on npm Public Registry API.

        Return:
            `ServiceResponse` : return whether success or fail in searching.
                If success and self.auto_install_mcp=True, the content will be
                a next_step_instruction listing all available MCP servers and
                desired functionality.
                If success and self.auto_install_mcp=False, the content will be
                1) dictionary of available MCP servers 2) a model free
                recommendation 3) next_step_instruction reminding to request
                human instruction.
        """
        try:
            all_choices = search_mcp_server(
                desired_functionality,
                size=mcp_search_candidates,
                search_url=search_url,
            )
            model_free_recommend = model_free_recommend_mcp(
                desired_functionality,
                all_choices,
            )

            if self.auto_install_mcp:
                return_content = {
                    "next_step_instruction": CHOOSE_MCP_PROMPT.format_map(
                        {
                            "available_choices": json.dumps(
                                all_choices,
                                indent=4,
                                ensure_ascii=False,
                            ),
                            "functionality": desired_functionality,
                        },
                    ),
                }
            else:
                return_content = {
                    "mcp_server_choices": json.dumps(
                        all_choices,
                        indent=2,
                        ensure_ascii=False,
                    ),
                    "model_free_recommend": json.dumps(
                        model_free_recommend,
                        indent=2,
                        ensure_ascii=False,
                    ),
                    "next_step_instruction": HUMAN_CHOOSE_PROMPT,
                }
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=return_content,
            )
        except Exception as e:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content="Fail to search for MCP server. " f"Error:\n {e}",
            )

    def get_mcp_server_config_template(
        self,
        mcp_package_name: str,
        query_detail_api: str = "https://registry.npmjs.org",
    ) -> ServiceResponse:
        """
        Prepare MCP server config template for installing MCP servers.
        Before installing any MCP server with tools, you MUST call this
        function to obtain appropriate MCP server config template.
        Args:
            mcp_package_name (str): the name of the MCP server to be installed;
            query_detail_api (str): the URL to obtained details (more
                specifically, the README information) of the MCP server;

        Returns:
            `ServiceResponse` : return whether success or fail for obtaining
                appropriate MCP server config template. If success, the content
                of the `ServiceResponse` will be a template in JSON format.
                If fail, the user is expected to check the website manually.
        """
        try:
            package_config = build_mcp_server_config(
                mcp_package_name,
                query_detail_api,
            )
        except Exception as e:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content="Fail to get MCP server config template. "
                f"Error:\n {e}",
            )

        return_prompt = (
            f"{json.dumps(package_config, indent=4, ensure_ascii=False)}"
        )
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=return_prompt,
        )

    def install_mcp_server_for_new_tools(
        self,
        mcp_config_or_path: Union[str, dict],
    ) -> ServiceResponse:
        """
        Install the MCP server for a set of new tool.
        Before calling this function, make sure the MCP server config is ready,
        either as JSON string or as JSON file.
        Args:
            mcp_config_or_path (Union[str, dict]): A dictionary, or
                a string in JSON format, or a path to the MCP server config.
                For example,
                1) if a str, it can be like
                '{"mcpServers": {"xxxx-mcp": {"command": "npx", "args": ["-y", "xxxx-mcp@0.0.1"], "env": {"API_KEY": "your-api-key"}}}}'
                # pylint:disable=line-too-long # noqa: E501
                2) If it is a file path, it should be like'./xxx.json'

        Return:
            `ServiceResponse` : return whether success or fail in installing
        """
        try:
            if isinstance(mcp_config_or_path, dict):
                mcp_config = mcp_config_or_path
            elif os.path.exists(mcp_config_or_path):
                with open(mcp_config_or_path, "r", encoding="utf-8") as f:
                    mcp_config = json.load(f)
            else:
                mcp_config = json.loads(mcp_config_or_path)
        except (json.JSONDecodeError, TypeError):
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=f"Input ({mcp_config_or_path}) must be a dict or "
                "a string in JSON format or a file path pointing to "
                "a JSON file ",
            )
        try:
            new_servers, new_functions = self.add_mcp_servers(
                server_configs=mcp_config,
            )
            self.auto_added_mcp_servers += new_servers
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content="Successfully installed MCP servers with following "
                f"tools.\n {new_functions}",
            )
        except Exception as e:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content="Failed to add new MCP servers with tools. "
                f"Error:\n {e}",
            )

    def remove_auto_added_tool(
        self,
        remove_tool_name: str,
    ) -> ServiceResponse:
        """
        When MCP server or tool usage errors happens, you can consider
        remove the tool to prevent the error happen again.
        Args:
            remove_tool_name (str): Name of tool to remove.

        Return:
            `ServiceResponse`:return whether success or fail in removing
                MCP server/tools.
        """
        try:
            all_remove_tools = []
            for i, server in enumerate(self.auto_added_mcp_servers):
                server_tools = sync_exec(server.list_tools)
                for tool in server_tools:
                    if tool.name == remove_tool_name:
                        # clean all service functions from the same MCP server
                        for cur_tool in server_tools:
                            self.service_funcs.pop(cur_tool.name, None)
                        all_remove_tools += [
                            tool.name for tool in server_tools
                        ]
                        # delete the server from the list
                        self.auto_added_mcp_servers.pop(i)
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=(
                    f"Successfully remove MCP server and "
                    f"tools {all_remove_tools} "
                ),
            )

        except Exception as e:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=(
                    f"Fail to remove tool {remove_tool_name}. " f"Error:\n {e}"
                ),
            )
