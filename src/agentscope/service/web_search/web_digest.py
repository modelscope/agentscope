# -*- coding: utf-8 -*-
"""parsing and digesting the web pages"""
import json
from urllib.parse import urlparse
from typing import Optional, Callable, Sequence
import requests
from loguru import logger


from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models.model import ModelWrapperBase
from agentscope.service import summarization


DEFAULT_WEB_SYS_PROMPT = (
    "You're a web page analyser. You job is to extract important"
    "and useful information from html or webpage description.\n"
)


def is_valid_url(url: str) -> bool:
    """
    Use regex to check if a URL is valid
    Args:
        url (str): string to be checked

    Returns:
        bool: True if url is valid, False otherwise
    """
    # This regex pattern is designed to match most common URLs.
    try:
        result = urlparse(url)
        # Check if the URL has both a scheme
        # (e.g., "http" or "https") and a netloc (domain).
        return all([result.scheme, result.netloc])
    except ValueError:
        return False  # A ValueError indicates that the URL is not valid.


def load_web(
    url: str,
    keep_raw: bool = True,
    html_selected_tags: Optional[Sequence[str]] = None,
    html_parse_func: Optional[Callable] = None,
    timeout: int = 5,
) -> ServiceResponse:
    """Function for parsing and digesting the web page.
    Args:
        url (str): the url of the web page
        keep_raw (bool):
            Whether to keep raw HTML. If True, the content is
            stored with key "raw".
        html_selected_tags (Optional[Sequence[str]]):
            the text in elements of `selected_tags` will
            be extracted and stored with "selected_tags_text"
            key in return.
        html_parse_func (Optional[Callable]):
            if "html_parse_func" is not None, then the
            `html_parse_func` will be invoked with the response
            text as input. The result is stored with
            `self_define_func` key
        timeout (int): timeout parameter for requests.

    Returns:
        `ServiceResponse`: If successful, `ServiceResponse` object is returned
        with `content` field is a dict, where keys are subset of
        {"raw", "self_define_func", "selected_tags_text"}
         For example, `content` field is
        {
            "raw": raw_content_of_web,
            "selected_tags_text":
                processed_text_content_of_the_selected_tags,
        }

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
        response = requests.get(url=url, headers=header, timeout=timeout)
        if response.status_code == 200:
            content_type = response.headers["Content-Type"].lower()
            if "html" in content_type:
                return parse_html(
                    response.text,
                    keep_raw,
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
                ServiceExecStatus.ERROR,
                content="",
            )
    except Exception as e:
        logger.warning(e)
        return ServiceResponse(ServiceExecStatus.ERROR, content="")


def parse_html(
    html_text: str,
    keep_raw: bool = True,
    html_selected_tags: Optional[Sequence[str]] = None,
    html_parse_func: Optional[Callable] = None,
) -> ServiceResponse:
    """
    Parse the obtained HTML file.
    Args:
        html_text (str):
            HTTP response text
        keep_raw (bool):
            Whether to keep raw HTML. If True, the content is
            stored with key "raw".
        html_selected_tags (Optional[Sequence[str]]):
            the text in elements of `selected_tags` will
            be extracted and stored with "selected_tags_text"
            key in return.
        html_parse_func (Optional[Callable]):
            if "html_parse_func" is not None, then the
            `html_parse_func` will be invoked with the response
            text as input. The result is stored with
            `self_define_func` key

    Returns:
        `ServiceResponse`: If successful, `ServiceResponse` object is returned
        with `content` field is a dict, where keys are subset of
        {"raw", "self_define_func", "selected_tags_text"}
         For example, `content` field is
        {
            "raw": raw_content_of_web,
            "selected_tags_text":
                processed_text_content_of_the_selected_tags,
        }
    """
    results = {}

    if keep_raw:
        results["raw"] = html_text

    if html_parse_func is not None:
        results["self_define_func"] = html_parse_func(html_text)
    if html_selected_tags:
        logger.info(
            f"extracting text information from tags: " f"{html_selected_tags}",
        )
        try:
            from bs4 import BeautifulSoup, NavigableString, Tag
        except ImportError as exc:
            raise ImportError(
                "BeautifulSoup4 is required for processing the "
                "web page without model."
                "Please install with `pip install bs4` .",
            ) from exc

        doc = BeautifulSoup(html_text, "html.parser")

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
                            text += f"[{child.strip()}]({href})"
                    else:
                        text += child.text
            return " ".join(text.split())

        text_parts = ""
        for element in doc.find_all(recursive=True):
            if element.name in html_selected_tags:
                text_parts += get_navigable_strings(element).strip(" \n\t")
                element.decompose()
        results["selected_tags_text"] = text_parts

    return ServiceResponse(
        status=ServiceExecStatus.SUCCESS,
        content=results,
    )


def digest_webpage(
    web_text_or_url: str,
    model: ModelWrapperBase = None,
    html_selected_tags: Sequence[str] = ("h", "p", "li", "div", "a"),
    digest_prompt: str = DEFAULT_WEB_SYS_PROMPT,
) -> ServiceResponse:
    """
    Args:
        web_text_or_url (str): preprocessed web text or url to the web page
        model (ModelWrapperBase): the model to digest the web content
        html_selected_tags (Sequence[str]):
            the text in elements of `selected_tags` will
            be extracted and feed to the model
        digest_prompt (str): system prompt for the model to digest
            the web content

    Returns:
        `ServiceResponse`: If successful, `ServiceResponse` object is returned
        with `content` field is filled with the model output.
    """
    if is_valid_url(web_text_or_url):
        # if an url is provided, then
        # load the content of the url first
        if html_selected_tags is None or len(html_selected_tags) == 0:
            html_selected_tags = ["h", "p", "li", "div", "a"]
        response = load_web(
            url=web_text_or_url,
            html_selected_tags=html_selected_tags,
        )
        if response.status == ServiceExecStatus.SUCCESS:
            web_text = response.content["selected_tags_text"]
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
