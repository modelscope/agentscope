# -*- coding: utf-8 -*-
"""Search question in the web"""
from typing import Any, Literal
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


def dblp_search(
    search_type: Literal["publication", "author", "venue"],
    question: str,
    num_results: int = 30,
    first_hit: int = 0,
    num_completion: int = 10,
) -> ServiceResponse:
    """
    Search DBLP database based on the type specified.

    Args:
        search_type (`Literal["publication", "author", "venue"]`):
            Type of search to perform, options are
            "publication", "author", or "venue".
        question (`str`):
            The search query string.
        num_results (`int`, defaults to `30`):
            The total number of search results to fetch.
        firts_hit (`int`, defaults to `0`):
            The first hit in the numbered sequence of search results to return
        num_completion (`int`, defaults to `10`):
            The number of completions to generate for the search query.

    Returns:
        `ServiceResponse`: Depending on the type,
        the response structure will vary.
        The detailed documentation will adjust based on the type parameter.
    """
    mapping = {
        "publication": dblp_search_publications,
        "author": dblp_search_authors,
        "venue": dblp_search_venues,
    }
    if search_type not in mapping:
        raise ValueError(
            f"Invalid type: {type}. Must be one of {list(mapping.keys())}.",
        )
    selected_function = mapping[search_type]
    dblp_search.__doc__ = selected_function.__doc__
    return selected_function(
        question,
        num_results,
        first_hit,
        num_completion,
    )


def dblp_search_publications(
    question: str,
    num_results: int = 30,
    first_hit: int = 0,
    num_completion: int = 10,
) -> ServiceResponse:
    """
    Search publications in the DBLP database
    via its public API and return structured
    publication data.

    Args:
        question (`str`):
            The search query string to look up
            in the DBLP database.
        num_results (`int`, defaults to `30`):
            The number of search results to fetch.
        firts_hit (`int`, defaults to `0`):
            The first hit in the numbered sequence
            of search results to return
        num_completion (`int`, defaults to `10`):
            The number of completions to generate
            for the search query.

    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the ServiceExecStatus enum,
        indicating success or error.
        The `content` is a list of parsed publication data if successful,
        or an error message if failed.
        Each item in the list contains publication information
        includes title, authors, venue, pages, year, type, DOI, and URL.

    Example:
        .. code-block:: python
            search_results = dblp_search_publications(question="Extreme
            Learning Machine",
                                                      num_results=3,
                                                      results_per_page=1,
                                                      num_completion=1)
            print(search_results)

        It returns the following structure:

        .. code-block:: python

            {
                'status': <ServiceExecStatus.SUCCESS: 1>,
                'content': [
                    {
                        'title': 'Power transformers fault diagnosis
                        based on a meta-learning approach to kernel
                        extreme learning machine with opposition-based
                        learning sparrow search algorithm.',
                        'venue': 'J. Intell. Fuzzy Syst.',
                        'pages': '455-466',
                        'year': '2023',
                        'type': 'Journal Articles',
                        'doi': '10.3233/JIFS-211862',
                        'url': 'https://dblp.org/rec/journals/jifs/YuTZTCH23',
                        'authors': 'Song Yu, Weimin Tan, Chengming Zhang,
                        Chao Tang, Lihong Cai, Dong Hu'
                    },
                    {
                        'title': 'Performance comparison of Extreme Learning
                        Machinesand other machine learning methods
                        on WBCD data set.',
                        'venue': 'SIU',
                        'pages': '1-4',
                        'year': '2021',
                        'type': 'Conference and Workshop Papers',
                        'doi': '10.1109/SIU53274.2021.9477984',
                        'url': 'https://dblp.org/rec/conf/siu/KeskinDAY21',
                        'authors': 'Ömer Selim Keskin, Akif Durdu,
                        Muhammet Fatih Aslan, Abdullah Yusefi'
                    }
                ]
            }
    """

    url = "https://dblp.org/search/publ/api"
    params = {
        "q": question,
        "format": "json",
        "h": num_results,
        "f": first_hit,
        "c": num_completion,
    }
    search_results = requests_get(url, params)

    if isinstance(search_results, str):
        return ServiceResponse(ServiceExecStatus.ERROR, search_results)

    hits = search_results.get("result", {}).get("hits", {}).get("hit", [])
    parsed_data = []
    for hit in hits:
        info = hit.get("info", {})
        title = info.get("title", "No title available")
        venue = info.get("venue", "No venue available")
        pages = info.get("pages", "No page information")
        year = info.get("year", "Year not specified")
        pub_type = info.get("type", "Type not specified")
        doi = info.get("doi", "No DOI available")
        url = info.get("url", "No URL available")
        authors = info.get("authors", {}).get("author", [])
        authors_info = info.get("authors", {}).get("author", [])
        if isinstance(
            authors_info,
            dict,
        ):  # Check if there's only one author in a dict format
            authors_info = [authors_info]
        authors = ", ".join(
            [author["text"] for author in authors_info if "text" in author],
        )
        data = {
            "title": title,
            "venue": venue,
            "pages": pages,
            "year": year,
            "type": pub_type,
            "doi": doi,
            "url": url,
            "authors": authors,
        }
        parsed_data.append(data)
    return ServiceResponse(ServiceExecStatus.SUCCESS, parsed_data)


