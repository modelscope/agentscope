# -*- coding: utf-8 -*-
"""The Retrieval related services"""
import json
import uuid
from typing import Optional, Union, Any
from sqlmodel import Session

import weaviate
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import (
    MetadataFilter,
    FilterOperator,
    MetadataFilters,
    FilterCondition,
)
from llama_index.vector_stores.weaviate import WeaviateVectorStore

from app.dao.knowledge_base_dao import KnowledgeBaseDao
from app.core.model import get_llama_index_embedding_model

from app.core.model import get_llama_index_rerank_model

from .base_service import BaseService
from app.utils.crypto import decrypt_with_rsa
from app.models.provider import ProviderBase
from app.services.provider_service import ProviderService

from app.services.knowledge_base_service import KnowledgeBaseService


class RetrievalService(BaseService[KnowledgeBaseDao]):
    """Service layer for retrieval."""

    _dao_cls = KnowledgeBaseDao

    def __init__(self, session: Session, user_id: uuid.UUID = None):
        super().__init__(session=session)

        self.provider_service = ProviderService(session)

        self.knowledge_base_service = KnowledgeBaseService(
            session=session,
        )

    def retrieve(
        self,
        knowledge_base_ids: Union[uuid.UUID, list[uuid.UUID]],
        query: str,
        api_key: Optional[str] = None,
        account_id: Optional[str] = None,
        retrieval_method: str = "hybrid_search",
        score_threshold: Optional[float] = 0.0,
        rerank_mode: str = "reranking_model",
        rerank_model: Optional[str] = "gte-rerank",
        rerank_model_provider: str = "dashscope",
        weights: Optional[dict] = None,
        top_k: Optional[int] = None,
        **kwargs: Any,
    ) -> list:
        """Retrieval"""

        if not query:
            return []
        if not weights:
            weights = {"semantic": 0.5}
        if isinstance(knowledge_base_ids, uuid.UUID):
            knowledge_base_ids = [knowledge_base_ids]

        if retrieval_method == "keyword_search":
            retrieval_result = self.keyword_search(
                account_id=account_id,
                knowledge_base_ids=knowledge_base_ids,
                query=query,
            )
            return retrieval_result

        retrieval_result = []
        for knowledge_base_id in knowledge_base_ids:
            if not api_key:
                knowledge_base = (
                    self.knowledge_base_service.get_knowledge_base(
                        account_id=account_id,
                        knowledge_base_id=knowledge_base_id,
                    )
                )

                provider_info: ProviderBase = (
                    self.provider_service.get_provider(
                        provider=knowledge_base.index_config[
                            "embedding_provider"
                        ],
                        workspace_id=knowledge_base.workspace_id,
                    )
                )
                assert (
                    provider_info.credential is not None
                ), "Provider credential cannot be None"
                model_credential = json.loads(provider_info.credential)
                api_key = decrypt_with_rsa(model_credential["api_key"])

            if not top_k:
                knowledge_base = (
                    self.knowledge_base_service.get_knowledge_base(
                        account_id=account_id,
                        knowledge_base_id=knowledge_base_id,
                    )
                )
                top_k = knowledge_base.search_config.get("top_k", 5)

            res = self._retrieve(
                account_id=account_id,
                knowledge_base_id=knowledge_base_id,
                retrieval_method=retrieval_method,
                query=query,
                api_key=api_key,
                alpha=weights.get("semantic", 0.5),
                rerank_mode=rerank_mode,
                rerank_model=rerank_model,
                rerank_model_provider=rerank_model_provider,
                top_k=top_k,
                threshold_score=score_threshold,
            )
            retrieval_result.extend(res)
        retrieval_result = sorted(
            retrieval_result,
            key=lambda x: x.score,
            reverse=True,
        )[:top_k]

        return retrieval_result

    def keyword_search(
        self,
        knowledge_base_ids: list[uuid.UUID],
        query: str,
        account_id: Optional[str] = None,
        top_k: int = 5,
    ) -> list:
        """keyword search for one knowledge base"""
        all_chunks = []

        for knowledge_base_id in knowledge_base_ids:
            chunks = self._keyword_search(
                account_id=account_id,
                knowledge_base_id=knowledge_base_id,
                query=query,
                top_k=top_k,
            )
            all_chunks.extend(chunks)

        all_chunks.sort(reverse=True, key=lambda x: x[0])

        return [chunk for score, chunk in all_chunks[:top_k]]

    def _keyword_search(
        self,
        knowledge_base_id: uuid.UUID,
        query: str,
        account_id: Optional[str] = None,
        top_k: int = 5,
    ) -> list:
        """Keyword search"""
        if not query:
            return []
        document_ids = self.dao.get_enabled_document_ids(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        chunks = []
        query_keywords = set(query.lower().split())
        for document_id in document_ids:
            document_chunks = self.dao.get_chunk(
                account_id=account_id,
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
            )
            for chunk in document_chunks:
                intersection_count = len(
                    query_keywords & set(chunk.keywords),
                )
                chunks.append((intersection_count, chunk))

        chunks.sort(reverse=True, key=lambda x: x[0])
        return chunks[:top_k]

    def _retrieve(
        self,
        knowledge_base_id: uuid.UUID,
        query: str,
        api_key: Optional[str],
        retrieval_method: str,
        account_id: Optional[str] = None,
        alpha: float = 0.5,
        rerank_mode: str = "rerank_model",
        rerank_model: Optional[str] = None,
        rerank_model_provider: str = "dashscope",
        top_k: Optional[int] = 5,
        threshold_score: Optional[float] = 0.0,
    ) -> list:
        """retrieve detail"""
        if not query:
            return []

        client = weaviate.connect_to_local()
        assert client.is_ready()

        document_ids = self.dao.get_enabled_document_ids(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        retrieval_nodes = []
        for document_id in document_ids:
            vector_store = WeaviateVectorStore(
                weaviate_client=client,
                index_name="LlamaIndex_" + str(document_id).replace("-", "_"),
            )

            embedding_model_dict = self.dao.get_embedding_model_dict(
                account_id=account_id,
                knowledge_base_id=knowledge_base_id,
            )
            embedding_model_instance = get_llama_index_embedding_model(
                api_key=api_key,
                **embedding_model_dict,
            )

            index = VectorStoreIndex.from_vector_store(
                vector_store,
                embedding_model_instance,
            )

            enabled_filter = MetadataFilter(
                key="enabled",
                value="True",
                operator=FilterOperator.EQ,
            )
            filters = MetadataFilters(
                filters=[enabled_filter],
                condition=FilterCondition.AND,
            )

            if retrieval_method == "semantic_search":
                retriever = index.as_retriever(
                    vector_store_query_mode="default",
                    similarity_top_k=top_k,
                    filters=filters,
                )
            elif retrieval_method == "full_text_search":
                retriever = index.as_retriever(
                    vector_store_query_mode="text_search",
                    similarity_top_k=top_k,
                    filters=filters,
                )
            else:
                retriever = index.as_retriever(
                    vector_store_query_mode="hybrid",
                    similarity_top_k=top_k,
                    alpha=alpha,
                    filters=filters,
                )
            nodes = retriever.retrieve(query)
            retrieval_nodes.extend(nodes)

        retrieval_nodes = sorted(
            retrieval_nodes,
            key=lambda x: x.score,
            reverse=True,
        )

        if threshold_score:
            retrieval_nodes = [
                node
                for node in retrieval_nodes
                if node.score >= threshold_score
            ]

        if retrieval_nodes:
            if rerank_mode == "reranking_model" and rerank_model:
                rerank_model_instance = get_llama_index_rerank_model(
                    rerank_model=rerank_model,
                    rerank_model_provider=rerank_model_provider,
                    api_key=api_key,
                )
                rerank_model_instance.top_n = top_k
                retrieval_nodes = rerank_model_instance.postprocess_nodes(
                    retrieval_nodes,
                    query_str=query,
                )
            else:
                retrieval_nodes = sorted(
                    retrieval_nodes,
                    key=lambda x: x.score,
                    reverse=True,
                )[:top_k]

        client.close()

        return retrieval_nodes
