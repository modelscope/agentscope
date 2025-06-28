# -*- coding: utf-8 -*-
"""Knowledge base related APIs"""
import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from app.api.deps import CurrentAccount, SessionDep, get_workspace_id
from app.exceptions.base import IncorrectParameterException
from app.schemas.common import PaginationParams
from app.schemas.file import UploadPolicy
from app.schemas.knowledge_base import (
    PageKnowledgeBaseInfo,
    KnowledgeBaseInfo,
    PageDocumentInfo,
    DocumentInfo,
    KnowledgeBaseForm,
    ProcessConfig,
    UpdateDocumentForm,
    RetrievalForm,
    ChunkStatusUpdateRequest,
    PageDocumentChunksInfo,
    DocumentChunkInfo,
    ChunkUpdateRequest,
    DocumentBatchDeleteRequest,
    KnowledgeBaseQuery,
    DocumentChunkPreviewRequest,
)
from app.schemas.response import create_response
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.retrieval_service import RetrievalService
from app.tasks.knowledge_base_task import (
    update_knowledge_base_task,
    process_document_task,
)
from app.shared import ASYNC_EXECUTOR

router = APIRouter(tags=["knowledge-bases"], prefix="")


@router.post("/knowledge-bases")
def create_knowledge_base(
    current_account: CurrentAccount,
    session: SessionDep,
    form: KnowledgeBaseForm,
) -> dict:
    """Create a new knowledge base."""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    index_config = form.index_config.model_dump()
    search_config = form.search_config.model_dump()
    process_config = form.process_config.model_dump()
    knowledge_base = knowledge_base_service.create_knowledge_base(
        account_id=current_account.account_id,
        kb_type=form.type,
        name=form.name,
        description=form.description,
        index_config=index_config,
        search_config=search_config,
        process_config=process_config,
    )
    return create_response(
        code="200",
        data=knowledge_base.id,
        message="Knowledge base created successfully",
    )


@router.get("/knowledge-bases")
def list_knowledge_bases(
    current_account: CurrentAccount,
    session: SessionDep,
    current: Optional[int] = 1,
    size: Optional[int] = 10,
    name: Optional[str] = None,
) -> dict:
    """Get the knowledge bases belong to the current user"""
    pagination = PaginationParams.from_pretrained(
        page=current,
        page_size=size,
        search=name,
    )

    knowledge_base_service = KnowledgeBaseService(session=session)
    total, knowledge_bases = knowledge_base_service.list_knowledge_bases_info(
        account_id=current_account.account_id,
        pagination=pagination,
    )

    return create_response(
        code="200",
        message="Get knowledge bases successfully",
        data=PageKnowledgeBaseInfo(
            current=current,
            size=size,
            total=total,
            records=[
                KnowledgeBaseInfo.model_validate(knowledge_base)
                for knowledge_base in knowledge_bases
            ],
        ),
    )


@router.put("/knowledge-bases/{knowledge_base_id}")
async def update_knowledge_base(
    current_account: CurrentAccount,
    knowledge_base_id: uuid.UUID,
    form: KnowledgeBaseForm,
    workspace_id: str = Depends(get_workspace_id),
) -> dict:
    """Update the knowledge base"""

    index_config = (
        form.index_config.model_dump() if form.index_config else None
    )
    search_config = (
        form.search_config.model_dump() if form.search_config else None
    )
    process_config = (
        form.process_config.model_dump() if form.process_config else None
    )

    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        ASYNC_EXECUTOR,
        update_knowledge_base_task,  # type: ignore
        current_account.account_id,
        str(knowledge_base_id),
        workspace_id,
        form.type,
        form.name,
        form.description,
        index_config,
        search_config,
        process_config,
    )

    return create_response(
        code="200",
        message="Knowledge base updated successfully",
        data=knowledge_base_id,
    )


