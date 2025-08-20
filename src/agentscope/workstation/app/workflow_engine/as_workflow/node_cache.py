# -*- coding: utf-8 -*-
# pylint: disable=R0912
"""Node result"""
import json
from typing import Any, Union, Optional, List

import networkx as nx
from agentscope.message import Msg
from agentscope.utils.common import _guess_type_by_extension
from ..core.node_caches.node_cache_handler import NodeCache
from ..core.status import Status
from ..core.node_caches import NodeCacheHandler
from ..core.node_caches.workflow_var import WorkflowVariable, DataType


class AgentscopeNodeCacheHandler(NodeCacheHandler):
    """Node cache for output"""

    def create_node_cache(
        self,
        status: str,
        message_str: Optional[str] = None,
    ) -> NodeCache:
        node_cache = NodeCache(status=status)
        if message_str:
            node_cache.message = message_str
        return node_cache

    def update_status(self, node_cache: NodeCache, status: str) -> None:
        node_cache.status = status

    def update_message(self, node_cache: NodeCache, message_str: str) -> None:
        node_cache.message = message_str

    @staticmethod
    def retrieve_node_input(
        node_id: str,
        global_cache: dict,
        graph: Optional[nx.DiGraph] = None,
    ) -> Optional[Union[str, dict]]:
        # Build a key-content map
        variable_value_map = {}
        for key, node_output in global_cache.items():
            if key == "memory":
                continue
            node_results = node_output.results
            if not node_results:
                continue

            for workflow_variable in node_results:
                variable_value_map[
                    workflow_variable.key
                ] = workflow_variable.content
        if graph:
            in_edge_data = list(graph.in_edges(node_id, data=True))
            edge_cnt = len(in_edge_data)
            skip_cnt = 0

            # Process incoming edges for the specified node
            for from_node_id, _, _ in in_edge_data:
                from_node_cache = global_cache.get(from_node_id)

                # Some node might not output to global_cache
                if not from_node_cache:
                    continue

                # Broadcast Skip Signal
                if from_node_cache.status == Status.SKIP.value:
                    skip_cnt += 1
                    continue

                # We do not verify all targets here, since all variable are
                # the same
                if from_node_cache.results:
                    targets = from_node_cache.results[0].get("targets")

                    # if targets is None, do not skip
                    if targets and node_id not in targets:
                        skip_cnt += 1

            # Start node doesn't have any incoming edges
            if edge_cnt and (skip_cnt == edge_cnt):
                return Status.SKIP.value

        return variable_value_map

    def convert_node_result_to_cache(
        self,
        result: Any,
        node_id: str,
        status: str,
        graph: nx.DiGraph,
    ) -> NodeCache:
        formatted_results = NodeCache(results=result, node_id=node_id)

        if status:
            formatted_results.status = status
        else:
            formatted_results.status = Status.FAILED.value

        if "message" in result:
            formatted_results.message = result["message"]

        return formatted_results

    def restore_node_results(
        self,
        results: dict,
        messages: Optional[List] = None,
    ) -> dict:
        graph_cache = {}

        for key, value in results.items():
            if key == "memory":
                graph_cache[key] = value
                continue
            graph_cache[key] = NodeCache(
                results=[
                    WorkflowVariable(
                        name=x.name,
                        content=x.content,
                        source=x.source,
                        data_type=x.data_type,
                    )
                    for x in value["results"]
                ],
                node_id=key,
            )

        # Handle sys args
        if messages:
            sys_vars = []
            sys_query_content = messages[-1].get("content")
            if sys_query_content:
                sys_vars.append(
                    WorkflowVariable(
                        name="query",
                        content=sys_query_content,
                        source="sys",
                        data_type=DataType.STRING,
                    ),
                )
            if len(messages) > 1:
                sys_history_list = messages[:-1]
                sys_vars.append(
                    WorkflowVariable(
                        name="historyList",
                        content=sys_history_list,
                        source="sys",
                        data_type=DataType.ARRAY_OBJECT,
                    ),
                )

            # TODO: handle imageList
            if sys_vars:
                graph_cache["sys"] = NodeCache(
                    results=sys_vars,
                    node_id="sys",
                )

        return graph_cache

    def process_msg_result(self, result: Msg) -> dict:
        """
        Process a Msg instance by converting it to a dictionary,
        adding additional data based on the URL, and preparing it for
        further use.

        :param result: instance of Msg
        :return: dictionary with processed message and additional URL data
        """
        txt = result.content
        result_dict = json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
        new_result = {"msg": [result_dict], "text": [txt]}

        self.append_url_types(result, new_result)

        return new_result

    def append_url_types(self, result: Msg, new_result: dict) -> None:
        """
        Append URL types to the result dictionary based on URL extensions.

        :param result: Msg instance that might contain URLs.
        :param new_result: Dictionary where URL data will be added based on
            their types.
        """
        if result.url:
            urls = [result.url] if isinstance(result.url, str) else result.url
            for url in urls:
                typ = _guess_type_by_extension(url)
                if typ in new_result:
                    new_result[typ].append(url)
                else:
                    new_result[typ] = [url]