def dblp_search_authors(
    question: str,
    num_results: int = 30,
    first_hit: int = 0,
    num_completion: int = 10,
) -> ServiceResponse:
    """
    Search for author information in the DBLP database
    via its public API and return structured author data.

    Args:
        question (`str`):
            The search query string to look up
            authors in the DBLP database.
        num_results (`int`, defaults to `30`):
            The total number of search results to fetch.
        firts_hit (`int`, defaults to `0`):
            The first hit in the numbered sequence
            of search results to return
        num_completion (`int`, defaults to `10`):
            The number of completions to generate
            for the search query.

    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the
        ServiceExecStatus enum, indicating the success or error of the search.
        The `content` is a list of parsed author
        data if successful, or an error message if failed.
        Each item in the list contains author information
        including their name, URL, and affiliations.

    Example:
        .. code-block:: python

            search_results = dblp_search_authors(question="Liu ZiWei",
                                                 num_results=3,
                                                 results_per_page=1,
                                                 num_completion=1)
            print(search_results)

        It returns the following structure:

        .. code-block:: python

            {
                'status': <ServiceExecStatus.SUCCESS: 1>,
                'content': [
                    {
                        'author': 'Ziwei Liu 0001',
                        'url': 'https://dblp.org/pid/05/6300-1',
                        'affiliations': 'Advantech Singapore Pte Ltd,
                        Singapore;
                        National University of Singapore,
                        Department of Computer Science, Singapore'
                    },
                    {
                        'author': 'Ziwei Liu 0002',
                        'url': 'https://dblp.org/pid/05/6300-2',
                        'affiliations': 'Nanyang Technological University,
                        S-Lab, Singapore;
                        Chinese University of Hong Kong,
                        Department of Information Engineering,
                        Hong Kong'
                    }
                ]
            }
    """
    url = "https://dblp.org/search/author/api"
    params = {
        "q": question,
        "format": "json",
        "h": num_results,
        "f": first_hit,
        "c": num_completion,
    }
    search_results = requests_get(url, params)
    if isinstance(search_results, str):
        return ServiceResponse(ServiceExecStatus.ERROR, search_results)
    hits = search_results.get("result", {}).get("hits", {}).get("hit", [])
    parsed_data = []
    for hit in hits:
        author = hit["info"]["author"]
        author_url = hit["info"]["url"]
        affiliations = []
        notes = hit["info"].get("notes", {})
        note_entries = notes.get("note", [])
        if isinstance(note_entries, dict):
            note_entries = [note_entries]
        for note in note_entries:
            if note["@type"] == "affiliation":
                affiliations.append(note["text"])
        affiliations = "; ".join(affiliations)
        entry_dict = {
            "author": author,
            "url": author_url,
            "affiliations": affiliations,
        }
        parsed_data.append(entry_dict)
    return ServiceResponse(ServiceExecStatus.SUCCESS, parsed_data)


def dblp_search_venues(
    question: str,
    num_results: int = 30,
    first_hit: int = 0,
    num_completion: int = 10,
) -> ServiceResponse:
    """
    Search for venue information in the DBLP database
    via its public API and return structured venue data.

    Args:
        question (`str`):
            The search query string to look up venues in the DBLP database.
        num_results (`int`, defaults to `30`):
            The total number of search results to fetch.
        firts_hit (`int`, defaults to `0`):
            The first hit in the numbered sequence of search results to return
        num_completion (`int`, defaults to `10`):
            The number of completions to generate for the search query.

    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the ServiceExecStatus enum,
        indicating the success or error of the search.
        The `content` is a list of parsed venue data if successful,
        or an error message if failed.
        Each item in the list contains venue information including
        its name, acronym, type, and URL.

    Example:
        .. code-block:: python

            search_results = dblp_search_venues(question="AAAI",
                                                 num_results=1,
                                                 results_per_page=1,
                                                 num_completion=1)
            print(search_results)

        It returns the following structure:

        .. code-block:: python

            {
                'status': <ServiceExecStatus.SUCCESS: 1>,
                'content': [
                    {
                        'venue': 'AAAI Conference on Artificial Intelligence
                        (AAAI)',
                        'acronym': 'AAAI',
                        'type': 'Conference or Workshop',
                        'url': 'https://dblp.org/db/conf/aaai/'
                    },
                    {
                        'venue': ''AAAI Fall Symposium Series',
                        'acronym': 'No acronym available',
                        'type': 'Conference or Workshop',
                        'url': 'https://dblp.org/db/conf/aaaifs/'
                    }
                ]
            }
    """
    url = "https://dblp.org/search/venue/api"
    params = {
        "q": question,
        "format": "json",
        "h": num_results,
        "f": first_hit,
        "c": num_completion,
    }
    search_results = requests_get(url, params)
    if isinstance(search_results, str):
        return ServiceResponse(ServiceExecStatus.ERROR, search_results)

    hits = search_results.get("result", {}).get("hits", {}).get("hit", [])
    parsed_data = []
    for hit in hits:
        venue = hit["info"]["venue"]
        acronym = hit["info"].get("acronym", "No acronym available")
        venue_type = hit["info"].get("type", "Type not specified")
        url = hit["info"]["url"]
        entry_dict = {
            "venue": venue,
            "acronym": acronym,
            "type": venue_type,
            "url": url,
        }
        parsed_data.append(entry_dict)
    return ServiceResponse(ServiceExecStatus.SUCCESS, parsed_data)