@router.get("/knowledge-bases/{knowledge_base_id}")
def get_knowledge_base(
    current_account: CurrentAccount,
    session: SessionDep,
    knowledge_base_id: uuid.UUID,
) -> dict:
    """Get the knowledge base"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    knowledge_base = knowledge_base_service.get_knowledge_base(
        account_id=current_account.account_id,
        knowledge_base_id=knowledge_base_id,
    )
    return create_response(
        code="200",
        message="Get knowledge base info successfully",
        data={
            "kb_id": knowledge_base.id,
            "name": knowledge_base.name,
            "description": knowledge_base.description,
        },
    )


@router.get("/knowledge-bases/{knowledge_base_id}/documents")
def list_knowledge_base_documents(
    current_account: CurrentAccount,
    session: SessionDep,
    knowledge_base_id: uuid.UUID,
    current: Optional[int] = 1,
    size: Optional[int] = 10,
    name: Optional[str] = None,
) -> dict:
    """Get the knowledge base documents"""
    pagination = PaginationParams.from_pretrained(
        page=current,
        page_size=size,
        search=name,
    )
    knowledge_base_service = KnowledgeBaseService(session=session)
    (
        total,
        documents,
    ) = knowledge_base_service.list_knowledge_base_documents_info(
        account_id=current_account.account_id,
        knowledge_base_id=knowledge_base_id,
        pagination=pagination,
    )

    return create_response(
        code="200",
        message="List knowledge base documents successfully",
        data=PageDocumentInfo(
            current=current,
            size=size,
            total=total,
            records=[
                DocumentInfo.model_validate(document) for document in documents
            ],
        ),
    )


@router.delete("/knowledge-bases/{knowledge_base_id}")
def delete_knowledge_base(
    current_account: CurrentAccount,
    session: SessionDep,
    knowledge_base_id: uuid.UUID,
) -> dict:
    """Delete a specified knowledge base"""

    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    knowledge_base_service.delete_knowledge_base(
        account_id=current_account.account_id,
        knowledge_base_id=knowledge_base_id,
    )
    return create_response(
        code="200",
        message="Knowledge base deleted successfully",
        data=knowledge_base_id,
    )


@router.post("/knowledge-bases/{kb_id}/documents")
async def create_document(
    current_account: CurrentAccount,
    session: SessionDep,
    kb_id: uuid.UUID,
    files: list[UploadPolicy],
    process_config: Optional[ProcessConfig] = None,
    workspace_id: str = Depends(get_workspace_id),
) -> dict:
    """Create document in knowledge base"""

    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    if process_config is not None:
        process_config = process_config.model_dump()
    else:
        process_config = knowledge_base_service.get_process_config(
            knowledge_base_id=kb_id,
        )

    document_ids = []
    for file in files:
        document_id = knowledge_base_service.create_document_record(
            account_id=current_account.account_id,
            knowledge_base_id=kb_id,
            name=file.name,
            path=file.path,
            extension=file.extension,
            content_type=file.content_type,
            size=file.size,
            process_config=process_config,
            indexing_status="uploaded",
        )
        document_ids.append(document_id)

    loop = asyncio.get_running_loop()
    for doc_id in document_ids:
        loop.run_in_executor(
            ASYNC_EXECUTOR,
            process_document_task,  # type: ignore
            current_account.account_id,
            str(kb_id),
            [str(doc_id)],
            process_config,
            workspace_id,
        )

    return create_response(
        code="200",
        message="Document created successfully",
        data=document_ids,
    )


@router.get("/knowledge-bases/{knowledge_base_id}/documents/{document_id}")
def get_document(
    current_account: CurrentAccount,
    session: SessionDep,
    knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
) -> dict:
    """Get a document from the knowledge base"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    document = knowledge_base_service.get_document(
        account_id=current_account.account_id,
        knowledge_base_id=knowledge_base_id,
        document_id=document_id,
    )
    return create_response(
        code="200",
        message="Get document successfully",
        data={
            "doc_id": document.id,
            "kb_id": document.knowledge_base_id,
            "name": document.name,
            "path": document.path,
            "format": document.extension,
            "metadata": document.doc_metadata,
        },
    )


@router.put("/knowledge-bases/{knowledge_base_id}/documents/{document_id}")
def update_document(
    current_account: CurrentAccount,
    session: SessionDep,
    knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
    form: UpdateDocumentForm,
) -> dict:
    """Update a document"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    update_data = {
        k: v
        for k, v in form.model_dump(exclude_unset=True).items()
        if v is not None
    }

    knowledge_base_service.update_document(
        account_id=current_account.account_id,
        knowledge_base_id=knowledge_base_id,
        document_id=document_id,
        **update_data,
    )
    return create_response(
        code="200",
        message="Document updated successfully",
    )


@router.delete("/knowledge-bases/{kb_id}/documents/batch-delete")
def batch_delete_documents(
    current_account: CurrentAccount,
    session: SessionDep,
    kb_id: uuid.UUID,
    delete_request: DocumentBatchDeleteRequest,
) -> dict:
    """Batch delete documents"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    for document_id in delete_request.doc_ids:
        knowledge_base_service.delete_document(
            account_id=current_account.account_id,
            knowledge_base_id=kb_id,
            document_id=document_id,
        )
    return create_response(
        code="200",
        message="Documents deleted successfully",
        data=delete_request.doc_ids,
    )


