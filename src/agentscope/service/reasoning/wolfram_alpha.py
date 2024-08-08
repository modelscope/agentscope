# -*- coding: utf-8 -*-
"""Query Wolfram Alpha API"""
import os
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
    Query the Wolfram Alpha Short Answers API. The Short Answers API returns
    a single plain text result directly from Wolfram|Alpha. In general, this
    text is taken directly from the Result pod of Wolfram|Alpha output. This
    API type is designed to deliver brief answers in the most basic
    format possible. Suitable for queries such as simple knowledge/facts
    retrieval. See
    https://products.wolframalpha.com/short-answers-api/documentation
    for more details.

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
            # Output: Paris, Île-de-France, France
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
    save_path: str = "wolfram_alpha_result.png",
) -> ServiceResponse:
    """
    Query the Wolfram Alpha Simple API. The Simple API generates full
    Wolfram|Alpha output in a universally viewable image format.
    Suitable for queries such as knowledge/facts retrieval. See
    https://products.wolframalpha.com/simple-api/documentation
    for more details.

    Args:
        api_key (`str`):
            Your Wolfram Alpha API key.
        query (`str`):
            The query string to search.
        save_path (`str`, optional):
            The path where the result image will be saved.
            Defaults to "wolfram_alpha_result.png" in the current directory.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a dictionary containing
        the result or error information,
        which depends on the `status` variable.
        The returned image is saved in the specified save path.

    Example:
        .. code-block:: python

            result = query_wolfram_alpha_simple(
                "your_api_key",
                "Plot sin(x)",
                save_path="path/to/save/result.png"
            )
            if result.status == ServiceExecStatus.SUCCESS:
                logger.info(f"Result saved as '{result.content['result']}'")
    """
    url = "http://api.wolframalpha.com/v1/simple"
    params = {"i": query, "appid": api_key}

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            # Get the directory path
            dir_path = os.path.dirname(save_path)

            # If dir_path is not empty, create the directory
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            with open(save_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Result saved as '{save_path}'")
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content={
                    "result": save_path,
                },
            )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={
                "error": f"HTTP Error: {response.status_code} {response.text}",
            },
        )
    except Exception as e:
        logger.error(f"Error in query_wolfram_alpha_simple: {str(e)}")
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
        )


def query_wolfram_alpha_show_steps(
    api_key: str,
    query: str,
) -> ServiceResponse:
    """
    Query the Wolfram Alpha Show Steps API. An extension of the
    Full Results API, the Show Steps API gives direct access to
    Wolfram|Alpha's full for queries in a variety of mathematical
    and scientific subjects. These explanations of computed answers
    are designed to provide clarity and understanding to the
    end user and are especially useful in educational and
    training applications. see
    https://products.wolframalpha.com/show-steps-api/documentation
    for more details.

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

        Output:
            solve x^2 + 2 x + 1 = 0
            x = -1
            Solve for x:
            x^2 + 2 x + 1 = 0
            Write the left hand side as a square:
            (x + 1)^2 = 0
            Take the square root of both sides:
            x + 1 = 0
            Subtract 1 from both sides:
            Answer: |
             | x = -1
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
    Query the Wolfram Alpha LLM API. The LLM API is built for
    use specifically with large language models and chat products.
    Although the majority of data available through the
    Wolfram|Alpha website is also available through this API,
    certain subjects may be restricted by default. see
    https://products.wolframalpha.com/llm-api/documentation for more details.

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
                "3 densest elemental metals"
            )
            if result.status == ServiceExecStatus.SUCCESS:
                print(result.content['result'])

        Example output:
        .. code-block:: text

            Query:
            "3 densest elemental metals"

            Input interpretation:
            3 densest metallic elements | by mass density

            Result:
            1 | hassium | 41 g/cm^3 |
            2 | meitnerium | 37.4 g/cm^3 |
            3 | bohrium | 37.1 g/cm^3 |

            Periodic table location:
            image: https://www6b3.wolframalpha.com/Calculate/...

            Images:
            image: https://www6b3.wolframalpha.com/Calculate/...
            Wolfram Language code:
            Dataset[
                EntityValue[
                    {
                        Entity["Element", "Hassium"],
                        Entity["Element", "Meitnerium"],
                        Entity["Element", "Bohrium"]
                    },
                    EntityProperty["Element", "Image"],
                    "EntityAssociation"
                ]
            ]

            Basic elemental properties:
             | hassium | meitnerium | bohrium
            atomic symbol | Hs | Mt | Bh
            atomic number | 108 | 109 | 107
            atomic mass | 269 u | 277 u | 270 u
            half-life | 67 min | 30 min | 90 min

            Material properties:
             | hassium | meitnerium | bohrium
            mass density | 41 g/cm^3 | 37.4 g/cm^3 | 37.1 g/cm^3
            (properties at standard conditions)

            Reactivity:
             | bohrium
            valence | 7

            Atomic properties:
             | hassium | meitnerium | bohrium
            term symbol | ^5D_4 | ^4F_(9/2) | ^6S_(5/2)
            (electronic ground state properties)

            Abundances:
              | (all cases)
            crust abundance | 0 mass%
            human abundance | 0 mass%

            Nuclear properties:
             | hassium | meitnerium | bohrium
            half-life | 67 min | 30 min | 90 min
            specific radioactivity | 446085 TBq/g | 833168 TBq/g | 285952 TBq/g
            unstable isotopes | hassium-276 (67 min) | ...
                              | meitnerium-278 (30 min) | ...
                              | bohrium-274 (90 min) | ...

              | (all cases)
            decay mode | alpha emission

            Identifiers:
             | hassium | meitnerium | bohrium
            CAS number | 54037-57-9 | 54038-01-6 | 54037-14-8
            PubChem CID number | CID56951714 | CID56951716 | CID56951713

            Wikipedia page hits history:
            image: https://www6b3.wolframalpha.com/Calculate/...

            Wolfram|Alpha website result for "3 densest elemental metals":
            https://www6b3.wolframalpha.com/input?i=3+densest+elemental+metals
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
