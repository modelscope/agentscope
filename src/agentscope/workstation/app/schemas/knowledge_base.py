# -*- coding: utf-8 -*-
"""Knowledge base schemas"""
import uuid
from typing import Optional, List

from sqlmodel import SQLModel, Field

from app.models.knowledge_base import KnowledgeBaseTypeEnum
from pydantic import BaseModel


class KnowledgeBaseQuery(BaseModel):
    kb_ids: List[uuid.UUID]


class KnowledgeBaseInfo(SQLModel):
    """Knowledge base info"""

    kb_id: uuid.UUID
    name: str
    description: str
    total_docs: int


class PageKnowledgeBaseInfo(SQLModel):
    """Page knowledge base info"""

    current: int
    size: int
    total: int
    records: List[KnowledgeBaseInfo]


class DocumentInfo(SQLModel):
    """Document info"""

    id: uuid.UUID
    type: str
    name: str
    description: str
    path: str
    index_status: str
    size: int
    enabled: bool
    gmt_create: str
    gmt_modified: str
    creator: str
    doc_id: uuid.UUID
    kb_id: uuid.UUID
    format: str
    # modifier: str


class PageDocumentInfo(SQLModel):
    """Page document info"""

    current: int
    size: int
    total: int
    records: List[DocumentInfo]


class ProcessConfig(SQLModel):
    """knowledge base precess config"""

    chunk_type: str = Field(default="basic")
    delimiter: str = Field(default="\n\n")
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=100)
    regex: Optional[str] = Field(default=None)


class SearchConfig(SQLModel):
    """knowledge base search config"""

    top_k: int = Field(default=20)
    similarity_threshold: float = Field(default=0.5)
    search_type: str = Field(default="hybrid")
    hybrid_weight: float = Field(default=0.7)
    enable_rerank: bool = Field(default=True)
    rerank_provider: str = Field(default="dashscope")
    rerank_model: str = Field(default="gte-rerank")


class IndexConfig(SQLModel):
    """knowledge base index config"""

    embedding_model: str = Field(default="text-embedding-v2")
    embedding_provider: str = Field(default="dashscope")


class KnowledgeBaseForm(SQLModel):
    """The form used to create knowledge base"""

    type: KnowledgeBaseTypeEnum = Field(
        default=KnowledgeBaseTypeEnum.UNSTRUCTURED,
    )
    name: str
    description: str
    process_config: Optional[ProcessConfig] = Field(default=None)
    index_config: Optional[IndexConfig]
    search_config: Optional[SearchConfig]


class UpdateDocumentForm(SQLModel):
    """The form used to update document"""

    name: Optional[str]
    description: Optional[str]


class DocumentChunkInfo(SQLModel):
    """Document chunk"""

    chunk_id: Optional[uuid.UUID] = None
    doc_id: uuid.UUID
    doc_name: str
    title: Optional[str] = None
    text: str
    page_number: Optional[int] = None
    enabled: bool = Field(default=True)


class PageDocumentChunksInfo(SQLModel):
    """Page knowledge base info"""

    current: int
    size: int
    total: int
    records: List[DocumentChunkInfo]


class FileSearchOptions(SQLModel):
    """The file search options model used to retrieve"""

    kb_ids: list[uuid.UUID]
    enable_search: bool = Field(default=True)
    top_k: Optional[int] = None
    similarity_threshold: float = Field(default=0.2)


class RetrievalForm(SQLModel):
    """The form used to retrieve"""

    query: str
    search_options: FileSearchOptions


class ChunkStatusUpdateRequest(SQLModel):
    chunk_ids: list[uuid.UUID]
    enabled: bool


class ChunkUpdateRequest(SQLModel):
    """The response used to update chunk"""

    text: str
    doc_name: Optional[str] = None
    title: Optional[str] = None


class DocumentBatchDeleteRequest(SQLModel):
    """The request used to delete document"""

    doc_ids: list[uuid.UUID]
    kb_id: uuid.UUID


class DocumentChunkPreviewRequest(SQLModel):
    """The request used to get document chunk preview"""

    kb_id: uuid.UUID
    process_config: dict
