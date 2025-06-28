# -*- coding: utf-8 -*-
"""The utilities for the services layer"""
import json
import uuid
from typing import Optional, Literal, Union

import weaviate

from app.core.model import get_llama_index_embedding_model
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.vector_stores.weaviate import WeaviateVectorStore


def process_weaviate_indexing(
    knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
    document_name: str,
    api_key: str,
    chunk_type: Literal[
        "paragraph",
        "basic",
        "parent-child",
        "full-text",
        "length",
        "page",
        "title",
        "regex",
    ] = "length",
    chunk_ids: list[uuid.UUID] = None,
    chunks: list[str] = None,
    child_chunk_ids: list[list[uuid.UUID]] = None,
    child_chunks: list[list[str]] = None,
    embedding_model: str = None,
    embedding_provider: str = None,
) -> None:
    """Weaviate indexing"""
    client = weaviate.connect_to_local()
    assert client.is_ready()
    try:
        vector_store = WeaviateVectorStore(
            weaviate_client=client,
            index_name="LlamaIndex_" + str(document_id).replace("-", "_"),
        )
        vector_store.clear()

        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
        )

        nodes = []
        if chunk_type != "parent-child":
            for chunk_id, chunk_content in zip(chunk_ids, chunks):
                nodes.append(
                    TextNode(
                        text=chunk_content,
                        metadata={
                            "chunk_id": str(chunk_id),
                            "document_id": str(document_id),
                            "document_name": document_name,
                            "knowledge_base_id": str(knowledge_base_id),
                            "enabled": "True",
                        },
                    ),
                )
        else:
            for chunk_idx, chunk_id in enumerate(chunk_ids):
                for child_chunk_id, child_chunk_content in zip(
                    child_chunk_ids[chunk_idx],
                    child_chunks[chunk_idx],
                ):
                    nodes.append(
                        TextNode(
                            text=child_chunk_content,
                            metadata={
                                "child_chunk_id": str(child_chunk_id),
                                "chunk_id": str(chunk_id),
                                "document_id": str(document_id),
                                "document_name": document_name,
                                "knowledge_base_id": str(knowledge_base_id),
                                "enabled": "True",
                            },
                        ),
                    )

        embedding_model_dict = {
            "embedding_model": embedding_model,
            "embedding_provider": embedding_provider,
        }
        embedding_model_instance = get_llama_index_embedding_model(
            api_key=api_key,
            **embedding_model_dict,
        )

        VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            embed_model=embedding_model_instance,
        )
    except Exception as e:
        raise e
    finally:
        client.close()


def weaviate_delete_index(
    document_ids: Union[list[uuid.UUID], uuid.UUID],
) -> None:
    """Weaviate delete index names"""
    if isinstance(document_ids, uuid.UUID):
        document_ids = [document_ids]
    client = weaviate.connect_to_local()
    assert client.is_ready()
    try:
        for document_id in document_ids:
            vector_store = WeaviateVectorStore(
                weaviate_client=client,
                index_name="LlamaIndex_" + str(document_id).replace("-", "_"),
            )
            vector_store.delete_index()

    finally:
        client.close()


def weaviate_set_chunk_status(
    document_id: uuid.UUID,
    chunk_id: uuid.UUID,
    status: bool,
) -> None:
    """Weaviate disable document"""
    client = weaviate.connect_to_local()
    assert client.is_ready()
    try:
        index_name = "LlamaIndex_" + str(document_id).replace("-", "_")
        collection = client.collections.get(index_name)
        for item in collection.iterator():
            item.properties["enabled"] = str(status)
            node_content = json.loads(item.properties["_node_content"])
            if node_content["metadata"]["chunk_id"] == str(chunk_id):
                node_content["metadata"]["enabled"] = str(status)
                item.properties["_node_content"] = json.dumps(node_content)
                collection.data.update(
                    uuid=item.uuid,
                    properties=item.properties,
                )
    finally:
        client.close()


def weaviate_update_chunk(
    document_id: uuid.UUID,
    chunk_id: uuid.UUID,
    content: str,
    vector: list[float],
    doc_name: Optional[str] = None,
    title: Optional[str] = None,
) -> None:
    """Update chunk content in weaviate"""
    client = weaviate.connect_to_local()
    assert client.is_ready()
    try:
        index_name = "LlamaIndex_" + str(document_id).replace("-", "_")
        collection = client.collections.get(index_name)
        for item in collection.iterator():
            node_content = json.loads(item.properties["_node_content"])
            if node_content["metadata"]["chunk_id"] == str(chunk_id):
                item.properties["text"] = content
                if doc_name:
                    node_content["metadata"]["document_name"] = doc_name
                if title:
                    node_content["metadata"]["title"] = title
                item.properties["_node_content"] = json.dumps(node_content)
                collection.data.update(
                    uuid=item.uuid,
                    properties=item.properties,
                    vector=vector,
                )
                break
    finally:
        client.close()


def weaviate_delete_chunk(
    document_id: uuid.UUID,
    chunk_id: uuid.UUID,
) -> None:
    """delete chunk"""
    client = weaviate.connect_to_local()
    assert client.is_ready()
    try:
        index_name = "LlamaIndex_" + str(document_id).replace("-", "_")
        collection = client.collections.get(index_name)
        for item in collection.iterator():
            node_content = json.loads(item.properties["_node_content"])
            if node_content["metadata"]["chunk_id"] == str(chunk_id):
                collection.data.delete_by_id(item.uuid)
                break
    finally:
        client.close()


def weaviate_add_chunk(
    document_id: uuid.UUID,
    chunk_id: uuid.UUID,
    content: str,
    api_key: str,
    document_name: str,
    title: Optional[str] = None,
    embedding_model: str = "text-embedding-v2",
    embedding_provider: str = "tongyi",
) -> None:
    """Add chunk to weaviate"""
    client = weaviate.connect_to_local()
    assert client.is_ready()
    try:
        vector_store = WeaviateVectorStore(
            weaviate_client=client,
            index_name="LlamaIndex_" + str(document_id).replace("-", "_"),
        )

        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
        )

        nodes = [
            TextNode(
                text=content,
                metadata={
                    "chunk_id": str(chunk_id),
                    "document_id": str(document_id),
                    "document_name": document_name,
                    "enabled": "True",
                    "title": title,
                },
            ),
        ]

        embedding_model_dict = {
            "embedding_model": embedding_model,
            "embedding_provider": embedding_provider,
        }
        embedding_model_instance = get_llama_index_embedding_model(
            api_key=api_key,
            **embedding_model_dict,
        )

        VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            embed_model=embedding_model_instance,
            store_nodes_override=True,
        )
    except Exception as e:
        raise e
    finally:
        client.close()
