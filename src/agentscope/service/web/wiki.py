# -*- coding: utf-8 -*-
"""
Search contents from WikiPedia,
including texts, categories, infotable, table,...
"""

import re


from bs4 import BeautifulSoup

from agentscope.service.service_response import (
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.utils.common import requests_get


def _wiki_api(params: dict) -> dict:
    """Scratch information via Wiki API"""
    url = "https://en.wikipedia.org/w/api.php"
    return requests_get(url, params=params)


def _check_entity_existence(entity: str) -> ServiceResponse:
    """
    Function to check if the eneity exists in Wikipedia
    If yes, continue searching;
    if not, return top 5 similar entities
    
    Args:
        entity (str): searching keywords
        
    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the ServiceExecStatus enum,
        indicating success or error.
        If the entity does not exist, `status`=ERROR
        and return top-5 similar entities in `content`.
        If entity exists, `status`=SUCCESS, return the original entity in `content`.
        
    Example 1 (entity exists):
        .. code-block:: python
        
            _check_entity_existence('Hello')
        
        It returns:
        .. code-block:: python
        
            {
                'status': <ServiceExecStatus.SUCCESS: 1>, 
                'content': {
                    'entity': 'Hello'
                    }
            }
        
    Example 2 (entity does not exist):   
        .. code-block:: python
        
             _check_entity_existence('nihao')
             
        It returns:
        .. code-block:: python
        
            {
                'status': <ServiceExecStatus.ERROR: -1>,
                'content': {
                    'similar_entities': [
                        'Ni Hao',
                        'Ranma ½',
                        'Ni Hao, Kai-Lan',
                        'List of Ranma ½ episodes',
                        'Studio Deen'
                    ]
                }
            }
        
    """
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": entity,
        "format": "json",
    }

    search_data = _wiki_api(search_params)

    if "query" in search_data and "search" in search_data["query"]:
        if search_data["query"]["search"]:
            exact_match = None
            for result in search_data["query"]["search"]:
                if result["title"].lower() == entity.lower():
                    exact_match = result["title"]
                    break
            if not exact_match:
                similar_entities = [
                    result["title"]
                    for result in search_data["query"]["search"][:5]
                ]
                return ServiceResponse(
                    ServiceExecStatus.ERROR,
                    {"similar_entities": similar_entities},
                )
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                {"entity": exact_match},
            )
    return ServiceResponse(
        ServiceExecStatus.ERROR,
        {"error": "Entity not found"},
    )


def wiki_get_category_members(
    entity: str,
    max_members: int = 1000,
    limit_per_request: int = 500,
) -> ServiceResponse:
    """Function to retrieve category members from Wikipedia:Category pages

    Args:
        entity (str): searching keywords
        max_members (int): maximum number of members to output
        limit_per_request (int): number of members retrieved per request

    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the ServiceExecStatus enum,
        indicating success or error.
        If the entity does not exist, `status`=ERROR
        and return top-5 similar entities in `content`.
        If the entity exists, `status`=SUCCESS,
        and return `content` as a list of dicts.
        Keys of each dict:

            "pageid": unique page ID for the member

            "ns": namespace for the member,
                indicating if the corresponding page is Article/User/...

            "title": title of the member

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
                {'pageid': 67911196, 'ns': 0,
                'title': 'Bayesian learning mechanisms'},
                {'pageid': 233488, 'ns': 0, 'title': 'Machine learning'},
                ...]

            }

    """
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{entity}",
        "cmlimit": limit_per_request,  # Maximum number of results per request
        "format": "json",
    }

    members = []
    total_fetched = 0

    while total_fetched < max_members:
        data = _wiki_api(params)
        batch_members = data["query"]["categorymembers"]
        members.extend(batch_members)
        total_fetched += len(batch_members)

        # Check if there is a continuation token
        if "continue" in data and total_fetched < max_members:
            params["cmcontinue"] = data["continue"]["cmcontinue"]
        else:
            break

    # If more members were fetched than max_members, trim the list
    if len(members) > max_members:
        members = members[:max_members]

    if len(members) > 0:
        return ServiceResponse(ServiceExecStatus.SUCCESS, members)

    return ServiceResponse(ServiceExecStatus.ERROR, members)


