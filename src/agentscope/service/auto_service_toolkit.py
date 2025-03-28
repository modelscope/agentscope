# -*- coding: utf-8 -*-
""" An Enhanced Service Toolkit that can search and auto import MCP servers."""
import json
import re
import os
import click
from typing import (
    Any,
    Optional,
    List,
    Dict,
)
from loguru import logger
import requests
from rich.console import Console

from ..message import Msg
from ..models import ModelWrapperBase
from ..manager import FileManager, ModelManager

from .service_toolkit import ServiceToolkit

try:
    from docstring_parser import parse
except ImportError:
    parse = None



class AutoServiceToolkit(ServiceToolkit):

    llm_max_retries: int = 3

    def __init__(
        self,
        env_file_dir: Optional[str] = None,
        confirm_install: bool = False,
        model_free: bool = False,
        model_config_name: Optional[str] = None,
        use_console: bool = True,
    ):
        super().__init__()
        if env_file_dir is None:
            env_file_dir = FileManager.get_instance().cache_dir or "./"
        self.env_file_path = os.path.join(env_file_dir, ".mcp_env.json")
        if not os.path.exists(self.env_file_path):
            with open(self.env_file_path, mode="w") as env_file:
                json.dump({}, env_file)
        print(f"cache env  at {self.env_file_path}")
        if not model_free:
            model_manager = ModelManager.get_instance()
            self.model = model_manager.get_model_by_config_name(
                model_config_name
            )
        else:
            self.model = None

        self.confirm_install = confirm_install

        if use_console:
            self.console = Console()
        else:
            raise NotImplementedError

        self.auto_added_mcp_servers = []

    def get_package_details(self, package_name: str) -> Optional[Dict]:
        """Get detailed package information including environment variables."""
        try:
            response = requests.get(f"https://registry.npmjs.org/{package_name}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching package details: {e}")
            return None

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

    def _calculate_relevance_score(self, pkg: Dict, query: str) -> float:
        """Calculate relevance score for a package based on various factors."""

        # Get package details
        name = pkg.get("name", "").lower()
        description = pkg.get("description", "").lower()
        keywords = [k.lower() for k in pkg.get("keywords", [])]
        downloads = pkg.get("downloads", {}).get("last-month", 0)

        # Calculate text relevance
        query_terms = query.lower().split()
        name_score = sum(1 for term in query_terms if term in name) / len(
            query_terms)
        desc_score = sum(
            1 for term in query_terms if term in description) / len(
            query_terms)
        keyword_score = sum(1 for term in query_terms if
                            any(term in k for k in keywords)) / len(
            query_terms)

        # Normalize downloads (assuming max downloads is 1M)
        download_score = min(downloads / 1_000_000, 1.0)

        # Weighted scoring (hard-coded)
        weights = {
            'name': 0.3,
            'description': 0.2,
            'keywords': 0.2,
            'downloads': 0.3
        }

        total_score = (
            name_score * weights['name'] +
            desc_score * weights['description'] +
            keyword_score * weights['keywords'] +
            download_score * weights['downloads']
        )

        return total_score

    def _model_free_select_and_choose(
        self,
        task: str
    ) -> Optional[Dict]:
        packages = self.search_mcp_server(task)

        """Select the best package based on relevance score."""
        if not packages:
            return None

        scored_packages = [
            (pkg, self._calculate_relevance_score(pkg, task))
            for pkg in packages
        ]

        # Sort by score in descending order
        scored_packages.sort(key=lambda x: x[1], reverse=True)
        return scored_packages[0][0], packages


    def _llm_search_and_choose(
        self,
        task: str,
    ):
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
            "You are a helpful assistant that can extract a keyword from the task to describe"
            "the key functionality/software required to solve the task."
            "ONLY output ONE keyword."
        )
        search_usr_prompt = (
            f"Given task: {task}. \n"
            f"What are the the key unctionality/software in ONE keyword?"
        )
        msgs = self.model.format(
            Msg("system", search_sys_prompt, role="system"),
            Msg("user", search_usr_prompt, role="user"),
        )
        function_keywords = self.model(msgs).text
        print(f"keywords: {function_keywords}")

        avaiable_choices = self.search_mcp_server(function_keywords)
        logger.info(f"Search function keywords: {function_keywords}")
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
            "ONLY output ONE name of the package.\n\n"
        )
        choose_usr_prompt = (
            f"Available software packages:\n {avaiable_choices}\n"
            f"Given task: {task} \nWhat is the most appropriate MCP server?\n"
            "ONLY output ONE name of the package.\n\n# OUTPUT FORMAT:\n"
            "THE_PACKAGE_NAME"
        )
        print(avaiable_choices)
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
                for pkg in avaiable_choices:
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
                "Try to use model-free model."
            )
            raise ValueError( "LLM mode fails")

        return chosen_function, avaiable_choices

    def _extract_env_info(self, package_details: Dict) -> Dict[str, str]:
        """
        Extract API key information from package readme information.
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
            r"'env'\s*:\s*\{\s*'([^']+)'\s*:\s*'([^']+)'\s*\}"
        ]

        for pattern in env_var_patterns:
            matches = re.findall(pattern, readme)
            for match in matches:
                env_info[match[0]] = {
                    "example_value": match[1],
                }
                print(match[0], match[1])
        return env_info


    def _update_env_variables(
        self,
        required_envs: Dict
    ):
        # prepare the environment variables for the MCP server
        envs = {}
        with open(self.env_file_path, "r") as f:
            stored_envs = json.load(f)
        for env_name, info in required_envs.items():
            if env_name in os.environ:
                # check if the env has been set in the env
                envs[env_name] = os.environ[env_name]
                if not env_name in stored_envs:
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
                        f"If you believe this is not environment variable,"
                        f"delete the shown default value and press ENTER."
                        "[/yellow]"
                    )
                env_value = click.prompt(
                    f"Enter the value for {env_name}",
                    default=info['example_value'],
                    show_default=True
                )
                env_type = type(env_value)
                env_value = str(env_value).strip()
                if len(env_value) > 0:
                    envs[env_name] = env_type(env_value)
                    stored_envs[env_name] = env_value

        with open(self.env_file_path, "w") as f:
            json.dump(stored_envs, f)

        return envs

    def _build_server_config(
        self, chosen_mcp_name: str
    ) -> List[Dict]:
        """
        Search if there is any
        Example:
        """
        configs = []
        package_details = self.get_package_details(chosen_mcp_name)
        readme = package_details.get("readme", "")

        # Check for if there is any `mcpServers` config in README
        config_patterns = []
        pattern = r'"mcpServers"\s*:\s*(\{(?:[^{}]*|\{.*?\})*\})'
        matches = re.findall(pattern, readme, re.DOTALL)
        for idx, match_str in enumerate(matches, 1):
            self.console.print(
                f"\nExtracted mcpServers JSON #{idx}:\n{match_str}"
            )
            try:
                config_json = json.loads(match_str)
                logger.info(
                    f"\nParsed config into JSON\n"
                )
                configs.append(config_json)
            except json.JSONDecodeError as e:
                logger.error(f"\nError decoding JSON #{idx}:", e)

        chosen_config = {}
        for config in configs:
            for key, value in config.items():
                if chosen_config.get(key) is None:
                    chosen_config = config
                elif (config[key]["command"] == "npx" and
                      chosen_config[key]["command"] != "npx"):
                    chosen_config = config

        envs_dict = self._extract_env_info(package_details)

        if len(chosen_config) == 0:
            chosen_config = {
                chosen_mcp_name: {
                    "command": "npx",
                    "args": ["-y", chosen_mcp_name],
                    "env": {
                        k: v["example_value"] for k, v in envs_dict.items()
                    }
                }
            }

        self.console.print(
            "Overall composed config will look like:\n"
            f"{json.dumps(chosen_config, indent=2)}"
        )

        self.console.print(
            "Need to verify the following MCP server configuration."
            "Press Enter to use the provided value."
        )

        name = list(chosen_config.keys())[0]

        # update args
        to_be_remove_arg_idx = []
        for i, arg in enumerate(chosen_config[name]["args"]):
            if arg == "-y" or arg == name or arg == chosen_mcp_name:
                continue
            new_arg = click.prompt(
                f"Update arg: {arg}? "
                "(press Enter to use default; "
                "press Space + Enter to remove this arg)",
                default=arg
            )
            arg_type = type(new_arg)
            new_arg = str(new_arg).strip()
            if len(new_arg) > 0:
                chosen_config[name]['args'][i] = arg_type(new_arg)
            else:
                to_be_remove_arg_idx.append(i)

        # remove unwanted args
        args_len = len(chosen_config[name]["args"])
        chosen_config[name]["args"] = [
            chosen_config[name]["args"][i] for i in range(args_len)
            if i not in to_be_remove_arg_idx
        ]

        # add new args
        while True:
            new_arg = click.prompt(
                f"Add new arg: {arg}? "
                "(press Space + Enter when you don't need to add more)",
                default="",
                show_default=False
            )
            if len(str(new_arg).strip()) == 0:
                break
            chosen_config[name]["args"].append(new_arg)


        # update env
        chosen_config[name]["env"] = self._update_env_variables(
            envs_dict
        )

        return chosen_config

    def _confirm_chosen_mcp(
        self,
        default_choice,
        all_choices
    ):
        for i, choice in enumerate(all_choices):
            if choice["name"] == default_choice["name"] and i > 0:
                all_choices[0], all_choices[i] = all_choices[i], all_choices[0]

        self.console.print(
            "The following may be MCP servers that can help you:"
        )

        for idx, choice in enumerate(all_choices):
            if choice == default_choice:
                self.console.print(
                    f"{idx}. {choice['name']} "
                    "[bold green](recommended)[/bold green]"
                )
            else:
                self.console.print(f"{idx}. {choice['name']}")

        user_input = self.console.input(
            "\nEnter choice number or press [bold green]Enter[/bold green] "
            "to select default: ")

        if not user_input.strip():
            selected = default_choice
        else:
            try:
                selected = all_choices[int(user_input)]
            except (ValueError, IndexError):
                self.console.print(
                    "[red]Invalid selection, default chosen.[/red]"
                )
                selected = default_choice
        return selected

    def search_and_add_mcp_server(
        self,
        task: str,
    ) -> None:
        if self.model:
            chosen_function, all_choices = self._llm_search_and_choose(task)
        else:
            chosen_function, all_choices = self._model_free_select_and_choose(
                task
            )
        # confirm with user before install
        if self.confirm_install:
            chosen_function = self._confirm_chosen_mcp(
                chosen_function, all_choices
            )
        config = self._build_server_config(chosen_function["name"])
        print("--- Final:")
        print(config)
        self.add_mcp_servers(
            server_configs={
                "mcpServers": config,
            },
        )
        self.auto_added_mcp_servers.append(chosen_function["name"])

    # TODO: re-add mcp server if fail
    def remove_and_add_mcp_server(
        self,
        mcp_name: str,
    ):
        pass