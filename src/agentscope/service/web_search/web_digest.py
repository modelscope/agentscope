# -*- coding: utf-8 -*-
"""parsing and digesting the web pages"""
from typing import Optional
import requests

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models.model import ModelWrapperBase
from agentscope.message import Msg


DEFAULT_SYS_PROMPT = (
    "You're a data cleaner. You job is to extract important"
    "and useful information from html or webpage source.\n"
    "Extract useful part from the following:{}"
)

DEFAULT_SPLIT_LEVEL = [
    ("h1", "Header 1"),
    ("h2", "Header 2"),
]


def webpage_digest(
    url: str,
    model: Optional[ModelWrapperBase] = None,
    html_split_levels: Optional[list[tuple[str, str]]] = None,
    digest_prompt: Optional[str] = DEFAULT_SYS_PROMPT,
) -> ServiceResponse:
    """Function for parsing and digesting the web page.
    Args:
        url (str): the url of the web page
        model (Optional[ModelWrapperBase]): the model that is
            used to digest the web page content.
        html_split_levels (Optional[list[tuple[str, str]]]):
            parameters for splitting the html file.
            Default will split a html file at 'h1' and 'h2' levels,
            and feed each partition to model to digest.
        digest_prompt (Optional[str]): prompt for
            the model to analyze the webpage content

    Returns:
        ServiceResponse: containing the following digested content in dict.
            1) "html_text_content": (str)text information on the webpage;
            2) "href_links": (list[dict[str, str]])list of hyper-links
                on the webpage:
                [
                    {
                        "content": $content_in_tag_a
                        "href_link": "https://xxxx"
                    },
                    {
                        "content": $content_in_tag_a
                        "href_link": "https://yyyyy"
                    },
                    ...
                ]
            3) "model_digested": (list[dict[str, str]]) list of LLM
                digested information for each split of the html
                file if `model` is not None
                [
                    {
                        "split_info": $metadata_of_the_split
                        "digested_text": $model_digested_info
                    }
                ]
                If `model` is None, this will be an empty list.
                "split_info" is the title/header of split
                e.g. html_split_levels uses DEFAULT_SPLIT_LEVEL
                then one of them may be {'Header 1': 'Foo'}.
    """
    html = requests.get(url)
    digest_result = {}

    try:
        from langchain.docstore.document import Document
        from bs4 import BeautifulSoup
        from langchain_community.document_transformers import (
            BeautifulSoupTransformer,
        )
        from langchain_text_splitters import HTMLHeaderTextSplitter
    except ImportError as exc:
        raise ImportError(
            "LangChain and BeautifulSoup4 required for processing the "
            "web page without model."
            "Please install with `pip install langchain beautifulsoup4` .",
        ) from exc

    html_doc = Document(page_content=html.text, metadata={"url": url})

    # html to text
    bs_transformer = BeautifulSoupTransformer()
    html_content = bs_transformer.transform_documents([html_doc])
    digest_result["html_text_content"] = html_content[0].page_content

    # obtain links in html
    links = []
    soup = BeautifulSoup(html.text, "html.parser")
    for element in soup.find_all():
        if element.name in ["a"]:
            links.append(
                {
                    "content": element.get_text(),
                    "href_link": element.get("href"),
                },
            )
    digest_result["href_links"] = links

    # split the webpage and feed them to a model for analysis
    model_digested = []
    if model is not None:
        if html_split_levels is None:
            html_split_levels = DEFAULT_SPLIT_LEVEL
        html_splitter = HTMLHeaderTextSplitter(
            headers_to_split_on=html_split_levels,
        )
        html_header_splits = html_splitter.split_text(html_doc.page_content)
        # ask the model to analyze all split parts
        for split in html_header_splits:
            if len(split.page_content) == 0:
                pass
            msg = Msg(
                name="system",
                role="system",
                content=digest_prompt.format(split.page_content),
            )
            analysis_res = model(messages=[msg])
            if analysis_res.text:
                model_digested.append(
                    {
                        "split_info": split.metadata,
                        "digested_text": analysis_res.text,
                    },
                )
        digest_result["model_digested"] = model_digested

    return ServiceResponse(
        status=ServiceExecStatus.SUCCESS,
        content=digest_result,
    )
