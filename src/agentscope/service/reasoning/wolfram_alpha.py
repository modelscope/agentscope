# -*- coding: utf-8 -*-
"""Query Wolfram Alpha API"""
from typing import Any, Dict  # Corrected import order
import requests  # Corrected import order
from loguru import logger  # Corrected import order
from agentscope.service.service_response import (
    ServiceResponse,
    ServiceExecStatus,
)


def query_wolfram_alpha_short_answers(
    api_key: str,
    query: str,
) -> ServiceResponse:
    """
    Query the Wolfram Alpha Short Answers API.

    Args:
        api_key (`str`):
            Your Wolfram Alpha API key.
        query (`str`):
            The query string to search.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a dictionary containing
        the result or error information,
        which depends on the `status` variable.

    Example:
        .. code-block:: python

            result = query_wolfram_alpha_short_answers(
                "your_api_key",
                "What is the capital of France?"
            )
            if result.status == ServiceExecStatus.SUCCESS:
                print(result.content['result'])
    """
    url = "http://api.wolframalpha.com/v1/result"
    params = {"i": query, "appid": api_key}

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content={"result": response.text},
            )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={
                "error": f"HTTP Error: {response.status_code} {response.text}",
            },
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
        )


def query_wolfram_alpha_simple(
    api_key: str,
    query: str,
) -> ServiceResponse:
    """
    Query the Wolfram Alpha Simple API.

    Args:
        api_key (`str`):
            Your Wolfram Alpha API key.
        query (`str`):
            The query string to search.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a dictionary containing
        the result or error information,
        which depends on the `status` variable.

    Example:
        .. code-block:: python

            result = query_wolfram_alpha_simple(
                "your_api_key",
                "Plot sin(x)"
            )
            if result.status == ServiceExecStatus.SUCCESS:
                print("Result saved as 'wolfram_alpha_result.png'")
    """
    url = "http://api.wolframalpha.com/v1/simple"
    params = {"i": query, "appid": api_key}

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            with open("wolfram_alpha_result.png", "wb") as file:
                file.write(response.content)
            print("Result saved as 'wolfram_alpha_result.png'")
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content={
                    "result": "Image saved as 'wolfram_alpha_result.png'",
                },
            )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={
                "error": f"HTTP Error: {response.status_code} {response.text}",
            },
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
        )


def query_wolfram_alpha_show_steps(
    api_key: str,
    query: str,
) -> ServiceResponse:
    """
    Query the Wolfram Alpha Show Steps API.

    Args:
        api_key (`str`):
            Your Wolfram Alpha API key.
        query (`str`):
            The query string to search.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a dictionary containing
        the result or error information,
        which depends on the `status` variable.

    Example:
        .. code-block:: python

            result = query_wolfram_alpha_show_steps(
                "your_api_key",
                "Solve x^2 + 2x + 1 = 0"
            )
            if result.status == ServiceExecStatus.SUCCESS:
                print(result.content['result'])
    """
    url = "http://api.wolframalpha.com/v2/query"
    params = {
        "input": query,
        "appid": api_key,
        "output": "JSON",
        "podstate": "Step-by-step solution",
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data: Dict[str, Any] = response.json()
            steps = []
            logger.info(f"Show Steps API response: {data}")
            for pod in data["queryresult"].get("pods", []):
                logger.info(f"Processing pod: {pod.get('title')}")
                for subpod in pod.get("subpods", []):
                    logger.info(f"Processing subpod: {subpod.get('title')}")
                    plaintext = subpod.get("plaintext", "").strip()
                    if plaintext:
                        steps.append(plaintext)
            if not steps:
                logger.warning(
                    "No step-by-step solution found in the response.",
                )
                return ServiceResponse(
                    status=ServiceExecStatus.ERROR,
                    content={
                        "error": (
                            "No step-by-step solution found in the response."
                        ),
                    },
                )
            formatted_steps = "\n".join(steps)
            print(formatted_steps)
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content={"result": formatted_steps},
            )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={
                "error": f"HTTP Error: {response.status_code} {response.text}",
            },
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
        )


def query_wolfram_alpha_llm(
    api_key: str,
    query: str,
) -> ServiceResponse:
    """
    Query the Wolfram Alpha LLM API.

    Args:
        api_key (`str`):
            Your Wolfram Alpha API key.
        query (`str`):
            The query string to search.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a dictionary containing
        the result or error information,
        which depends on the `status` variable.

    Example:
        .. code-block:: python

            result = query_wolfram_alpha_llm(
                "your_api_key",
                "Explain quantum entanglement"
            )
            if result.status == ServiceExecStatus.SUCCESS,
                print(result.content['result'])
    """
    url = "https://www.wolframalpha.com/api/v1/llm-api"
    params = {"input": query, "appid": api_key}

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content={"result": response.text},
            )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={
                "error": f"HTTP Error: {response.status_code} {response.text}",
            },
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
        )
