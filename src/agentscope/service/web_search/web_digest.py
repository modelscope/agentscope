# -*- coding: utf-8 -*-
"""parsing and digesting the web pages"""
import typing
import json
import re
from typing import Optional, Callable, Literal, Any, Sequence
import requests
from loguru import logger


from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models.model import ModelWrapperBase
from agentscope.service import summarization


DEFAULT_SYS_PROMPT = (
    "You're a web page analyser. You job is to extract important"
    "and useful information from html or webpage description.\n"
)


HTML_PARSING_TYPES = Literal[
    "raw",
    "selected_tags_to_text",
    "self_define_func",
]


def is_valid_url(url: str) -> bool:
    """
    Use regex to check if a URL is valid
    Args:
        url (str): string to be checked

    Returns:
        bool: True if url is valid, False otherwise
    """
    # This regex pattern is designed to match most common URLs.
    regex = re.compile(
        r"^(https?://)"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
        r"[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )  # rest of url
    return re.match(regex, url) is not None


def web_load(
    url: str,
    html_parsing_types: Sequence[HTML_PARSING_TYPES] = tuple(
        ["selected_tags_to_text"],
    ),
    html_selected_tags: Optional[Sequence[str]] = tuple(
        ["h", "p", "li", "div", "a"],
    ),
    html_parse_func: Optional[Callable[[requests.Response], Any]] = None,
) -> ServiceResponse:
    """Function for parsing and digesting the web page.
    Args:
        url (str): the url of the web page
        html_parsing_types (Sequence[HTML_PARSING_TYPES]): parsing/
            pre-processing strategies for the HTML web pages:
                "raw": returns the raw HTML content
                "selected_tags_to_text": returns the text content of
                    selected HTML tags. Tags are set by the
                    `html_select_tags` parameter.
                "self_define_func": user-define processing function
                    for HTML file
        html_selected_tags (Optional[Sequence[str]]): if
            "selected_tags_to_text" is in `html_parsing_types`,
            then the text in `html_select_tags` will be extracted.
            Defaults to ["h", "p", "li", "div", "a"].
        html_parse_func (Optional[Callable[[requests.Response], Any]]): if
            "self_define_func" in `html_parsing_types`, then the
            `html_parse_func` will be invoked with the response as input.
            For example,
                `html_parse_func(requests.get(url))`

    Returns:
        `ServiceResponse`: If successful, `ServiceResponse` object is returned
        with `content` field is a dict, where keys are `html_parsing_types` and
        values are the (pre-processed) parsed content. For example, if
        `html_parsing_types = ['raw', 'selected_tags_to_text']` the
            `content` field is
            {
                "raw": raw_content_of_web,
                "selected_tags_to_text":
                    processed_text_content_of_the_selected_tags,
            }
    """
    header = {
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
        " AppleWebKit/537.36 (KHTML, like Gecko) ",
    }
    try:
        response = requests.get(url=url, headers=header, timeout=5)
        if response.status_code == 200:
            content_type = response.headers["Content-Type"].lower()
            if "html" in content_type:
                return html_parse(
                    response,
                    html_parsing_types,
                    html_selected_tags,
                    html_parse_func,
                )
            elif "pdf" in content_type:
                # TODO: support pdf in the future
                raise NotImplementedError(
                    "Unsupported url to PDF content.",
                )
            elif "json" in content_type:
                return ServiceResponse(
                    ServiceExecStatus.SUCCESS,
                    content=json.loads(response.text),
                )
            elif "image" in content_type:
                # TODO: to support image (gif, jpeg, png) data
                logger.warning(
                    "Current implementation returns binary "
                    "response.content for url with image Content-Types",
                )
                return ServiceResponse(
                    ServiceExecStatus.SUCCESS,
                    content=response.content,
                )
            else:
                raise NotImplementedError(
                    f"Unsupported content type ({content_type}) "
                    f"with url: ({url})",
                )
        else:
            logger.warning(
                f"Fail to load web page, "
                f"status code {response.status_code}",
            )
            return ServiceResponse(
                ServiceExecStatus.SUCCESS,
                content="",
            )
    except Exception as e:
        logger.warning(e)
        return ServiceResponse(ServiceExecStatus.ERROR, content="")


def html_parse(
    html_response: requests.Response,
    html_parsing_types: Sequence[HTML_PARSING_TYPES] = tuple(
        ["selected_tags_to_text"],
    ),
    html_selected_tags: Optional[Sequence[str]] = tuple(
        ["h", "p", "li", "div", "a"],
    ),
    html_parse_func: Optional[Callable] = None,
) -> ServiceResponse:
    """
    Parse the obtained HTML file.
    Args:
        html_response (requests): HTTP response, returned by
            requests.get function
        html_parsing_types (Sequence[HTML_PARSING_TYPES]):
            parsing/pre-processing strategies for the HTML
            web pages, can be any combination of:
                "raw": returns the raw HTML content
                "selected_tags_to_text": returns the text content of
                selected HTML tags. Tags are set by the
                    `html_select_tags` parameter.
                "self_define_func": user-define processing function for
                    HTML file
        html_selected_tags (Optional[Sequence[str]]): if
            "selected_tags_to_text" is in `html_parsing_types`, then the
            text in `html_select_tags` will be extracted.
            Defaults to ["h", "p", "li", "div", "a"].
        html_parse_func (Optional[Callable[[requests.Response], Any]]): if
            "self_define_func" in `html_parsing_types`, then the
            `html_parse_func` will be invoked with the response as
            input. For example,
                `html_parse_func(requests.get(url))`

    Returns:
        `ServiceResponse`: If successful, `ServiceResponse` object is returned
        with `content` field is a dict, where keys are `html_parsing_types` and
        values are the (pre-processed) parsed content. For example, if
        `html_parsing_types = ['raw', 'selected_tags_to_text']` the
        `content` field is
        {
            "raw": raw_content_of_web,
            "selected_tags_to_text":
                processed_text_content_of_the_selected_tags,
        }
    """
    logger.info(f"parsing_types: {html_parsing_types}")
    assert set(html_parsing_types) <= set(
        typing.get_args(HTML_PARSING_TYPES),
    ), (
        f"html_parsing_types must be subset of "
        f"{typing.get_args(HTML_PARSING_TYPES)}"
    )

    results = {}

    for parse_type in html_parsing_types:
        if parse_type == "raw":
            results[str(parse_type)] = html_response.text
        elif parse_type == "self_define_func" and html_parse_func is not None:
            results[str(parse_type)] = html_parse_func(html_response)
        elif parse_type == "selected_tags_to_text":
            logger.info(
                f"extracting text information "
                f"from tags: {html_selected_tags}",
            )
            try:
                from bs4 import BeautifulSoup, NavigableString, Tag
            except ImportError as exc:
                raise ImportError(
                    "BeautifulSoup4 is required for processing the "
                    "web page without model."
                    "Please install with `pip install bs4` .",
                ) from exc

            doc = BeautifulSoup(html_response.text, "html.parser")

            def get_navigable_strings(
                e: Tag,
            ) -> str:
                # pylint: disable=cell-var-from-loop
                text = ""
                for child in e.children:
                    if isinstance(child, Tag):
                        # pylint: disable=cell-var-from-loop
                        text += get_navigable_strings(child).strip(" \n\t")
                    elif isinstance(child, NavigableString):
                        if (e.name == "a") and (href := e.get("href")):
                            if is_valid_url(href):
                                text += f"{child.strip()} ({href})"
                        else:
                            text += child.text
                return " ".join(text.split())

            text_parts = ""
            if html_selected_tags is None:
                html_selected_tags = ["h", "p", "li", "div", "a"]
            for element in doc.find_all(recursive=True):
                if element.name in html_selected_tags:
                    text_parts += get_navigable_strings(element).strip(" \n\t")
                    element.decompose()
            results[str(parse_type)] = text_parts

    return ServiceResponse(
        status=ServiceExecStatus.SUCCESS,
        content=results,
    )


def webpage_digest(
    web_text_or_url: str,
    model: ModelWrapperBase = None,
    digest_prompt: str = DEFAULT_SYS_PROMPT,
) -> ServiceResponse:
    """
    Args:
        web_text_or_url (str): preprocessed web text or url to the web page
        model (ModelWrapperBase): the model to digest the web content
        digest_prompt (str): system prompt for the model to digest
            the web content

    Returns:
        `ServiceResponse`: If successful, `ServiceResponse` object is returned
        with `content` field is filled with the model output.
    """
    if is_valid_url(web_text_or_url):
        # if an url is provided, then
        # load the content of the url first
        response = web_load(
            url=web_text_or_url,
            html_parsing_types=["selected_tags_to_text"],
        )
        if response.status == ServiceExecStatus.SUCCESS:
            web_text = response.content["selected_tags_to_text"]
        else:
            return ServiceResponse(
                status=response.status,
                content=response.content,
            )
    else:
        web_text = web_text_or_url
    return summarization(
        model=model,
        text=web_text,
        system_prompt=digest_prompt,
    )
