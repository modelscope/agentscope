# -*- coding: utf-8 -*-
# pylint: disable=R0912
""" An Enhanced Service Toolkit that can search and auto import MCP servers."""
import json
import re
import os
from typing import Any, Optional
import click
from loguru import logger
import requests
from rich.console import Console

from ..message import Msg
from ..manager import FileManager, ModelManager

from .service_toolkit import ServiceToolkit, sync_exec
from .service_response import ServiceResponse, ServiceExecStatus


class AutoServiceToolkit(ServiceToolkit):
    """
    This is an enhanced Service Toolkit that can search and
    auto import MCP servers with given functionality keywords.
    """

    llm_max_retries: int = 3

    def __init__(
        self,
        confirm_install: bool = True,
        model_free: bool = False,
        model_config_name: Optional[str] = None,
        env_file_dir: Optional[str] = None,
    ):
        """
        Initialize the AutoServiceToolkit instance.
        Args:
            confirm_install (bool): Whether the toolkit requires human confirm
                before installing MCP server
            model_free (bool): Whether the toolkit select/recommend the
                MCP server with LLM or not.
            model_config_name (str): If the toolkit is model-based,
                specify which LLM is used for selecting MCP server.
            env_file_dir (str): directory path for caching environment
                variables required by MCP servers, so that users do not need
                to enter those everytime.
        """
        super().__init__()
        if env_file_dir is None:
            env_file_dir = FileManager.get_instance().cache_dir or "./"
        self.env_file_path = os.path.join(env_file_dir, ".mcp_env.json")
        if not os.path.exists(self.env_file_path):
            with open(
                self.env_file_path,
                mode="w",
                encoding="utf-8",
            ) as env_file:
                json.dump({}, env_file)
        logger.info(f"cache env  at {self.env_file_path}")
        if not model_free and model_config_name is not None:
            model_manager = ModelManager.get_instance()
            self.model = model_manager.get_model_by_config_name(
                model_config_name,
            )
        else:
            self.model = None

        self.confirm_install = confirm_install

        if not self.confirm_install:
            logger.warning(
                "The confirm_install input is set to False, "
                "which mean the toolkit will be installed without human "
                "confirm and can have potential risk on install unverified MCP"
                "server. Besides, it is HIGHLY recommended to turn "
                "confirm_install when using model-free mode for better "
                "performance.",
            )

        self.console = Console()

        self.auto_added_mcp_servers = []

        # add the auto_add_mcp_servers
        self.add(self.search_and_add_mcp_server)
        self.add(self.remove_auto_added_mcp_server)

    @staticmethod
    def get_package_details(package_name: str) -> Optional[dict]:
        """
        Get detailed package information including environment variables.
        Args:
            package_name (str): The package name.

        Return:
            `Dict`: The package information, including all that can obtain
                from https://registry.npmjs.org
        """
        try:
            response = requests.get(
                f"https://registry.npmjs.org/{package_name}",
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching package details: {e}")
            return None

    @staticmethod
    def search_mcp_server(
        function_keywords: str,
        size: int = 20,
        **kwargs: Any,
    ) -> list[dict]:
        """
        Search for appropriate MCP server with function
        Depend on npm Public Registry API:
        https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md
        It is possible to search MCP with specific authors, maintainer,
        scope, etc. Details can be found in the above websites.
        https://itnext.io/increasing-an-npm-packages-search-score-fb557f859300

        Args:
            function_keywords (str): Keywords of the desired function;
            size (int): Size of the search results;
            kwargs (Any): Additional keyword for API search, such as
                quality, popularity, and maintenance score.
        Returns:
            `list[dict]`: List of MCP servers with description. Fields include
                name, description, keywords, and download statistics

        An example of the return is
        [
          {
            "name": "@modelcontextprotocol/server-github",
            "description": "MCP server for using the GitHub API",
            "keywords": ["mcp"],
            "downloads": {"monthly": 53055,}
          },
          ...
        ]
        """
        search_url = "https://registry.npmjs.org/-/v1/search"
        if "mcp server" not in function_keywords.lower():
            # make search more specific on MCP servers
            function_keywords += " mcp server"

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
                        "name": pkg["name"],
                        "keywords": pkg["keywords"],
                        "description": pkg["description"],
                        "downloads": package["downloads"],
                        "publisher": pkg["publisher"],
                    },
                )
        return return_results

    @staticmethod
    def _calculate_relevance_score(
        pkg: dict,
        query: str,
    ) -> float:
        """
        Calculate relevance score for a package based on various factors.
        This is used when the toolkit is in model-free mode.
        The key idea is to compute an averaged score for
            1. The overlap degree of the query(functionality) to the name,
                description and keywords:  the portion of words in query can
                be found in the name/description/keywords
            2. The downloaded score normalized by at most 1M

        Args:
            pkg (dict): Details of a package from search_mcp_server function

        Returns:
            `float`: the score of the relevance
        """

        # Get package details
        name = pkg.get("name", "").lower()
        description = pkg.get("description", "").lower()
        keywords = [k.lower() for k in pkg.get("keywords", [])]
        downloads = pkg.get("downloads", {}).get("monthly", 0)

        # Calculate text relevance
        query_terms = query.lower().split()
        name_score = sum(1 for term in query_terms if term in name) / len(
            query_terms,
        )
        desc_score = sum(
            1 for term in query_terms if term in description
        ) / len(
            query_terms,
        )
        keyword_score = sum(
            1 for term in query_terms if any(term in k for k in keywords)
        ) / len(
            query_terms,
        )

        # Normalize downloads (assuming max downloads is 1M)
        download_score = min(downloads / 1_000_000, 1.0)

        # Weighted scoring (hard-coded for current version)
        weights = {
            "name": 0.3,
            "description": 0.2,
            "keywords": 0.2,
            "downloads": 0.3,
        }

        total_score = (
            name_score * weights["name"]
            + desc_score * weights["description"]
            + keyword_score * weights["keywords"]
            + download_score * weights["downloads"]
        )

        return total_score

    def _model_free_select(
        self,
        functionality: str,
        available_choices: list[dict],
    ) -> dict:
        """
        Select the best package based on relevance score.
        Args:
            functionality (str): The description of the desired functionality
            available_choices (list[dict]): The list of details of
                searched MCP servers

        Return:
            `Dict`: The selected package (and its details)`
        """
        if not available_choices:
            return {}

        scored_packages = [
            (pkg, self._calculate_relevance_score(pkg, functionality))
            for pkg in available_choices
        ]

        # Sort by score in descending order
        scored_packages.sort(key=lambda x: x[1], reverse=True)
        return scored_packages[0][0]

    def _llm_select(
        self,
        functionality: str,
        available_choices: list[dict],
    ) -> dict:
        """
        Automatically search for appropriate MCP server with the given task.
        Args:
            functionality (str): The description of the desired functionality
            available_choices (list[dict]): The list of details of
                searched MCP servers

        Return:
            `Dict`: The selected package (and its details)`
        """
        logger.info(f"Candidate functions: {available_choices}")
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
            "ONLY output ONE name of the package.\n\n"
        )
        choose_usr_prompt = (
            f"Available software packages:\n {available_choices}\n"
            f"Given task: {functionality} \n"
            "What is the most appropriate MCP server?\n"
            "ONLY output ONE name of the package.\n\n"
            "# OUTPUT FORMAT:\n"
            "THE_PACKAGE_NAME"
        )
        init_msgs = [
            Msg("system", choose_sys_prompt, role="system"),
            Msg("user", choose_usr_prompt, role="user"),
        ]
        chosen_function = {}
        for _ in range(self.llm_max_retries):
            try:
                msgs = self.model.format(*init_msgs)
                function_name = self.model(msgs).text
                init_msgs.append(Msg("system", function_name, role="system"))
                logger.info(f"Model chooses function: {function_name}")
                for pkg in available_choices:
                    if pkg["name"] == function_name:
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

        if len(chosen_function) == 0:
            logger.error(
                "LLM mode fail to get the best MCP server. "
                "Try to use model-free model.",
            )
            raise ValueError("LLM mode fails")

        return chosen_function

    @staticmethod
    def _extract_env_info(package_details: dict) -> dict:
        """
        Extract API key information from package readme information.
        It is expected that there is a `readme` field in the package_details,
        as specified in
        https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md

        Args:
            package_details (dict): The package information, including README.

        Returns:
            `dict`: The required environment variables mentioned in the README,
                and its example input.

        """
        env_info = {}
        readme = package_details.get("readme", "")

        # Check for specific environment variable requirements
        env_var_patterns = [
            # matching content like "export ENV_VARIABLE=XXXX"
            r"export\s+(\w+)\s*=\s*['\"]([^'\"]+)['\"]",
            # matching content like "ENV_VARIABLE=XXXX"
            r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]",
            # matching content like "env": {"ENV_VARIABLE": "XXX"}
            r'"env"\s*:\s*\{\s*"([^"]+)"\s*:\s*"([^"]+)"',
            r"'env'\s*:\s*\{\s*'([^']+)'\s*:\s*'([^']+)'\s*\}",
        ]

        for pattern in env_var_patterns:
            matches = re.findall(pattern, readme)
            for match in matches:
                env_info[match[0]] = {
                    "example_value": match[1],
                }
        return env_info

    def _update_env_variables(
        self,
        required_envs: dict,
    ) -> dict:
        """
        Update the required environment variables.
        Let human to step in to provide the values for environment variables.
        Args:
            required_envs (dict): The required environment variables.

        Return:
            `dict`: The updated environment variables.
        """
        # prepare the environment variables for the MCP server
        envs = {}
        with open(self.env_file_path, "r", encoding="utf-8") as f:
            stored_envs = json.load(f)
        for env_name, info in required_envs.items():
            if env_name in os.environ:
                # check if the env has been set in the env
                envs[env_name] = os.environ[env_name]
                if env_name not in stored_envs:
                    stored_envs[env_name] = os.environ[env_name]
            elif env_name in stored_envs:
                # check if the env has been saved in the local file
                envs[env_name] = stored_envs[env_name]
            else:
                # if no value found, prompt the user to provide necessary value
                if self.console:
                    self.console.print(
                        "[yellow]"
                        f"This MCP may require {env_name} as "
                        f"environment variable."
                        "Please enter the value of the environment "
                        "variable below,"
                        f"such as {info['example_value']} . "
                        f"If you believe this is not an environment variable,"
                        f"delete the shown default value and press ENTER."
                        "[/yellow]",
                    )
                env_value = click.prompt(
                    f"Enter the value for {env_name}",
                    default=info["example_value"],
                    show_default=True,
                )
                env_type = type(env_value)
                env_value = str(env_value).strip()
                if len(env_value) > 0:
                    envs[env_name] = env_type(env_value)
                    stored_envs[env_name] = env_value

        with open(self.env_file_path, "w", encoding="utf-8") as f:
            json.dump(stored_envs, f)

        return envs

    def _build_server_config(
        self,
        chosen_mcp_name: str,
        skip_modification: bool = False,
    ) -> dict:
        """
        Search if there is any server config in README, and generate such
        configuration but replace the args and env with human input.
        Example extraction:
            {
              "mcpServers": {
                "github": {
                  "command": "npx",
                  "args": [
                    "-y",
                    "@modelcontextprotocol/server-github"
                  ],
                  "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
                  }
                }
              }
            }

        Args:
            chosen_mcp_name (str): The name of the chosen MCP server.
            skip_modification (bool): Whether to skip modification of the
                the configuration. NOTE: Turn `Ture` only when testing.

        Return:
            `dict`: the updated configuration
        """
        configs = []
        package_details = self.get_package_details(chosen_mcp_name) or {}
        readme = package_details.get("readme", "")

        # Check for if there is any `mcpServers` config in README
        pattern = r'"mcpServers"\s*:\s*(\{(?:[^{}]*|\{.*?\})*\})'
        matches = re.findall(pattern, readme, re.DOTALL)
        for idx, match_str in enumerate(matches, 1):
            self.console.print(
                f"\nExtracted mcpServers JSON #{idx}:\n{match_str}",
            )
            try:
                config_json = json.loads(match_str)
                logger.info(
                    "\nParsed config into JSON\n",
                )
                configs.append(config_json)
            except json.JSONDecodeError as e:
                logger.error(f"\nError decoding JSON #{idx}:", e)

        chosen_config = {}
        # prefer those with "npx" command
        for config in configs:
            for key, _ in config.items():
                if chosen_config.get(key) is None:
                    chosen_config = config
                elif (
                    config[key]["command"] == "npx"
                    and chosen_config[key]["command"] != "npx"
                ):
                    chosen_config = config

        envs_dict = self._extract_env_info(package_details)

        if len(chosen_config) == 0:
            chosen_config = {
                chosen_mcp_name: {
                    "command": "npx",
                    "args": ["-y", chosen_mcp_name],
                    "env": {
                        k: v["example_value"] for k, v in envs_dict.items()
                    },
                },
            }

        self.console.print(
            "Overall composed config will look like:\n"
            f"{json.dumps(chosen_config, indent=2)}",
        )

        self.console.print(
            "Need to verify the following MCP server configuration."
            "Press Enter to use the provided value.",
        )

        if skip_modification:
            return chosen_config

        name = list(chosen_config.keys())[0]

        # update args
        to_be_remove_arg_idx = []
        for i, arg in enumerate(chosen_config[name]["args"]):
            if arg in ["-y", name, chosen_mcp_name]:
                continue
            new_arg = click.prompt(
                f"Update arg: {arg}? "
                "(press Enter to use default; "
                "press Space + Enter to remove this arg)",
                default=arg,
            )
            arg_type = type(new_arg)
            new_arg = str(new_arg).strip()
            if len(new_arg) > 0:
                chosen_config[name]["args"][i] = arg_type(new_arg)
            else:
                to_be_remove_arg_idx.append(i)

        # remove unwanted args
        args_len = len(chosen_config[name]["args"])
        chosen_config[name]["args"] = [
            chosen_config[name]["args"][i]
            for i in range(args_len)
            if i not in to_be_remove_arg_idx
        ]

        # add new args
        while True:
            new_arg = click.prompt(
                "Add new arg? "
                "(press Space + Enter when you don't need to add more)",
                default="",
                show_default=False,
            )
            if len(str(new_arg).strip()) == 0:
                break
            chosen_config[name]["args"].append(new_arg)

        # update env
        chosen_config[name]["env"] = self._update_env_variables(
            envs_dict,
        )

        return chosen_config

    def _confirm_chosen_mcp(
        self,
        default_choice: dict,
        all_choices: list[dict],
    ) -> dict:
        """
        Let user confirm whether the suggested MCP server is what they want.
        Args:
            default_choice (dict): The suggested and default
                MCP server configuration
            all_choices (dict): All the suggested MCP server

        Return:
            `dict`: the details of the MCP server confirmed by human.
        """
        for i, choice in enumerate(all_choices):
            if choice["name"] == default_choice["name"] and i > 0:
                all_choices[0], all_choices[i] = all_choices[i], all_choices[0]

        self.console.print(
            "The following may be MCP servers that can help you:",
        )

        for idx, choice in enumerate(all_choices):
            if choice == default_choice:
                self.console.print(
                    f"{idx}. {choice['name']} "
                    "[bold green](recommended)[/bold green]",
                )
            else:
                self.console.print(f"{idx}. {choice['name']}")

        user_input = self.console.input(
            "\nEnter choice number or press [bold green]Enter[/bold green] "
            "to select default: ",
        )

        if not user_input.strip():
            selected = default_choice
        else:
            try:
                selected = all_choices[int(user_input)]
            except (ValueError, IndexError):
                self.console.print(
                    "[red]Invalid selection, default chosen.[/red]",
                )
                selected = default_choice
        return selected

    def search_and_add_mcp_server(
        self,
        desired_functionality: str,
    ) -> ServiceResponse:
        """
        Automatically search for appropriate MCP servers as tools to
        solve the task.
        Args:
            desired_functionality (str):
                One or two keywords for the desired functionality/software.
                ONLY ONE OR TWO KEYWORD as the functionality.
                Examples: "web search", "file search", "GitHub access"

        Return:
            `ServiceResponse` : return whether success or fail in installing
                MCP server/tools.
        """
        try:
            all_choices = self.search_mcp_server(desired_functionality)
            if self.model:
                chosen_function = self._llm_select(
                    desired_functionality,
                    all_choices,
                )
            else:
                chosen_function = self._model_free_select(
                    desired_functionality,
                    all_choices,
                )
            # confirm with user before install
            if self.confirm_install:
                chosen_function = self._confirm_chosen_mcp(
                    chosen_function,
                    all_choices,
                )
            config = self._build_server_config(chosen_function["name"])
            new_servers, new_functions = self.add_mcp_servers(
                server_configs={
                    "mcpServers": config,
                },
            )
            self.auto_added_mcp_servers += new_servers

            tools_str = json.dumps(new_functions, ensure_ascii=False, indent=2)
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=(
                    "Successfully auto added MCP servers. "
                    "New tools added:\n"
                    f"{tools_str}"
                ),
            )
        except Exception as e:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=("Fail to add MCP server. " f"Error:\n {e}"),
            )

    def remove_auto_added_mcp_server(
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
                for tool in sync_exec(server.list_tools):
                    if tool.name == remove_tool_name:
                        all_tools = sync_exec(server.list_tools)
                        # clean all service functions from the same MCP server
                        for cur_tool in all_tools:
                            self.service_funcs.pop(cur_tool.name, None)
                        all_remove_tools = [tool.name for tool in all_tools]
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
