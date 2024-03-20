# -*- coding: utf-8 -*-
"""parsing and digesting the web pages"""
from typing import Optional, Union
import requests
from loguru import logger

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models.model import ModelWrapperBase
from agentscope.prompt import PromptEngine, PromptType


DEFAULT_SYS_PROMPT = (
    "You're a web page analyser. You job is to extract important"
    "and useful information from html or webpage description.\n"
)

DEFAULT_SUMMARY_PROMPT = (
    "You're a web page analyser. You job is to summarize the "
    "content of a webpage.\n"
)

DEFAULT_SPLIT_LEVEL = [
    ("h1", "h1"),
    ("h2", "h1"),
]


def webpage_digest(
    url: str,
    model: Optional[ModelWrapperBase] = None,
    prompt_type: Optional[PromptType] = PromptType.LIST,
    html_split_levels: Optional[tuple[str]] = ("h1", "h2"),
    digest_prompt: Optional[str] = DEFAULT_SYS_PROMPT,
    digest_summary_prompt: Optional[str] = DEFAULT_SUMMARY_PROMPT,
) -> ServiceResponse:
    """Function for parsing and digesting the web page.
    Args:
        url (str): the url of the web page
        model (Optional[ModelWrapperBase]): the model that is
            used to digest the web page content.
        prompt_type (Optional[PromptEngine]): how the prompt engine
            compose the messages.
        html_split_levels (Optional[tuple[str]):
            In case the webpage is too long, this
            parameter is for splitting the html file.
            Default will split a html file at 'h1' and 'h2' levels,
            and feed each partition to model to digest.
        digest_prompt (Optional[str]): prompt for
            the model to analyze the webpage content
        digest_summary_prompt  (Optional[str]): prompt for
            the model to summarize the webpage content

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
                        "split_info": {'h1': 'Foo'}
                        "digested_text": "model digested info for
                                        content under h1"
                    },
                    {
                        "split_info": "summary"
                        "digested_text": "model summarize info for
                                        the whole page"
                    }
                ]
                If `model` is None, this will be an empty list.
                "split_info" is the header of the split,  "digested_text"
                is the digested content of the split.
                There is a special "split_info": "summary" for summarizing
                 the content of all text information on web page.
    """
    html = requests.get(url)
    logger.info(f"Get content from {url}...")
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
    logger.info(f"Parse text info from {url}, save to 'html_text_content'")

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
    logger.info(f"Parse href links from {url}, save to 'href_links'")

    # split the webpage and feed them to a model for analysis
    model_digested = []
    if model is not None:
        logger.info(f"Start using model to digest {url}")
        prompt_engine = PromptEngine(model=model, prompt_type=prompt_type)

        def compose_prompt(
            instruction: Optional[str],
            content: Optional[str],
        ) -> Union[str, list[dict]]:
            """simply compose to feed model"""
            sys_msg = {
                "name": "system",
                "role": "system",
                "content": instruction or " ",
            }
            info_msg = {
                "name": "user",
                "role": "user",
                "content": content or " ",
            }
            return prompt_engine.join(sys_msg, info_msg)

        all_text = ""
        if html_split_levels is None:
            # set the default splitting granularity to h1 and h2 in html
            html_split_levels = ("h1", "h2")
        split_levels = [(s, s) for s in html_split_levels]
        html_splitter = HTMLHeaderTextSplitter(
            headers_to_split_on=split_levels,
        )
        html_header_splits = html_splitter.split_text(html_doc.page_content)
        # ask the model to analyze all split parts
        for split in html_header_splits:
            if len(split.page_content) == 0:
                pass
            prompt = compose_prompt(digest_prompt, split.page_content)
            analysis_res = model(messages=prompt)
            if analysis_res.text:
                model_digested.append(
                    {
                        "split_info": split.metadata,
                        "digested_text": analysis_res.text,
                    },
                )
            all_text += analysis_res.text
        # generate a final summary
        prompt = compose_prompt(digest_summary_prompt, all_text)
        analysis_res = model(messages=prompt)
        if analysis_res.text:
            model_digested.append(
                {
                    "split_info": "summary",
                    "digested_text": analysis_res.text,
                },
            )

    digest_result["model_digested"] = model_digested

    return ServiceResponse(
        status=ServiceExecStatus.SUCCESS,
        content=digest_result,
    )
