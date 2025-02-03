# -*- coding: utf-8 -*-
"""
This module is an integration of the Llama index RAG
into AgentScope package
"""
import json
import os.path
from typing import Any, Optional, List

from llama_index.core.data_structs import Node

# search
from llama_index.core.schema import NodeWithScore
from loguru import logger

from agentscope.constants import (
    DEFAULT_CHUNK_SIZE,
)
from agentscope.service import load_web
from agentscope.utils.token_utils import count_openai_token
from agentscope.service import bing_search
from agentscope.rag.knowledge import Knowledge


class BingKnowledge(Knowledge):
    """
    This class is a wrapper with the Bing search api .
    """

    knowledge_type = "bing_knowledge"

    def __init__(
        self,
        knowledge_id: str,
        knowledge_config: Optional[dict] = None,
        to_load_web: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        This class is a knowledge wrapper using Bing Search to
        retrieve information online.

        Args:
            knowledge_id (str):
                The id of the RAG knowledge unit.
            knowledge_config (dict):
                The configuration for using online search
            load_web (bool):
                whether to load the web page content. Currently only supports
                loading content in "p" tags
        """
        super().__init__(
            knowledge_id=knowledge_id,
            knowledge_config=knowledge_config,
            **kwargs,
        )
        self.to_load_web = to_load_web

    def _init_rag(
        self,
        **kwargs: Any,
    ) -> Any:
        pass

    def retrieve(
        self,
        query: Any,
        similarity_top_k: int = None,
        to_list_strs: bool = False,
        **kwargs: Any,
    ) -> List[Any]:
        """
        retrieve content from bing search and format them in list
        """
        search_config = self.knowledge_config.get("bing_search_config", {})
        query_prefix = search_config.get("query_prefix", "")
        query = query_prefix + " " + query
        logger.info(f"bing query: {query}")
        key = os.getenv("BING_SEARCH_KEY", "")
        if len(key) == 0:
            raise ValueError(
                "Bing search key is empty."
                "Need to set bing key as environment variable:"
                "`export BING_SEARCH_KEY=xxxx` ",
            )
        bing_result = bing_search(
            query,
            api_key=key,
            num_results=similarity_top_k,
        ).content
        node_list = []
        logger.info(f"bing result: {bing_result}")
        if not isinstance(bing_result, list):
            return node_list

        for info_piece in bing_result:
            url = info_piece.get("link", "")
            bing_title = info_piece.get("title", "")
            info = {
                "Title": bing_title,
                "Description": info_piece.get("snippet", ""),
            }

            if self.to_load_web:
                try:
                    extracted = load_web(
                        url,
                        html_selected_tags=["p"],
                    ).content["html_to_text"]
                except (NotImplementedError, TypeError, KeyError) as e:
                    logger.warning(f"Load web page fail: {e}")
                    extracted = ""
                try:
                    token = count_openai_token(extracted, model="gpt-4-0613")
                except NotImplementedError as e:
                    logger.warning(e)
                    continue
                if token > DEFAULT_CHUNK_SIZE - 100:
                    extracted = extracted[: DEFAULT_CHUNK_SIZE - 100]
                info["additional_info"] = extracted

            info["Reference"] = url
            content = json.dumps(info, ensure_ascii=False)
            node_list.append(
                NodeWithScore(
                    node=Node(
                        text=content,
                        metadata={"file_path": url},
                    ),
                    score=1.0,
                ),
            )

        if to_list_strs:
            results = []
            for node in node_list:
                results.append(node.get_text())
            return results

        return node_list

    @classmethod
    def default_config(cls, **kwargs: Any) -> dict:
        """
        Return a default config for a knowledge class.
        """
        return {}

    @classmethod
    def build_knowledgebase_instance(
        cls,
        knowledge_id: str,
        knowledge_config: Optional[dict] = None,
        to_load_web: bool = False,
        **kwargs: Any,
    ) -> "Knowledge":
        """
        A constructor to build a knowledge base instance.
        Args:
            knowledge_id (str):
                The id of the knowledge instance.
            knowledge_config (dict):
                The configuration to the knowledge instance.
        """
        return cls(
            knowledge_id=knowledge_id,
            knowledge_config=knowledge_config,
            to_load_web=to_load_web,
        )
