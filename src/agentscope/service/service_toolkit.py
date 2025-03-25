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
    List,
    Dict,
)
from loguru import logger
import requests

from ..exception import (
    JsonParsingError,
    FunctionNotFoundError,
    FunctionCallFormatError,
    FunctionCallError,
)
from .service_response import ServiceResponse, ServiceExecStatus

from .mcp_manager import MCPSessionHandler, sync_exec
from ..message import Msg
from ..models import ModelWrapperBase

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
        "   [STATUS]: {status}\n"
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

    def _parse_and_check_text(  # pylint: disable=too-many-branches
        self,
        cmd: Union[list[dict], str],
    ) -> List[dict]:
        """Parsing and check the format of the function calling text."""

        # Record the error
        error_info = []

        if isinstance(cmd, str):
            # --- Syntax check: if the input can be loaded by JSON
            try:
                processed_text = cmd.strip()

                # complete "[" and "]" if they are missing
                index_start = processed_text.find("[")
                index_end = processed_text.rfind("]")

                if index_start == -1:
                    index_start = 0
                    error_info.append('Missing "[" at the beginning.')

                if index_end == -1:
                    index_end = len(processed_text)
                    error_info.append('Missing "]" at the end.')

                # remove the unnecessary prefix before "[" and suffix after "]"
                processed_text = processed_text[
                    index_start : index_end + 1  # noqa: E203
                ]

                cmds = json.loads(processed_text)
            except json.JSONDecodeError:
                # Since we have processed the text, here we can only report
                # the JSON parsing error
                raise JsonParsingError(
                    f"Except a list of dictionaries in JSON format, "
                    f"like: {self.tools_calling_format}",
                ) from None
        else:
            cmds = cmd

        # --- Semantic Check: if the input is a list of dicts with
        # required fields

        # Handle the case when the input is a single dictionary
        if isinstance(cmds, dict):
            # The error info is already recorded in error_info
            cmds = [cmds]

        if not isinstance(cmds, list):
            # Not list, raise parsing error
            raise JsonParsingError(
                f"Except a list of dictionaries in JSON format "
                f"like: {self.tools_calling_format}",
            )

        # --- Check the format of the command ---
        for sub_cmd in cmds:
            if not isinstance(sub_cmd, dict):
                raise JsonParsingError(
                    f"Except a JSON list of dictionaries, but got"
                    f" {type(sub_cmd)} instead.",
                )

            if "name" not in sub_cmd:
                raise FunctionCallFormatError(
                    "The field 'name' is required in the dictionary.",
                )

            # Obtain the service function
            func_name = sub_cmd["name"]

            # Cannot find the service function
            if func_name not in self.service_funcs:
                raise FunctionNotFoundError(
                    f"Cannot find a tool function named `{func_name}`.",
                )

            # If it is json(str) convert to json(dict)
            if isinstance(sub_cmd["arguments"], str):
                try:
                    sub_cmd["arguments"] = json.loads(sub_cmd["arguments"])
                except json.decoder.JSONDecodeError:
                    logger.debug(
                        f"Fail to parse the argument: {sub_cmd['arguments']}",
                    )

            # Type error for the arguments
            if not isinstance(sub_cmd["arguments"], dict):
                raise FunctionCallFormatError(
                    "Except a dictionary for the arguments, but got "
                    f"{type(sub_cmd['arguments'])} instead.",
                )

            # Leaving the type checking and required checking to the runtime
            # error reporting during execution
        return cmds

    def _execute_func(self, cmds: List[dict]) -> str:
        """Execute the function with the arguments.

        Args:
            cmds (`List[dict]`):
                A list of dictionaries, where each dictionary contains the
                name of the function and its arguments, e.g. {"name": "func1",
                "arguments": {"arg1": 1, "arg2": 2}}.

        Returns:
            `str`: The prompt of the execution results.
        """

        execute_results = []
        for i, cmd in enumerate(cmds):
            service_func = self.service_funcs[cmd["name"]]
            kwargs = cmd.get("arguments", {})

            # Execute the function
            try:
                func_res = service_func.processed_func(**kwargs)
            except Exception as e:
                func_res = ServiceResponse(
                    status=ServiceExecStatus.ERROR,
                    content=str(e),
                )

            status = (
                "SUCCESS"
                if func_res.status == ServiceExecStatus.SUCCESS
                else "FAILED"
            )

            arguments = [f"{k}: {v}" for k, v in kwargs.items()]

            execute_res = self._tools_execution_format.format_map(
                {
                    "index": i + 1,
                    "function_name": cmd["name"],
                    "arguments": "\n\t\t".join(arguments),
                    "status": status,
                    "result": func_res.content,
                },
            )

            execute_results.append(execute_res)

        execute_results_prompt = "\n".join(execute_results)

        return execute_results_prompt

    def parse_and_call_func(
        self,
        text_cmd: Union[list[dict], str],
        raise_exception: bool = False,
    ) -> Msg:
        """Parse, check the text and call the function."""

        try:
            # --- Step 1: Parse the text according to the tools_call_format
            cmds = self._parse_and_check_text(text_cmd)

            # --- Step 2: Call the service function ---

            execute_results_prompt = self._execute_func(cmds)

        except FunctionCallError as e:
            # Catch the function calling error that can be handled by
            # the model
            if raise_exception:
                raise e from None

            execute_results_prompt = str(e)

        return Msg("system", execute_results_prompt, "system")

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

    def search_mcp_server(
        self,
        function_keywords: str,
        size: int = 20,
        **kwargs: Any,
    ) -> list[dict]:
        """
        Search for appropriate MCP server with function
        Depend on npm Public Registry API:
        https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md
        https://itnext.io/increasing-an-npm-packages-search-score-fb557f859300
        It is possible to searching MCP with specific authors, maintainer,
        scope, etc. Deatils can be found in the above websites.

        Args:
            function_keywords (str): Keywords of the desired function;
            size (int): Size of the search results;
            kwargs (Any): Additional keyword for API search, such as
                quality, popularity, and maintenance score.
        Returns:
            `list[dict]`: List of MCP servers with description`

        An example of the return is
        [
          {
            "Name": "@modelcontextprotocol/server-github",
            "Description": "MCP server for using the GitHub API",
            "Keywords": ["mcp"],
            "Downloads": {"monthly": 53055,}
          },
          ...
        ]
        """
        search_url = "https://registry.npmjs.org/-/v1/search"
        if "mcp+server" not in function_keywords.lower():
            # make search more specific on MCP servers
            function_keywords += "+mcp+server"

        params = {
            "text": function_keywords,
            "size": size,
        }
        params.update(kwargs)
        response = requests.get(search_url, params=params)

        def rule_base_filter(package: dict) -> bool:
            """Filter those packages that are not MPC server"""
            pkg = package["package"]
            if pkg["name"] == "@modelcontextprotocol/sdk":
                return False
            elif (
                "mcp" in pkg["keywords"]
                or "MCP" in pkg["keywords"]
                or "modelcontextprotocol" in pkg["keywords"]
            ):
                return True
            elif (
                "@modelcontextprotocol" in pkg["name"]
                or "mcp" in pkg["description"]
                or "MCP" in pkg["description"]
                or "model context protocol" in pkg["description"].lower()
            ):
                return True
            else:
                return False

        return_results = []
        if response.status_code == 200:
            results = response.json()
            for package in results["objects"]:
                if not rule_base_filter(package):
                    continue
                pkg = package["package"]
                return_results.append(
                    {
                        "Name": pkg["name"],
                        "Keywords": pkg["keywords"],
                        "Description": pkg["description"],
                        "Downloads": package["downloads"],
                        "Publisher": pkg["publisher"],
                    },
                )
        return return_results

    def search_and_add_mcp_server(
        self,
        task: str,
        model: ModelWrapperBase,
        max_retries: int = 3,
    ) -> None:
        """
        Automatically search for appropriate MCP server with the given task.
        Args:
            task (str): Task description.
            model (ModelWrapperBase): LLM model to analysis the task and choose
                appropriate MCP server.
            max_retries (int): max number of retries, for example, for LLM
                choosing invalid package names.
        """
        search_sys_prompt = (
            "You are a helpful assistant that can output a keyword"
            "to search for software packages that can help solve the task."
            "ONLY output ONE keyword."
        )
        search_usr_prompt = (
            f"Given task: {task}. \n"
            f"What are the keywords to search for helpful software packages?"
        )
        msgs = model.format(
            Msg("system", search_sys_prompt, role="system"),
            Msg("user", search_usr_prompt, role="user"),
        )
        function_keywords = model(msgs).text

        avaiable_choices = self.search_mcp_server(function_keywords)
        logger.info(f"Seach function keywords: {function_keywords}")
        logger.info(f"Candidate functions: {avaiable_choices}")
        choose_sys_prompt = (
            "Given the available software packages and "
            "the description of task, you need to determine what is the most"
            "appropriate MCP Server to help solve the task based on the "
            "description, keyword and download statistics information."
            "Usually, a package is a MCP server software package  if it has "
            "at least one of the following properties: "
            "1. There are keywords 'mcp' or '@modelcontextprotocol' or "
            "'server' in their Name."
            "2. There are keywords 'mcp' or 'Model Context protocol' "
            "in its Description or Keywords."
            "\n# Requirements:"
            "1. Make choice based on the name, description and keywords."
            "2. The selected package must be MCP server."
            "ONLY output ONE Name of the package.\n\n"
        )
        choose_usr_prompt = (
            f"Available software packages:\n {avaiable_choices}\n"
            f"Given task: {task} \nWhat is the most appropriate MCP server?\n"
            "ONLY output ONE Name of the package.\n\n# OUTPUT FORMAT:\n"
            "THE_PACKAGE_NAME"
        )
        init_msgs = [
            Msg("system", choose_sys_prompt, role="system"),
            Msg("user", choose_usr_prompt, role="user"),
        ]
        for _ in range(max_retries):
            try:
                msgs = model.format(*init_msgs)
                function_name = model(msgs).text
                init_msgs.append(Msg("system", function_name, role="system"))
                logger.info(f"Model chooses function: {function_name}")
                chosen_function = {}
                for pkg in avaiable_choices:
                    if pkg["Name"] == function_name:
                        chosen_function = pkg
                if len(chosen_function) == 0:
                    raise ValueError(
                        "Name does not match any of the available choices.",
                    )
            except Exception as e:
                init_msgs.append(
                    Msg(
                        "user",
                        f"Encounter the following error {e}",
                        "user",
                    ),
                )

        # build an instance
        config = {
            "command": "npx",
            "args": ["-y", chosen_function["Name"]],
            # TODO: how to know what env variable are required?
        }
        self.add_mcp_servers(
            server_configs={
                "mcpServers": {chosen_function["Name"]: config},
            },
        )


class ServiceFactory:
    """A service factory class that turns service function into string
    prompt format."""

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
        logger.warning(
            "The service factory will be deprecated in the future."
            " Try to use the `ServiceToolkit` class instead.",
        )

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
        func_description = "\n".join([short_description, long_description])

        # The arguments that requires the agent to specify
        # we remove the self argument, for class methods
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
                "description": func_description,
                "parameters": {
                    "type": "object",
                    "properties": properties_field,
                    "required": args_required,
                },
            },
        }

        return tool_func, func_dict
