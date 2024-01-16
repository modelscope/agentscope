# -*- coding: utf-8 -*-
"""Search question in the web"""
from typing import Optional

from agentscope.service.service_response import ServiceResponse
from agentscope.utils.common import requests_get
from agentscope.constants import ServiceExecStatus


def web_search(
    engine: str,
    question: str,
    api_key: str,
    cse_id: Optional[str] = None,
    num_results: int = 10,
    **kwargs: Optional[dict],
) -> ServiceResponse:
    """
    Perform a web search using a specified search engine (currently supports
    Google and Bing).

    This function abstracts the details of using the Google Custom Search JSON
    API and the Bing Search API. It formulates the correct query based on the
    search engine, handles the API request, and returns the results in a
    uniform format.

    Args:
        engine (`str`):
            The search engine to use. Supported values are 'google' and 'bing'.
        question (`str`):
            The search query string.
        api_key (`str`):
            The API key for authenticating with the chosen search engine's API.
        cse_id (`Optional[str]`, defaults to `None`):
            The unique identifier for a specific Google Custom Search
            Engine. Required only when using Google search.
        num_results (`int`, defaults to `10`):
            The maximum number of search results to return.
        **kwargs (`Optional[dict]`):
            Additional keyword arguments to pass to the search engine API.
            These can include search-specific parameters such as language,
            region, and safe search settings.

    Returns:
        `ServiceResponse`: A dictionary containing the status of the search (
        'success' or 'fail') and the search results. The 'content' key
        within the dictionary contains a list of search results, each result
        is a dictionary with 'title', 'link', and 'snippet', or the error
        information.

    Raises:
        `ValueError`: If an unsupported search engine is specified.
    """
    if engine.lower() == "google":
        if not cse_id:
            raise ValueError(
                "Google Custom Search Engine ID (cse_id) must be "
                "provided for Google search.",
            )
        return _search_google(question, api_key, cse_id, num_results, **kwargs)
    elif engine.lower() == "bing":
        return _search_bing(question, api_key, num_results, **kwargs)
    else:
        raise ValueError(f"Unsupported search engine: {engine}")


def _search_bing(
    question: str,
    bing_api_key: str,
    num_results: int = 10,
    **kwargs: Optional[dict],
) -> ServiceResponse:
    """
    Performs a query search using the Bing Search API and returns searching
    results.

    Args:
        question (`str`):
            The search query string.
        bing_api_key (`str`):
            The API key provided for authenticating with the Bing Search API.
        num_results (`int`, defaults to `10`):
            The number of search results to return.
        **kwargs (`Optional[dict]`):
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

            results = _search_bing(question="What is an agent?",
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
        ```
    """

    # Bing Search API endpoint
    bing_search_url = "https://api.bing.microsoft.com/v7.0/search"

    params = {"q": question, "count": num_results}
    if kwargs:
        params.update(**kwargs)

    headers = {"Ocp-Apim-Subscription-Key": bing_api_key}

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


def _search_google(
    question: str,
    google_api_key: str,
    google_cse_id: str,
    num_results: int = 10,
    **kwargs: Optional[dict],
) -> ServiceResponse:
    """
    Performs a query search using the Google Custom Search JSON API and
    returns searching results.

    Args:
        question (`str`):
            The search query string.
        google_api_key (`str`):
            The API key provided for authenticating with the Google Custom
            Search JSON API.
        google_cse_id (`str`):
            The unique identifier of a programmable search engine to use.
        num_results (`int`, defaults to `10`):
            The number of search results to return.
        **kwargs (`Optional[dict]`):
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

            results = _search_google(
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
        "key": google_api_key,
        "cx": google_cse_id,
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
