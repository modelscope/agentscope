# -*- coding: utf-8 -*-
"""
Search contents from WikiPedia
"""
import requests

from ..service_response import (
    ServiceResponse,
    ServiceExecStatus,
)


def wikipedia_search_categories(
    query: str,
    max_members: int = 1000,
) -> ServiceResponse:
    """Retrieve categories from Wikipedia:Category pages.

    Args:
        query (str):
            The given searching keywords
        max_members (int):
            The maximum number of members to output

    Returns:
        `ServiceResponse`: A response that contains the execution status and
        returned content. In the returned content, the meanings of keys:
            - "pageid": unique page ID for the member
            - "ns": namespace for the member
            - "title": title of the member

        Example:

        .. code-block:: python

            members = wiki_get_category_members(
                "Machine_learning",
                max_members=10
            )
            print(members)

        It returns contents:

        .. code-block:: python

            {
                'status': <ServiceExecStatus.SUCCESS: 1>,
                'content': [
                    {
                        'pageid': 67911196,
                        'ns': 0,
                        'title': 'Bayesian learning mechanisms'
                    },
                    {
                        'pageid': 233488,
                        'ns': 0,
                        'title': 'Machine learning'
                    },
                    # ...
                ]
            }

    """
    url = "https://en.wikipedia.org/w/api.php"
    limit_per_request: int = 500
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{query}",
        "cmlimit": limit_per_request,  # Maximum number of results per request
        "format": "json",
    }

    members = []
    total_fetched = 0

    try:
        while total_fetched < max_members:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()

            data = response.json()

            batch_members = data["query"]["categorymembers"]
            members.extend(batch_members)
            total_fetched += len(batch_members)

            # Check if there is a continuation token
            if "continue" in data and total_fetched < max_members:
                params["cmcontinue"] = data["continue"]["cmcontinue"]
            else:
                break

    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=str(e),
        )

    # If more members were fetched than max_members, trim the list
    if len(members) > max_members:
        members = members[:max_members]

    if len(members) > 0:
        return ServiceResponse(ServiceExecStatus.SUCCESS, members)

    return ServiceResponse(ServiceExecStatus.ERROR, members)


def wikipedia_search(  # pylint: disable=C0301
    query: str,
) -> ServiceResponse:
    """Search the given query in Wikipedia. Note the returned text maybe related entities, which means you should adjust your query as needed and search again.

    Note the returned text maybe too long for some llm, it's recommended to
    summarize the returned text first.

    Args:
        query (`str`):
            The searched query in wikipedia.

    Return:
        `ServiceResponse`: A response that contains the execution status and
        returned content.
    """  # noqa

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": query,
        "prop": "extracts",
        "explaintext": True,
        "format": "json",
    }
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        # Combine into a text
        text = []
        for page in data["query"]["pages"].values():
            if "extract" in page:
                text.append(page["extract"])
            else:
                return ServiceResponse(
                    status=ServiceExecStatus.ERROR,
                    content="No content found",
                )

        content = "\n".join(text)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=content,
        )

    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=str(e),
        )