def wiki_get_infobox(
    entity: str,
) -> ServiceResponse:
    """
    Function to retrieve InfoBox from the WikiPedia page

    Args:
        entity (str): searching keywords

    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the ServiceExecStatus enum,
        indicating success or error.
        If the entity does not exist, `status`=ERROR,
        and return top-5 similar entities in `content`.
        If the entity exists, `status`=SUCCESS,
        and return `content` as a dict containing information in the InfoBox.

    Example:

    .. code-block:: python
    
        infobox_data = wiki_get_infobox(entity="Python (programming language)")
        print(infobox_data)

    It returns content:

    .. code-block:: python
    
    {
        'status': <ServiceExecStatus.SUCCESS: 1>,
        'content':  {'Paradigm': 'Multi-paradigm : object-oriented ...',
                    'Designed\xa0by': 'Guido van Rossum',
                    'Developer': 'Python Software Foundation',
                    'First\xa0appeared': '20\xa0February 1991 ...',
                    'Stable release': '3.12.4 / 6 June 2024 ; ...',
                    'Typing discipline': 'duck , dynamic , strong ; ...',
                    'OS': 'Tier 1 : 64-bit Linux , macOS ; 。。。',
                    'License': 'Python Software Foundation License',
                    'Filename extensions': '.py, .pyw, .pyz, [10] .pyi, ...',
                    'Website': 'python.org'}
    }
    """

    existence_response = _check_entity_existence(entity)
    if existence_response.status == ServiceExecStatus.ERROR:
        return existence_response

    parse_params = {
        "action": "parse",
        "page": entity,
        "prop": "text",
        "format": "json",
    }

    parse_data = _wiki_api(parse_params)

    if "parse" in parse_data:
        raw_html = parse_data["parse"]["text"]["*"]
        soup = BeautifulSoup(raw_html, "html.parser")
        infobox = soup.find("table", {"class": "infobox"})

        if not infobox:
            return ServiceResponse(ServiceExecStatus.ERROR, None)

        infobox_data = {}
        for row in infobox.find_all("tr"):
            header = row.find("th")
            value = row.find("td")
            if header and value:
                key = header.get_text(" ", strip=True)
                val = value.get_text(" ", strip=True)
                infobox_data[key] = val

        return ServiceResponse(ServiceExecStatus.SUCCESS, infobox_data)
    error_message = parse_data.get("error", {}).get(
        "info",
        "Unknown error occurred",
    )
    return ServiceResponse(
        ServiceExecStatus.ERROR,
        {"error": error_message},
    )


def wiki_get_page_content_by_paragraph(
    entity: str,
    max_paragraphs: int = 1,
) -> ServiceResponse:
    """
    Retrieve content from a Wikipedia page and split it into paragraphs,
    excluding section headers.

    Args:
        entity (str): search word.
        max_paragraphs (int, optional):
            The maximum number of paragraphs to retrieve.
            Default is 1 (retrieve the first paragraph).

    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the ServiceExecStatus enum,
        indicating success or error.
        If the entity does not exist, `status`=ERROR,
        and return top-5 similar entities in `content`.
        If the entity exists, `status`=SUCCESS,
        and return `content` as a list of paragraphs from the Wikipedia page.

    Example:

        .. code-block:: python
        
            wiki_paragraph = wiki_get_page_content_by_paragraph(
                entity="Python (programming language)",
                max_paragraphs=1)
            print(wiki_paragraph)

        It will return content:
        .. code-block:: python
        
            {
                'status': <ServiceExecStatus.SUCCESS: 1>,
                'content': ['Python is a high-level...']
            }

    """
    existence_response = _check_entity_existence(entity)
    if existence_response.status == ServiceExecStatus.ERROR:
        return existence_response

    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": True,
        "titles": entity,
        "format": "json",
    }

    data = _wiki_api(params)
    page = next(iter(data["query"]["pages"].values()))
    content = page.get("extract", "No content found.")
    if content == "No content found.":
        return ServiceResponse(ServiceExecStatus.ERROR, content)

    # Split content into paragraphs, including headers
    paragraphs = [
        para.strip()
        for para in content.split("\n\n")
        if para.strip() != ""
    ]

    # Return the specified number of paragraphs
    if max_paragraphs:
        paragraphs = paragraphs[:max_paragraphs]

    return ServiceResponse(ServiceExecStatus.SUCCESS, paragraphs)


