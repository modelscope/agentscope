# -*- coding: utf-8 -*-
"""Module for Retrieval node related functions."""
import json
import os
import time
import uuid
from typing import Dict, Any, Generator

from .node import Node
from .utils import NodeType
from ...core.node_caches.workflow_var import WorkflowVariable, DataType

from app.db.init_db import get_session
from app.services.retrieval_service import RetrievalService


class RetrievalNode(Node):
    """
    A node responsible for retrieving data from a knowledge base using a
    specified retriever. Supports reranking when multiple knowledge bases
    are queried.

    Attributes:
        node_type (str): The type of the node, set to Retrieval.
    """

    node_type: str = NodeType.RETRIEVAL.value

    def _execute(self, **kwargs: Any) -> Generator:
        start_time = int(time.time() * 1000)
        query = self.sys_args["input_params"][0]["value"]

        node_param = self.sys_args["node_param"]

        knowledge_base_ids = node_param["knowledge_base_ids"]
        knowledge_base_ids = [uuid.UUID(_) for _ in knowledge_base_ids]
        top_k = node_param["top_k"]
        similarity_threshold = node_param["similarity_threshold"]

        nodes = []
        try:
            for session in get_session():
                retrieval_service = RetrievalService(
                    session=session,
                )
                nodes = retrieval_service.retrieve(
                    query=query,
                    knowledge_base_ids=knowledge_base_ids,
                    top_k=top_k,
                    score_threshold=similarity_threshold,
                    # api_key=os.getenv("DASHSCOPE_API_KEY"),
                )
        except Exception as e:
            self.logger.query_error(
                request_id=self.request_id,
                message=f"Failed to retrieve from knowledge base: {str(e)}",
            )

        result = [
            # json.dumps(
            {
                "doc_id": node.metadata.get("document_id", ""),
                "doc_name": node.metadata.get("document_name", ""),
                "title": node.metadata.get("title", ""),
                "text": node.get_content(),
                "score": node.get_score(),
                "page_number": node.metadata.get("page_number", ""),
                "chunk_id": node.metadata.get("chunk_id", ""),
                "node_id": node.id_,
            }
            # )
            for node in nodes
        ]
        # "rewrite_query": query,

        node_exec_time = str(int(time.time() * 1000) - start_time) + "ms"
        yield [
            WorkflowVariable(
                name="chunk_list",
                content=result,
                source=self.node_id,
                data_type=DataType.ARRAY_OBJECT,
                input={"input": query},
                output={"chunk_list": result},
                output_type="json",
                node_type=self.node_type,
                node_name=self.node_name,
                node_exec_time=node_exec_time,
            ),
        ]

    def _mock_execute(self, **kwargs: Any) -> Generator:
        yield [
            WorkflowVariable(
                name="chunk_list",
                content={
                    "chunkList": [
                        {
                            "content": "Mock content.",
                            "title": "Mock title.",
                            "documentName": "Mock document name.",
                            "score": "Mock score.",
                        },
                    ],
                    "rewriteQuery": "Mock query",
                },
                source=self.node_id,
                data_type=DataType.OBJECT,
                input=self.sys_args.get("input_params"),
                node_type=self.node_type,
                node_name=self.node_name,
            ),
        ]

    def compile(self) -> Dict[str, Any]:
        """
        Compiles the retrieval node into a structured dictionary containing
        imports, initializations, and execution logic for performing data
        retrieval and optional reranking.

        Returns:
            A dictionary with sections for imports, initializations, and execs.
        """
        retriever_str = self.build_graph_var_str("retriever")
        nodes_list_name = self.build_graph_var_str("node_list")
        dashscope_rerank_str = self.build_graph_var_str("dashscope_rerank")
        knowledge_base_ids = self.sys_args["node_param"]["knowledge_base_ids"]
        top_k = self.sys_args["node_param"]["top_k"]
        query = self.build_var_str(
            self.sys_args["input_params"][0],
        )

        import_list = [
            "import os",
            "from llama_index.indices.managed.dashscope.retriever "
            "import DashScopeCloudRetriever",
        ]

        if len(knowledge_base_ids) > 1:
            import_list.extend(
                [
                    "import dashscope",
                    "from llama_index.postprocessor.dashscope_rerank import"
                    " DashScopeRerank",
                ],
            )
            init_str = """
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
"""
            execs_str = f"""
{nodes_list_name} = []

for idx in {knowledge_base_ids}:
    {retriever_str} = DashScopeCloudRetriever(
        index_name=idx,
        rerank_top_n={top_k},
        enable_rewrite=True,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    )

    {nodes_list_name}.extend({retriever_str}.retrieve("{query}"))

{dashscope_rerank_str} = DashScopeRerank(
    top_n={top_k},
)
nodes = dashscope_rerank.postprocess_nodes(
    {nodes_list_name},
    query_str="{query}"
)

{self.build_graph_var_str("result")} = {{
    "chunkList": [
        {{
            "content": node.node.get_content(),
            "title": node.node.metadata.get("title", ""),
            "documentName": node.node.metadata.get("doc_name", ""),
            "score": node.get_score(),
        }}
        for node in nodes
    ],
    "rewriteQuery": {query},
}}
"""
        else:
            init_str = f"""
{retriever_str} = DashScopeCloudRetriever(
    index_name="{knowledge_base_ids[0]}",
    rerank_top_n={top_k},
    enable_rewrite=True,
    api_key=os.getenv("DASHSCOPE_API_KEY"),
)
"""
            execs_str = f"""
nodes = {retriever_str}.retrieve({query})
{self.build_graph_var_str("result")} = {{
    "chunkList": [
        {{
            "content": node.node.get_content(),
            "title": node.node.metadata.get("title", ""),
            "documentName": node.node.metadata.get("doc_name", ""),
            "score": node.get_score(),
        }}
        for node in nodes
    ],
    "rewriteQuery": {query},
}}
{self.build_node_output_str(self.build_graph_var_str("result"), str)}
"""

        return {
            "imports": import_list,
            "inits": [init_str],
            "execs": [execs_str],
            "increase_indent": False,
        }
