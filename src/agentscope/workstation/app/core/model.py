# -*- coding: utf-8 -*-
"""Model related utils"""
from typing import Union

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank


def get_llama_index_embedding_model(
    embedding_model: str,
    embedding_provider: str,
    api_key: str,
) -> Union[OpenAIEmbedding, DashScopeEmbedding]:
    """Get llama index embedding model"""
    if embedding_provider == "openai":
        return OpenAIEmbedding(model=embedding_model, api_key=api_key)
    elif embedding_provider == "Tongyi":
        if embedding_model == "text-embedding-v3":
            return DashScopeEmbedding(
                model_name=embedding_model,
                embed_batch_size=10,
                api_key=api_key,
            )
        return DashScopeEmbedding(model_name=embedding_model, api_key=api_key)
    raise ValueError(
        f"Unsupported embedding model provider: {embedding_provider}",
    )


def get_llama_index_rerank_model(
    rerank_model: str,
    rerank_model_provider: str,
    api_key: str,
) -> Union[DashScopeRerank]:
    """Get llama index rerank model"""
    if rerank_model_provider == "dashscope":
        return DashScopeRerank(model=rerank_model, api_key=api_key)
    else:
        raise ValueError(
            f"Unsupported rerank model provider: {rerank_model_provider}",
        )
