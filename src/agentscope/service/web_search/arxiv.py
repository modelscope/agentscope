# -*- coding: utf-8 -*-
"""Search papers in arXiv API. This implementation refers to the repository
https://github.com/lukasschwab/arxiv.py, which is MIT licensed.
"""
import json
import re
import time
import urllib
from calendar import timegm
from datetime import datetime, timezone
from typing import List, Optional, Union

try:
    import feedparser
except ImportError:
    feedparser = None
from loguru import logger

from agentscope.service.service_response import (
    ServiceResponse,
    ServiceExecStatus,
)

ARXIV_SEARCH_URL = "http://export.arxiv.org/api/query?{parameters_str}"

LOGIC_OPERATORS = ["ANDNOT", "AND", "OR"]

SYMBOLS = ["(", ")"]

QUERY_PREFIX = ["all:", "ti:", "au:", "abs:", "co:", "jr:", "cat:", "rn:"]


class _Result(dict):
    """The class for arXiv search results."""

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    id: str
    """A url of the form `https://arxiv.org/abs/{id}`."""

    title: str
    """The title of the result."""

    updated: str
    """When the result was last updated."""

    published: str
    """When the result was published."""

    summary: str
    """The summary of the search result."""

    authors: List[str]
    """The authors of the search result."""

    comment: Optional[str]
    """The authors' comment if present."""

    primary_category: Optional[str]
    """The result's primary arXiv category. See [arXiv: Category
    Taxonomy](https://arxiv.org/category_taxonomy)."""

    tags: List[str]
    """All of the result's tags. See [arXiv: Category
    Taxonomy](https://arxiv.org/category_taxonomy)."""

    journal_ref: Optional[str]
    """A journal reference if present."""

    doi: Optional[str]
    """A URL for the resolved DOI to an external resource if present."""

    def __init__(
        self,
        entry_id: str,
        title: str,
        updated: str,
        published: str,
        summary: str,
        authors: List[str],
        pdf_url: Optional[str] = None,
        comment: Optional[str] = None,
        primary_category: Optional[str] = None,
        tags: List[str] = None,
        journal_ref: Optional[str] = None,
        doi: Optional[str] = None,
    ) -> None:
        """The class for arXiv search results."""
        self.entry_id = entry_id
        self.title = title
        self.updated = updated
        self.published = published
        self.summary = summary
        self.authors = authors
        self.pdf_url = pdf_url
        self.comment = comment
        self.primary_category = primary_category
        self.tags = tags
        self.journal_ref = journal_ref
        self.doi = doi

    def __str__(self) -> str:
        cleaned_dict = {}
        for key in self:
            if self[key] is not None:
                cleaned_dict[key] = self[key]
        return json.dumps(cleaned_dict, ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()


def _parse_pdf_url(links: List) -> Union[str, None]:
    """Parse the pdf url from the links."""
    for link in links:
        if link.get("title") == "pdf":
            return link.get("href")
    return None


def _parse_timestamp(timestamp: time.struct_time) -> str:
    """Parse the timestamp to a string."""
    timestamp = datetime.fromtimestamp(timegm(timestamp), tz=timezone.utc)
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def _clean_arxiv_search_results(result: dict) -> dict:
    """Clean the arXiv search results, and remove unnecessary information."""
    feed = result.feed

    # Basic information
    cleaned_dict = {
        "updated": _parse_timestamp(feed.updated_parsed),
        "opensearch_total_results": int(feed.opensearch_totalresults),
        "opensearch_start_index": int(feed.opensearch_startindex),
        "opensearch_itemsperpage": int(feed.opensearch_itemsperpage),
    }

    # Entries
    entries = []
    for entry in result.entries:
        title = "0"
        if hasattr(entry, "title"):
            title = entry.title
        else:
            logger.warning(
                "Result %s is missing title attribute; defaulting to '0'",
                entry.id,
            )

        tags = [tag.get("term") for tag in entry.tags]
        if len(tags) == 0:
            tags = None

        entry_dict = _Result(
            # Basic properties
            entry_id=entry.id,
            title=title,
            updated=_parse_timestamp(entry.updated_parsed),
            published=_parse_timestamp(entry.published_parsed),
            summary=entry.summary,
            authors=[author.name for author in entry.authors],
            # Optional properties
            pdf_url=_parse_pdf_url(entry.links),
            comment=entry.get("arxiv_comment"),
            primary_category=entry.arxiv_primary_category.get("term"),
            tags=tags,
            journal_ref=entry.get("arxiv_journal_ref"),
            doi=entry.get("arxiv_doi"),
        )

        entries.append(entry_dict)

    cleaned_dict["entries"] = entries

    return cleaned_dict


def _reformat_query(query: str) -> str:
    """Reformat the query string for arxiv search, refer to
    https://info.arxiv.org/help/api/user-manual.html."""
    delimiter_regex = (
        "("
        + "|".join(
            map(re.escape, LOGIC_OPERATORS + QUERY_PREFIX + SYMBOLS),
        )
        + ")"
    )

    parts = re.split(delimiter_regex, query)

    parts = [part.strip() for part in parts if part.strip()]

    for i, part in enumerate(parts):
        if part not in LOGIC_OPERATORS + QUERY_PREFIX + SYMBOLS:
            # Add double quotes if it does not contain double quotes
            part = part.replace('"', "%22").replace(" ", "+")

            if not part.startswith("%22"):
                part = f"%22{part}"
            if not part.endswith("%22"):
                part = f"{part}%22"
            parts[i] = part
        elif part in SYMBOLS:
            parts[i] = part.replace("(", "%28").replace(")", "%29")
        elif part in LOGIC_OPERATORS:
            parts[i] = f"+{part}+"

    refined_query = "".join(parts)

    return refined_query


def arxiv_search(
    search_query: str,
    id_list: List[str] = None,
    start: int = 0,
    max_results: Optional[int] = None,
) -> ServiceResponse:
    """Search arXiv paper by a given query string.

    Args:
        search_query (`str`):
            The query string, supporting prefixes "all:", "ti:", "au:",
            "abs:", "co:", "jr:", "cat:", and "rn:", boolean operators "AND",
            "OR" and "ANDNOT". For example, searching for papers with
            title "Deep Learning" and author "LeCun" by a
            search_query ti:"Deep Learning" AND au:"LeCun"
        id_list (`List[str]`, defaults to `None`):
            A list of arXiv IDs to search.
        start (`int`, defaults to `0`):
            The index of the first search result to return.
        max_results (`Optional[int]`, defaults to `None`):
            The maximum number of search results to return.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a list of search results or error information,
        which depends on the `status` variable.
    """

    if feedparser is None:
        raise ImportError(
            "The `feedparser` module is not installed. Please install it by "
            "running `pip install feedparser`.",
        )

    # construct url
    search_query = _reformat_query(search_query)

    parameters = {"search_query": search_query}

    if id_list:
        parameters["id_list"] = ",".join(id_list)

    if start > 0:
        parameters["start"] = str(start)

    if max_results:
        parameters["max_results"] = str(max_results)

    parameters_str = "&".join([f"{k}={v}" for k, v in parameters.items()])

    url = ARXIV_SEARCH_URL.format(parameters_str=parameters_str)

    try:
        logger.debug(f"Searching arXiv by url: {url}")

        with urllib.request.urlopen(url) as data:
            # Parse the results by feedparser
            feedparser_dict = feedparser.parse(data.read().decode("utf-8"))

        # Remove unnecessary information
        results = _clean_arxiv_search_results(feedparser_dict)

        if data.code == 200:
            # Return the searching results
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=results,
            )
        else:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=f"Error: {data.code}, {data}",
            )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=f"Error: {e}",
        )
