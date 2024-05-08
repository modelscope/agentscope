# -*- coding: utf-8 -*-
""" Search papers, authors and venues in DBLP API.
For detail usage of the DBLP API
please refer to https://dblp.org/faq/How+can+I+fetch+DBLP+data.html
"""
from agentscope.service.service_response import (
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.utils.common import requests_get


def dblp_search_publications(
    question: str,
    num_results: int = 30,
    start: int = 0,
    num_completion: int = 10,
) -> ServiceResponse:
    """Search publications in the DBLP database.

    Args:
        question (`str`):
            The search query string.
        num_results (`int`, defaults to `30`):
            The number of search results to return.
        start (`int`, defaults to `0`):
            The index of the first search result to return.
        num_completion (`int`, defaults to `10`):
            The number of completions to generate.

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
        "f": start,
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
    start: int = 0,
    num_completion: int = 10,
) -> ServiceResponse:
    """Search for author information in the DBLP database.

    Args:
        question (`str`):
            The search query string.
        num_results (`int`, defaults to `30`):
            The number of search results to return.
        start (`int`, defaults to `0`):
            The index of the first search result to return.
        num_completion (`int`, defaults to `10`):
            The number of completions to generate.


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
        "f": start,
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
    start: int = 0,
    num_completion: int = 10,
) -> ServiceResponse:
    """Search for venue information in the DBLP database.

    Args:
        question (`str`):
            The search query string.
        num_results (`int`, defaults to `30`):
            The number of search results to return.
        start (`int`, defaults to `0`):
            The index of the first search result to return.
        num_completion (`int`, defaults to `10`):
            The number of completions to generate.

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
        "f": start,
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
