# -*- coding: utf-8 -*-
"""parsing and digesting the web pages"""
from typing import Optional
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_text_splitters import HTMLHeaderTextSplitter

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models.model import ModelWrapperBase
from agentscope.message import Msg


DEFAULT_SYS_PROMPT = (
    "You're a data cleaner. You job is to extract useful "
    "training data from html or webpage source.\n"
    "Extract useful part from the following data:{}"
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
    """
    Parses the web page
    :param url: the url of the web page
    :param model: the model that is used to digest the web page content.
    :param html_split_levels:  required parameter for HTMLHeaderTextSplitter
    :param digest_prompt: prompt for the model to analyze the webpage content

    :return: a ServiceResponse containing the digested content

    If the model is None, then the webpage content will be processed
    by **BeautifulSoupTransformer**.
    If the model is not None, then the return consists model digested
    content for each part of the web page split by **HTMLHeaderTextSplitter**
    """
    loader = AsyncChromiumLoader([url])
    htmls = loader.load()

    if model is None:
        # if no model is provided, process with BeautifulSoupTransformer
        bs_transformer = BeautifulSoupTransformer()
        docs_transformed = bs_transformer.transform_documents(htmls)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=docs_transformed[0].page_content,
        )

    # split the webpage and feed them to a model for analysis
    if html_split_levels is None:
        html_split_levels = DEFAULT_SPLIT_LEVEL
    html_splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=html_split_levels,
    )
    html_header_splits = html_splitter.split_text(htmls[0].page_content)
    # ask the model to analyze all split parts
    analysis = ""
    for split in html_header_splits:
        msg = Msg(
            name="system",
            role="system",
            content=digest_prompt.format(split),
        )
        analysis_res = model(messages=[msg])
        if analysis_res.text:
            analysis += analysis_res.text

    return ServiceResponse(
        status=ServiceExecStatus.SUCCESS,
        content=analysis,
    )