def wiki_get_all_wikipedia_tables(
    entity: str,
) -> ServiceResponse:
    """
    Retrieve tables on the Wikipedia page

    Args:
        entity (str): search word.

    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the ServiceExecStatus enum,
        indicating success or error.
        If the entity does not exist, `status`=ERROR,
        and return top-5 similar entities in `content`.
        If the entity exists, `status`=SUCCESS,
        and return `content` as a list of tables from the Wikipedia page.
        Each table is presented as a dict,
        where key is the column name and value is the values for each column.

    Example:

        .. code-block:: python
        
            wiki_table = wiki_get_all_wikipedia_tables(
                entity="Python (programming language)"
                )
            print(wiki_table)

        It will return content:
        .. code-block:: python
        
            {
                'status': <ServiceExecStatus.SUCCESS: 1>,
                'content': [
                            {
                                'Type': ['bool','bytearray',...],
                                'Mutability': ['immutable','mutable',...],
                                ...
                            }
                           ]
            }

    """
    existence_response = _check_entity_existence(entity)
    if existence_response.status == ServiceExecStatus.ERROR:
        return existence_response

    params = {
        "action": "parse",
        "page": entity,
        "prop": "text",
        "format": "json",
    }

    data = _wiki_api(params)
    raw_html = data["parse"]["text"]["*"]

    soup = BeautifulSoup(raw_html, "html.parser")
    tables = soup.find_all("table", {"class": "wikitable"})

    if not tables:
        return ServiceResponse(ServiceExecStatus.ERROR, None)

    all_tables_data = []
    for _, table in enumerate(tables):
        headers = [
            header.get_text(strip=True) for header in table.find_all("th")
        ]
        table_dict = {header: [] for header in headers}

        for row in table.find_all("tr")[1:]:  # Skip the header row
            cells = row.find_all(["td", "th"])
            if len(cells) == len(
                headers,
            ):  # Ensure the row has the correct number of cells
                for i, cell in enumerate(cells):
                    table_dict[headers[i]].append(
                        cell.get_text(strip=True),
                    )

        all_tables_data.append(table_dict)

    return ServiceResponse(ServiceExecStatus.SUCCESS, all_tables_data)


def wiki_get_page_images_with_captions(
    entity: str,
) -> ServiceResponse:
    """
    Function to retrive images and details on the Wikipedia page

    Args:
        entity (str): search word.

    Returns:
        `ServiceResponse`: A dictionary containing `status` and `content`.
        The `status` attribute is from the ServiceExecStatus enum,
        indicating success or error.
        If the entity does not exist, `status`=ERROR,
        and return top-5 similar entities in `content`.
        If the entity exists, `status`=SUCCESS,
        and return the `content` as a list of dict from the Wikipedia page.

        Each dict has:
        'title': title of the image
        'url': link to the image
        'caption': caption of the image

    Example:
        .. code-block:: python
        
            wiki_images = wiki_get_page_images_with_captions(
                entity="Python (programming language)"
                )
            print(wiki_images)

        It will return:

        .. code-block:: python
        
            {
                'status': <ServiceExecStatus.SUCCESS: 1>,
                'content': [{
                'title': 'File:Commons-logo.svg',
                'url': 'https://upload.wikimedia.org...',
                'caption': 'The Wikimedia Commons logo,...'},
                ...
                            ]
            }
    """

    existence_response = _check_entity_existence(entity)
    if existence_response.status == ServiceExecStatus.ERROR:
        return existence_response

    params = {
        "action": "query",
        "prop": "images",
        "titles": entity,
        "format": "json",
    }
    data = _wiki_api(params)
    page = next(iter(data["query"]["pages"].values()))
    images = page.get("images", [])
    if len(images) == 0:
        return ServiceResponse(ServiceExecStatus.ERROR, None)

    image_details = []
    for image in images:
        image_title = image["title"]
        params = {
            "action": "query",
            "titles": image_title,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        }
        data = _wiki_api(params)
        image_page = next(iter(data["query"]["pages"].values()))
        if "imageinfo" in image_page:
            image_info = image_page["imageinfo"][0]
            image_url = image_info.get("url", "")
            extmetadata = image_info.get("extmetadata", {})
            caption = extmetadata.get("ImageDescription", {}).get(
                "value",
                "No caption available",
            )
            image_details.append(
                {
                    "title": image_title,
                    "url": image_url,
                    "caption": caption,
                },
            )

    return ServiceResponse(ServiceExecStatus.SUCCESS, image_details)