@router.delete("/knowledge-bases/{kb_id}/documents/{doc_id}")
def delete_document(
    current_account: CurrentAccount,
    session: SessionDep,
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
) -> dict:
    """Delete a specific document"""

    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    knowledge_base_service.delete_document(
        account_id=current_account.account_id,
        knowledge_base_id=kb_id,
        document_id=doc_id,
    )
    return create_response(
        code="200",
        message="Document deleted successfully",
    )


@router.post("/knowledge-bases/retrieve")
def retrieve(
    current_account: CurrentAccount,
    session: SessionDep,
    retrieval_form: RetrievalForm,
) -> dict:
    """Retrieve a query from the knowledge base"""
    retrieval_service = RetrievalService(
        session=session,
    )
    retrieval_result = retrieval_service.retrieve(
        account_id=current_account.account_id,
        query=retrieval_form.query,
        knowledge_base_ids=retrieval_form.search_options.kb_ids,
        score_threshold=retrieval_form.search_options.similarity_threshold,
        top_k=retrieval_form.search_options.top_k,
    )
    return create_response(
        code="200",
        message="Query processed and results retrieved successfully.",
        data=[
            {
                "doc_id": result.metadata.get("document_id"),
                "doc_name": result.metadata.get("document_name"),
                "title": None,
                "text": result.text,
                "score": result.score,
                "page_number": None,
                "chunk_id": result.metadata.get("chunk_id"),
                "node_id": result.id_,
            }
            for result in retrieval_result
        ],
    )


@router.post("/knowledge-bases/query-by-codes")
def query_knowledge_bases_by_codes(
    current_account: CurrentAccount,
    session: SessionDep,
    query: KnowledgeBaseQuery,
) -> dict:
    """get knowledge list by codes"""
    # validate the query
    if not query.kb_ids:
        raise IncorrectParameterException(
            extra_info="Missing parameters: query or kb_ids",
        )

    # get knowledge_bases from retrieval service
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    knowledge_bases = knowledge_base_service.list_knowledge_bases_by_ids(
        account_id=current_account.account_id,
        knowledge_base_ids=query.kb_ids,
    )

    # build the return object
    return create_response(
        code="200",
        message="Success",
        data=knowledge_bases,
    )


@router.put(
    "/knowledge-bases/{knowledge_base_id}/documents/{"
    "document_id}/update-status",
)
def set_document_status(
    current_account: CurrentAccount,
    session: SessionDep,
    knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
    enabled: bool,
) -> dict:
    """Enable or disable a document from the knowledge base"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    knowledge_base_service.set_document_status(
        account_id=current_account.account_id,
        knowledge_base_id=knowledge_base_id,
        document_id=document_id,
        enabled=enabled,
    )
    return create_response(
        code="200",
        message="Document status set successfully",
        data=document_id,
    )


@router.get("/documents/{doc_id}/chunks")
def list_document_chunks(
    current_account: CurrentAccount,
    session: SessionDep,
    # knowledge_base_id: uuid.UUID,
    doc_id: uuid.UUID,
    current: int,
    size: int,
    search: Optional[str] = None,
) -> dict:
    """Get the chunks of a document"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    pagination = PaginationParams(
        current=current,
        size=size,
        search=search,
    )
    total, chunks = knowledge_base_service.list_document_chunks_info(
        account_id=current_account.account_id,
        # knowledge_base_id=knowledge_base_id,
        document_id=doc_id,
        pagination=pagination,
    )

    return create_response(
        code="200",
        message="Chunks listed successfully",
        data=PageDocumentChunksInfo(
            current=current,
            size=size,
            total=total,
            records=[
                DocumentChunkInfo.model_validate(chunk) for chunk in chunks
            ],
        ),
    )


