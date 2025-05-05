# -*- coding: utf-8 -*-
# pylint: disable=R0912
""" An Enhanced Service Toolkit that can search and auto import MCP servers."""
import json
import re
from typing import Any, Optional
from loguru import logger
import requests


def get_package_details(
    package_name: str,
    query_api: str = "https://registry.npmjs.org",
) -> Optional[dict]:
    """
    Get detailed package information including environment variables.
    Args:
        package_name (str): The package name.
        query_api (str): the query api to obtain more details about the
            packages, default is set to "https://registry.npmjs.org"

    Return:
        `Dict`: The package information
    """
    try:
        response = requests.get(
            f"{query_api}/{package_name}",
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching package details: {e}")
        return None


def search_mcp_server(
    function_keywords: str,
    size: int = 20,
    search_url: str = "https://registry.npmjs.org/-/v1/search",
    **kwargs: Any,
) -> list[dict]:
    """
    Search for appropriate MCP server with tools/functions for LLM and agents.
    By Default, it depends on npm Public Registry API:
    https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md
    It is possible to search MCP with specific authors, maintainer,
    scope, etc. Details can be found in the above websites.
    https://itnext.io/increasing-an-npm-packages-search-score-fb557f859300

    Args:
        function_keywords (str): Keywords of the desired function;
        size (int): Size of the search results;
        search_url (str): the MCP server (npm package) search URL API;
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
        pkg (dict): Details of a package from search_mcp_server function.
            Each pkg should be a dict with "name", "description", "keywords",
            and "downloads" fields.
        query (str): The query (key functionality) to search for.

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
    desc_score = sum(1 for term in query_terms if term in description) / len(
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


def model_free_recommend_mcp(
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
        `Dict`: The selected package (and its details "name",
        "description", "keywords", and "downloads")`
    """
    if not available_choices:
        return {}

    scored_packages = [
        (pkg, _calculate_relevance_score(pkg, functionality))
        for pkg in available_choices
    ]

    # Sort by score in descending order
    scored_packages.sort(key=lambda x: x[1], reverse=True)
    return scored_packages[0][0]


def _extract_env_info(package_details: dict) -> dict:
    """
    Extract API key information from package readme information.
    It is expected that there is a `readme` field in the package_details,
    as specified in
    https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md

    Args:
        package_details (dict): The package information,
            including "readme" field.

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


def build_mcp_server_config(
    chosen_mcp_name: str,
    query_detail_api: str = "https://registry.npmjs.org",
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
        query_detail_api (str): The default API URL for query detailed
            information of MCP servers.

    Return:
        `dict`: a configuration template
    """
    configs = []
    package_details = (
        get_package_details(
            chosen_mcp_name,
            query_detail_api,
        )
        or {}
    )
    readme = package_details.get("readme", "")

    # Check for if there is any `mcpServers` config in README
    pattern = r'"mcpServers"\s*:\s*(\{(?:[^{}]*|\{[^{}]*\})*\})'
    matches = re.findall(pattern, readme, re.DOTALL)
    for idx, match_str in enumerate(matches, 1):
        logger.info(
            f"\nExtracted mcpServers JSON #{idx}:\n{match_str}",
        )
        try:
            config_json = json.loads(match_str)
            logger.info(
                "\nParsed config into JSON\n",
            )
            configs.append(config_json)
        except json.JSONDecodeError as e:
            logger.warning(f"Error decoding JSON #{idx}:", e)

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

    envs_dict = _extract_env_info(package_details)

    if len(chosen_config) == 0:
        chosen_config = {
            chosen_mcp_name: {
                "command": "npx",
                "args": ["-y", chosen_mcp_name],
                "env": {k: v["example_value"] for k, v in envs_dict.items()},
            },
        }

    return {"mcpServers": chosen_config}


# for encouraging agent to automatically install MCP server
CHOOSE_MCP_PROMPT = (
    "# TASK:\n"
    "Given the available software packages and "
    "the description of desired functionality, you need to determine "
    "what is the most appropriate MCP Server to help solve the task "
    "based on the description, keyword and download statistics information."
    "Usually, a package is a MCP server software package if it has "
    "at least one of the following properties: "
    "1. There are keywords 'mcp' or '@modelcontextprotocol' or "
    "'server' in their Name."
    "2. There are keywords 'mcp' or 'Model Context protocol' "
    "in its Description or Keywords."
    "\n# Requirements:"
    "1. Make choice based on the name, description and keywords."
    "2. The selected package must be MCP server."
    "ONLY output ONE name of the package.\n\n"
    "### Available software packages (MCP servers):\n "
    "{available_choices}\n"
    "## Desired funtionality: {functionality} \n"
    "# Question:\n"
    "What is the most appropriate MCP server?\n"
    "Once you have make the decision, call the function that can help you get"
    "the MCP server configuration template with the chosen MCP server name."
)

# remind agent to get human (user agent) involved
HUMAN_CHOOSE_PROMPT = (
    "Your next step should output the complete list of available "
    "choices to the User, including your recommendation. "
    "You should expect the user will choose one of the MCP server package "
    "in the next round."
    "Once you have the User's decision, call the function that can help you "
    "get the MCP server configuration template with the chosen MCP server "
    "name."
)