def wiki_page_retrieval(
    entity: str,
    max_paragraphs: int = 1,
)-> ServiceResponse:
    """
    Function to retrive different format 
    (infobox, paragraphs, tables, images)
    of information on the Wikipedia page

    Args:
        entity (str): search word.
        max_paragraphs (int, optional):
            The maximum number of paragraphs to retrieve.
            Default is 1 (retrieve the first paragraph).
        
    Returns:
        A dictionary contains retrieved information of different format.
        Keys are four formats: `infobox`, `paragraph`, `table`, `image`.
        The value for each key is a `ServiceResponse` object containing
        `status` and `content`. 
        The `status` attribute is from the ServiceExecStatus enum,
        indicating success or error.
        If the entity does not exist, `status`=ERROR,
        otherwise `status`=SUCCESS.
        The `content` attribute is the retrieved contents 
        if  `status`=SUCCESS. Contents are different for each format.
        `infobox`: Information in the InfoBox.
        `paragraph`: A list of paragraphs from the Wikipedia page. The number 
                of paragraphs is determined by arg `max_paragraphs`.
        `table`: A list of tables from the Wikipedia page. Each table 
                is presented as a dict, where key is the 
                column name and value is the values for each column.
        `image`: A list of dict from the Wikipedia page. 
                Each dict has:
                'title': title of the image
                'url': link to the image
                'caption': caption of the image

    Example:
        .. code-block:: python
        
            wiki_page_retrieval(entity='Hello', max_paragraphs=1)

        It will return:

        .. code-block:: python
        
            {
                'infobox': {
                    'status': <ServiceExecStatus.ERROR: -1>, 
                'content': None
                },
                'paragraph': {
                    'status': <ServiceExecStatus.SUCCESS: 1>,
                    'content': ['Hello is a salutation or greeting in the English language. It is first attested in writing from 1826.']
                },
                'table': {
                    'status': <ServiceExecStatus.ERROR: -1>, 
                    'content': None
                },
                'image': {
                    'status': <ServiceExecStatus.SUCCESS: 1>,
                    'content': [
                        {
                            'title': 'File:Semi-protection-shackle.svg',
                            'url': 'https://upload.wikimedia.org/wikipedia/en/1/1b/Semi-protection-shackle.svg',
                            'caption': '<p>English: <span lang="en"><a href="//en.wikipedia.org/wiki/Wikipedia:Semiprotection" class="mw-redirect" title="Wikipedia:Semiprotection">Semi-protection</a> lock with grey shackle</span>\n</p>'
                        },
                        {
                            'title': 'File:TelephoneHelloNellie.jpg',
                            'url': 'https://upload.wikimedia.org/wikipedia/commons/b/b3/TelephoneHelloNellie.jpg',
                            'caption': 'No caption available'
                        },
                        {
                            'title': 'File:Wiktionary-logo-en-v2.svg',
                            'url': 'https://upload.wikimedia.org/wikipedia/commons/9/99/Wiktionary-logo-en-v2.svg',
                            'caption': 'A logo derived from ...'
                        }
                    ]
                }
            }
                    
    """
    
    infobox_retrieval = wiki_get_infobox(entity=entity)
    paragraph_retrieval = wiki_get_page_content_by_paragraph(
        entity=entity, max_paragraphs=max_paragraphs)
    table_retrieval = wiki_get_all_wikipedia_tables(entity=entity)
    image_retrieval = wiki_get_page_images_with_captions(entity=entity)
    
    total_retrieval = {
        'infobox': infobox_retrieval,
        'paragraph': paragraph_retrieval,
        'table': table_retrieval,
        'image': image_retrieval
    }
    
    return total_retrieval