@router.put("/documents/{document_id}/chunks/update-status")
def set_chunk_status(
    current_account: CurrentAccount,
    session: SessionDep,
    # knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
    # chunk_ids: list[uuid.UUID],
    # enabled: bool,
    request_data: ChunkStatusUpdateRequest,
) -> dict:
    """Enable or disable a chunk from the knowledge base"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    for chunk_id in request_data.chunk_ids:
        knowledge_base_service.set_chunk_status(
            account_id=current_account.account_id,
            # knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            chunk_id=chunk_id,
            enabled=request_data.enabled,
        )
    return create_response(
        code="200",
        message="chunk status set successfully",
        data=request_data.chunk_ids,
    )


@router.put("/documents/{document_id}/chunks/{chunk_id}")
def update_chunk(
    current_account: CurrentAccount,
    session: SessionDep,
    # knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
    chunk_id: uuid.UUID,
    chunk_update_request: ChunkUpdateRequest,
    workspace_id: str = Depends(get_workspace_id),
) -> dict:
    """Edit a chunk from the knowledge base"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    knowledge_base_service.update_chunk(
        account_id=current_account.account_id,
        # knowledge_base_id=knowledge_base_id,
        document_id=document_id,
        chunk_id=chunk_id,
        workspace_id=workspace_id,
        content=chunk_update_request.text,
        doc_name=chunk_update_request.doc_name,
        title=chunk_update_request.title,
    )
    return create_response(
        code="200",
        message="Chunk content updated successfully",
        data=chunk_id,
    )


@router.put(
    "/knowledge-bases/{knowledge_base_id}/documents/{document_id}/re-index",
)
async def document_indexing(
    current_account: CurrentAccount,
    session: SessionDep,
    knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
    process_config: dict,
    workspace_id: str = Depends(get_workspace_id),
) -> dict:
    """Re-index a document"""

    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        ASYNC_EXECUTOR,
        process_document_task,
        current_account.account_id,
        str(knowledge_base_id),
        [str(document_id)],
        process_config["process_config"],
        workspace_id,
    )

    return create_response(
        code="200",
        message="Document re-index successfully",
        data=document_id,
    )


@router.delete("/documents/{document_id}/chunks/{chunk_id}")
def delete_chunk(
    current_account: CurrentAccount,
    session: SessionDep,
    # knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
    chunk_id: uuid.UUID,
) -> dict:
    """Delete a chunk from the knowledge base"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    knowledge_base_service.delete_chunk(
        account_id=current_account.account_id,
        # knowledge_base_id=knowledge_base_id,
        document_id=document_id,
        chunk_id=chunk_id,
    )
    return create_response(
        code="200",
        message="Chunk deleted successfully",
        data=chunk_id,
    )


@router.delete("/documents/{document_id}/chunks/batch-delete")
def batch_delete_chunks(
    current_account: CurrentAccount,
    session: SessionDep,
    # knowledge_base_id: uuid.UUID,
    document_id: uuid.UUID,
    chunk_ids: list[uuid.UUID],
) -> dict:
    """Delete multiple chunks from the knowledge base"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    for chunk_id in chunk_ids:
        knowledge_base_service.delete_chunk(
            account_id=current_account.account_id,
            # knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            chunk_id=chunk_id,
        )
    return create_response(
        code="200",
        message="Chunks deleted successfully",
        data=chunk_ids,
    )


@router.post("/documents/{doc_id}/chunks/preview")
def get_document_chunks_preview(
    current_account: CurrentAccount,
    session: SessionDep,
    doc_id: uuid.UUID,
    preview_request: DocumentChunkPreviewRequest,
) -> dict:
    """Get the preview of the chunks of a document"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    # process_config = process_config.model_dump()
    chunk_records = knowledge_base_service.get_document_chunks_preview(
        account_id=current_account.account_id,
        document_id=doc_id,
        process_config=preview_request.process_config,
    )
    return create_response(
        code="200",
        message="Document chunks previewed successfully",
        data=chunk_records,
    )


@router.post("/documents/{document_id}/chunks")
def add_chunk(
    current_account: CurrentAccount,
    session: SessionDep,
    document_id: uuid.UUID,
    text: str,
    workspace_id: str = Depends(get_workspace_id),
) -> dict:
    """Add chunks to a document"""
    knowledge_base_service = KnowledgeBaseService(
        session=session,
    )
    chunk_id = knowledge_base_service.add_chunk(
        account_id=current_account.account_id,
        document_id=document_id,
        content=text,
        workspace_id=workspace_id,
    )

    return create_response(
        code="200",
        message="Chunk added successfully",
        data=chunk_id,
    )
