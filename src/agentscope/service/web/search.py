# -*- coding: utf-8 -*-
"""Search question in the web"""
from typing import Any
from agentscope.service.service_response import ServiceResponse
from agentscope.utils.common import requests_get
from agentscope.service.service_status import ServiceExecStatus


def bing_search(
    question: str,
    api_key: str,
    num_results: int = 10,
    **kwargs: Any,
) -> ServiceResponse:
    """
    Search question in Bing Search API and return the searching results

    Args:
        question (`str`):
            The search query string.
        api_key (`str`):
            The API key provided for authenticating with the Bing Search API.
        num_results (`int`, defaults to `10`):
            The number of search results to return.
        **kwargs (`Any`):
            Additional keyword arguments to be included in the search query.
            For more details, please refer to
            https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/query-parameters

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a list of search results or error information,
        which depends on the `status` variable.
        For each searching result, it is a dictionary with keys 'title',
        'link', and 'snippet'.

    Example:
        .. code-block:: python

            results = bing_search(question="What is an agent?",
                                 bing_api_key="your bing api key",
                                 num_results=2,
                                 mkt="en-US")
            print(results)

        It returns the following dict.

        .. code-block:: python

            {
                'status': <ServiceExecStatus.SUCCESS: 1>,
                'content': [
                    {
                        'title': 'What Is an Agent? Definition, Types of
                            Agents, and Examples - Investopedia',
                        'link':
                        'https://www.investopedia.com/terms/a/agent.asp',
                        'snippet': "An agent is someone that is given
                            permission (either explicitly or assumed) to act
                            on an individual's behalf and may do so in a
                            variety of capacities. This could include
                            selling a home, executing..."},
                    {
                        'title': 'AGENT Definition & Usage Examples |
                                    Dictionary.com',
                        'link': 'https://www.dictionary.com/browse/agent',
                        'snippet': 'noun. a person who acts on behalf of
                            another person, group, business, government,
                            etc; representative. a person or thing that acts
                            or has the power to act. a phenomenon,
                            substance, or organism that exerts some force or
                            effect: a chemical agent.'
                    }
                ]
            }
    """

    # Bing Search API endpoint
    bing_search_url = "https://api.bing.microsoft.com/v7.0/search"

    params = {"q": question, "count": num_results}
    if kwargs:
        params.update(**kwargs)

    headers = {"Ocp-Apim-Subscription-Key": api_key}

    search_results = requests_get(
        bing_search_url,
        params,
        headers,
    )

    if isinstance(search_results, str):
        return ServiceResponse(ServiceExecStatus.ERROR, search_results)

    # Retrieve the top search result links
    results = search_results.get("webPages", {}).get("value", [])

    # Return all snippet
    return ServiceResponse(
        ServiceExecStatus.SUCCESS,
        [
            # We changed the keywords to be consistent with the
            # Google search results format.
            {
                "title": result["name"],
                "link": result["url"],
                "snippet": result["snippet"],
            }
            for result in results
        ],
    )


def google_search(
    question: str,
    api_key: str,
    cse_id: str,
    num_results: int = 10,
    **kwargs: Any,
) -> ServiceResponse:
    """
    Search question in Google Search API and return the searching results

    Args:
        question (`str`):
            The search query string.
        api_key (`str`):
            The API key provided for authenticating with the Google Custom
            Search JSON API.
        cse_id (`str`):
            The unique identifier of a programmable search engine to use.
        num_results (`int`, defaults to `10`):
            The number of search results to return.
        **kwargs (`Any`):
            Additional keyword arguments to be included in the search query.
            For more details, please refer to
            https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a list of search results or error information,
        which depends on the `status` variable.
        For each searching result, it is a dictionary with keys 'title',
        'link', and 'snippet'.

    Example:
        .. code-block:: python

            results = google_search(
                'Python programming',
                'your_google_api_key',
                'your_cse_id',
                num_results=2
            )
            if results.status == ServiceExecStatus.SUCCESS:
                for result in results.content:
                    print(result['title'], result['link'], result['snippet'])
    """

    # Google Search API endpoint
    google_search_url = "https://www.googleapis.com/customsearch/v1"

    # Define the query parameters
    params = {
        "q": question,
        "key": api_key,
        "cx": cse_id,
        "num": num_results,
    }
    if kwargs:
        params.update(**kwargs)

    search_results = requests_get(google_search_url, params)

    if isinstance(search_results, str):
        return ServiceResponse(ServiceExecStatus.ERROR, search_results)

    # Retrieve the top search result links
    results = search_results.get("items", [])

    # Return all snippet
    return ServiceResponse(
        ServiceExecStatus.SUCCESS,
        [
            {
                "title": result["title"],
                "link": result["link"],
                "snippet": result["snippet"],
            }
            for result in results
        ],
    )
