# -*- coding: utf-8 -*-
"""The knowledge base related services"""
import uuid
from typing import List, Optional, Union

from loguru import logger
from sqlmodel import Session

from app.core.model import get_llama_index_embedding_model
from app.dao.knowledge_base_dao import KnowledgeBaseDao
from app.exceptions.service import (
    KnowledgeBaseAccessDeniedException,
    KnowledgeBaseNotFoundException,
    DocumentNotFoundException,
)
from app.models.knowledge_base import (
    KnowledgeBase,
    Document,
    KnowledgeBasePermission,
    Chunk,
)
from app.models.provider import ProviderBase

from app.schemas.common import PaginationParams
from app.schemas.knowledge_base import KnowledgeBaseInfo
from app.utils.text_splitter import (
    preprocess_chunks_and_child_chunks,
    text_split,
    preprocess_chunk_parameter,
)
from app.utils.weaviate_utils import (
    process_weaviate_indexing,
    weaviate_delete_index,
    weaviate_set_chunk_status,
    weaviate_update_chunk,
    weaviate_delete_chunk,
    weaviate_add_chunk,
)
from app.services.base_service import BaseService
from app.services.chunk_service import ChunkService
from app.services.provider_service import ProviderService
from app.services.document_service import DocumentService
from app.services.knowledge_base_permission_service import (
    KnowledgeBasePermissionService,
)
from app.utils.extractor import extract_content
from app.utils.crypto import decrypt_with_rsa

import json


class KnowledgeBaseService(BaseService[KnowledgeBaseDao]):
    """Service layer for knowledge base."""

    _dao_cls = KnowledgeBaseDao

    def __init__(
        self,
        session: Session,
        user_id: uuid.UUID = None,  # pylint: disable=unused-argument
    ) -> None:
        super().__init__(session=session)
        self.document_service = DocumentService(
            session=session,
        )
        self.chunk_service = ChunkService(
            session=session,
        )
        self.knowledge_base_permission_service = (
            KnowledgeBasePermissionService(session=session)
        )
        self.provider_service = ProviderService(session)

    def check_permission(
        self,
        knowledge_base_id: Union[uuid.UUID, List[uuid.UUID]],
        account_id: Optional[str] = None,
    ) -> None:
        """Check if the user has permission to access the knowledge base"""
        logger.info(
            f"Check permission with knowledge_base_id : "
            f"{knowledge_base_id}, account_id: {account_id}",
        )
        return
        # TODO: Add detailed permission checking
        # if not self.dao.check_permission(
        #     account_id=account_id,
        #     knowledge_base_id=knowledge_base_id,
        # ):
        #     raise KnowledgeBaseAccessDeniedException()

    def check_knowledge_base_exist(
        self,
        knowledge_base_id: uuid.UUID,
        account_id: Optional[str] = None,
    ) -> KnowledgeBase:
        """Check if the knowledge base exists"""
        knowledge_base = self.dao.get_knowledge_base(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        if knowledge_base is None:
            raise KnowledgeBaseNotFoundException(
                f"Knowledge base not found with id: {knowledge_base_id}",
            )
        return knowledge_base

    def check_document_exist(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Document:
        """Check if the document exists"""
        document = self.dao.get_document(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )
        if document is None:
            raise DocumentNotFoundException(
                f"Document not found with id: {document_id}",
            )
        return document

    def create_knowledge_base(
        self,
        account_id: str,
        kb_type: str,
        name: str,
        description: str,
        index_config: dict,
        search_config: dict,
        process_config: dict,
    ) -> KnowledgeBase:
        """Create a new knowledge base."""

        knowledge_base = KnowledgeBase(
            creator_id=account_id,
            type=kb_type,
            name=name,
            description=description,
            index_config=index_config,
            search_config=search_config,
            process_config=process_config,
            updater_id=account_id,
        )

        knowledge_base = self.dao.create(knowledge_base)

        knowledge_base_permission = KnowledgeBasePermission(
            knowledge_base_id=knowledge_base.id,
            account_id=account_id,
            has_permission=True,
            team_id=account_id,
        )
        self.knowledge_base_permission_service.create(
            knowledge_base_permission,
        )

        return knowledge_base

    def list_knowledge_bases_by_ids(
        self,
        account_id: str,
        knowledge_base_ids: List[uuid.UUID],
    ) -> List[KnowledgeBaseInfo]:
        """List the knowledge bases by ids"""
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_ids,
        )

        knowledge_bases = self.dao.list_knowledge_base_ids(
            account_id=account_id,
            knowledge_base_ids=knowledge_base_ids,
        )
        if knowledge_bases is None:
            raise KnowledgeBaseNotFoundException(
                f"Knowledge base not found with id: {knowledge_base_ids}",
            )
        return knowledge_bases

    def list_knowledge_bases_info(
        self,
        account_id: str,
        pagination: PaginationParams,
    ) -> tuple[int, list[KnowledgeBaseInfo]]:
        """List the knowledge bases for a user"""
        total = self.count_by_field("creator_id", account_id)
        knowledge_bases = self.paginate(
            filters={"creator_id": account_id},
            pagination=pagination,
        )

        return total, knowledge_bases

    def get_knowledge_base(
        self,
        knowledge_base_id: uuid.UUID,
        account_id: Optional[str] = None,
    ) -> KnowledgeBase:
        """Get the knowledge base detail"""
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        knowledge_base = self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        return knowledge_base

    def update_knowledge_base(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        workspace_id: str,
        kb_type: str,
        name: str,
        description: str,
        index_config: Optional[dict] = None,
        search_config: Optional[dict] = None,
        process_config: Optional[dict] = None,
    ) -> KnowledgeBase:
        """Update the knowledge base"""
        knowledge_base = self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        old_process_config = knowledge_base.process_config
        old_index_config = knowledge_base.index_config

        updated_knowledge_base = self.dao.update_knowledge_base(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            type=kb_type,
            name=name,
            description=description,
            index_config=index_config,
            search_config=search_config,
            process_config=process_config,
        )

        if (process_config and old_process_config != process_config) or (
            index_config and old_index_config != index_config
        ):
            documents = knowledge_base.documents
            if documents:
                document_ids = [doc.id for doc in documents]
                self.dao.update_documents_indexing_status(
                    knowledge_base_id=updated_knowledge_base.id,
                    document_ids=document_ids,
                    new_status="uploaded",
                )
                for document in documents:
                    self.document_indexing(
                        account_id=account_id,
                        knowledge_base_id=updated_knowledge_base.id,
                        workspace_id=workspace_id,
                        document_id=document.id,
                        process_config=document.process_config,
                    )

        return updated_knowledge_base

    def list_knowledge_base_documents_info(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        pagination: PaginationParams,
    ) -> tuple[int, list[Document]]:
        """Get the knowledge bases for a user"""
        self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        total = self.document_service.count_by_field(
            "knowledge_base_id",
            knowledge_base_id,
        )
        documents = self.document_service.paginate(
            filters={"knowledge_base_id": knowledge_base_id},
            pagination=pagination,
        )
        return total, documents

    def delete_knowledge_base(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
    ) -> None:
        """Delete a specified knowledge base"""
        self.check_knowledge_base_exist(
            knowledge_base_id=knowledge_base_id,
            account_id=account_id,
        )

        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        documents = self.document_service.get_all_by_field(
            "knowledge_base_id",
            knowledge_base_id,
        )
        document_ids = [document.id for document in documents]

        weaviate_delete_index(document_ids)

        for document_id in document_ids:
            chunks = self.chunk_service.get_all_by_field(
                "document_id",
                document_id,
            )
            for chunk_id in [chunk.id for chunk in chunks]:
                self.chunk_service.delete(chunk_id)
            self.document_service.delete(document_id)

        knowledge_base_permissions = (
            self.knowledge_base_permission_service.get_all_by_field(
                "knowledge_base_id",
                knowledge_base_id,
            )
        )

        for knowledge_base_permission in knowledge_base_permissions:
            self.knowledge_base_permission_service.delete(
                knowledge_base_permission.id,
            )

        self.delete(knowledge_base_id)

    def create_document_record(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        name: str,
        path: str,
        extension: str,
        content_type: str,
        size: int,
        process_config: Optional[dict] = None,
        indexing_status: str = "uploaded",
        tabs: Optional[list[str]] = None,
    ) -> uuid.UUID:
        """create document record"""
        self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        if not process_config:
            process_config = self.get(
                knowledge_base_id,
            ).process_config

        return self.dao.create_document_record(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            name=name,
            path=path,
            extension=extension,
            content_type=content_type,
            size=size,
            process_config=process_config,
            indexing_status=indexing_status,
            tabs=tabs,
        )

    def update_document_content(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        content: str,
    ) -> None:
        """update document content"""
        self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        self.dao.update_document_content(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            content=content,
        )

    def update_document_indexing_status(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        indexing_status: str,
    ) -> None:
        """update document indexing status"""
        self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        self.dao.update_document_indexing_status(
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            indexing_status=indexing_status,
        )

    def get_document(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Optional[Document]:
        """Get a document from the knowledge base"""
        self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        self.check_document_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        return self.document_service.get(document_id)

    def update_document(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        **update_data: dict,
    ) -> None:
        """Update a specific document"""
        self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        self.check_document_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )
        self.document_service.update(
            id=document_id,
            obj_in=update_data,
        )

    def delete_document(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> None:
        """Delete a specific document"""
        self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        document = self.check_document_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )

        chunks = self.chunk_service.get_all_by_field(
            "document_id",
            document_id,
        )
        for chunk_id in [chunk.id for chunk in chunks]:
            self.chunk_service.delete(chunk_id)
        self.document_service.delete(document_id)

        weaviate_delete_index(document.id)

    def document_indexing(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        workspace_id: str,
        process_config: dict,
    ) -> None:
        """Indexing a document"""
        self.update_document_indexing_status(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            indexing_status="processing",
        )
        knowledge_base = self.check_knowledge_base_exist(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        (
            chunk_type,
            chunk_parameter,
            preprocessing_rules,
        ) = preprocess_chunk_parameter(
            chunk_type=process_config.get("chunk_type", "length"),
            delimiter=process_config.get("delimiter"),
            chunk_size=process_config.get("chunk_size"),
            chunk_overlap=process_config.get("chunk_overlap"),
        )

        document = self.get_document(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )

        self.dao.set_document_process_config(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            process_config=process_config,
        )

        self.dao.clear_document_chunks(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )

        document_content = extract_content(document.path, document.extension)

        chunks, child_chunks, keywords_list = text_split(
            document_content,
            chunk_type,
            chunk_parameter,
        )

        chunks, child_chunks = preprocess_chunks_and_child_chunks(
            chunks,
            child_chunks,
            preprocessing_rules,
        )
        chunk_ids = []
        child_chunk_ids = []

        for chunk_idx, chunk_content in enumerate(chunks):
            if keywords_list:
                keywords = keywords_list[chunk_idx]
            else:
                keywords = []
            chunk_id = self.dao.create_chunk(
                account_id=account_id,
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
                document_name=document.name,
                content=chunk_content,
                word_count=len(chunk_content.strip()),
                position=chunk_idx,
                keywords=keywords,
            )
            chunk_ids.append(chunk_id)
            if child_chunks:
                cc_ids = []
                for child_chunk_idx, child_chunk_content in enumerate(
                    child_chunks[chunk_idx],
                ):
                    chunk_id = self.dao.create_child_chunk(
                        account_id=account_id,
                        knowledge_base_id=knowledge_base_id,
                        document_id=document_id,
                        chunk_id=chunk_id,
                        content=child_chunk_content,
                        word_count=len(child_chunk_content.strip()),
                        position=child_chunk_idx,
                    )
                    cc_ids.append(chunk_id)
                child_chunk_ids.append(cc_ids)

        self.dao.update_before_document_indexing(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )

        provider_info: ProviderBase = self.provider_service.get_provider(
            provider=knowledge_base.index_config["embedding_provider"],
            workspace_id=workspace_id,
        )
        assert (
            provider_info.credential is not None
        ), "Provider credential cannot be None"

        model_credential = json.loads(provider_info.credential)
        api_key = decrypt_with_rsa(model_credential["api_key"])

        process_weaviate_indexing(
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            document_name=document.name,
            chunk_type=chunk_type,
            chunk_ids=chunk_ids,
            chunks=chunks,
            child_chunk_ids=child_chunk_ids,
            child_chunks=child_chunks,
            embedding_model=knowledge_base.index_config["embedding_model"],
            embedding_provider=knowledge_base.index_config[
                "embedding_provider"
            ],
            api_key=api_key,
        )

        self.update_document_indexing_status(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            indexing_status="processed",
        )

    def set_document_status(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        enabled: bool,
    ) -> None:
        """Disable a specific document"""
        self.dao.set_document_status(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            enabled=enabled,
        )

    def set_chunk_status(
        self,
        account_id: str,
        # knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        chunk_id: uuid.UUID,
        enabled: bool,
    ) -> None:
        """Disable a specific chunk"""
        document = self.document_service.get(document_id)
        knowledge_base_id = document.knowledge_base_id
        self.dao.set_chunk_status(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            chunk_id=chunk_id,
            enabled=enabled,
        )

        weaviate_set_chunk_status(document_id, chunk_id, enabled)

    def update_chunk(
        self,
        account_id: str,
        # knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        chunk_id: uuid.UUID,
        workspace_id: str,
        content: str,
        doc_name: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        """Update chunk content"""

        document = self.document_service.get(document_id)
        knowledge_base_id = document.knowledge_base_id
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        self.dao.update_chunk(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            chunk_id=chunk_id,
            content=content,
            doc_name=doc_name,
            title=title,
        )

        embedding_model_dict = self.dao.get_embedding_model_dict(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )

        provider_info: ProviderBase = self.provider_service.get_provider(
            provider=embedding_model_dict["embedding_provider"],
            workspace_id=workspace_id,
        )
        assert (
            provider_info.credential is not None
        ), "Provider credential cannot be None"
        model_credential = json.loads(provider_info.credential)
        api_key = decrypt_with_rsa(model_credential["api_key"])
        embedding_model_instance = get_llama_index_embedding_model(
            api_key=api_key,
            **embedding_model_dict,
        )

        vector = embedding_model_instance.get_text_embedding(content)

        weaviate_update_chunk(
            document_id,
            chunk_id,
            content,
            vector,
            doc_name,
            title,
        )

    def delete_chunk(
        self,
        account_id: str,
        # knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        chunk_id: uuid.UUID,
    ) -> None:
        """Delete a chunk"""
        document = self.document_service.get(document_id)
        knowledge_base_id = document.knowledge_base_id
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        self.chunk_service.delete(chunk_id)

        weaviate_delete_chunk(
            document_id,
            chunk_id,
        )

    def get_document_chunks_preview(
        self,
        account_id: str,  # pylint: disable=unused-argument
        document_id: uuid.UUID,
        process_config: dict,
    ) -> list:
        """get document chunks preview"""
        (
            chunk_type,
            chunk_parameter,
            preprocessing_rules,
        ) = preprocess_chunk_parameter(
            chunk_type=process_config.get("chunk_type", "length"),
            delimiter=process_config.get("delimiter"),
            chunk_size=process_config.get("chunk_size"),
            chunk_overlap=process_config.get("chunk_overlap"),
        )

        document = self.document_service.get(document_id)

        document_content = extract_content(document.path, document.extension)

        chunks, child_chunks, _ = text_split(
            document_content,
            chunk_type,
            chunk_parameter,
        )

        chunks, child_chunks = preprocess_chunks_and_child_chunks(
            chunks,
            child_chunks,
            preprocessing_rules,
        )

        return [
            {
                "title": None,
                "text": chunk,
                "doc_id": document_id,
                "doc_name": document.name,
                "page_number": None,
                "chunk_id": uuid.uuid4(),
                "enabled": True,
            }
            for chunk in chunks
        ]

    def list_document_chunks_info(
        self,
        account_id: str,
        document_id: uuid.UUID,
        pagination: PaginationParams,
    ) -> tuple[int, list[Chunk]]:
        """list document chunks"""
        document = self.document_service.get(document_id)
        knowledge_base_id = document.knowledge_base_id
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        total = self.chunk_service.count_by_field(
            "document_id",
            document_id,
        )
        chunks = self.chunk_service.paginate(
            filters={"document_id": document_id},
            pagination=pagination,
        )
        return total, chunks

    def add_chunk(
        self,
        account_id: str,
        document_id: uuid.UUID,
        workspace_id: str,
        content: str,
    ) -> uuid.UUID:
        """add chunk"""
        document = self.document_service.get(document_id)
        knowledge_base_id = document.knowledge_base_id
        self.check_permission(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        chunk = self.chunk_service.create(
            {
                "document_id": document_id,
                "document_name": document.name,
                "content": content,
                "creator_id": account_id,
                "knowledge_base_id": knowledge_base_id,
                "document": document,
                "word_count": len(content.strip()),
            },
        )
        document.chunks.append(chunk)

        embedding_model_dict = self.dao.get_embedding_model_dict(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
        )
        provider_info: ProviderBase = self.provider_service.get_provider(
            provider=embedding_model_dict["embedding_provider"],
            workspace_id=workspace_id,
        )
        assert (
            provider_info.credential is not None
        ), "Provider credential cannot be None"
        model_credential = json.loads(provider_info.credential)
        api_key = decrypt_with_rsa(model_credential["api_key"])

        weaviate_add_chunk(
            document_id=document_id,
            chunk_id=chunk.id,
            content=content,
            api_key=api_key,
            document_name=document.name,
            title=chunk.title,
            embedding_model=embedding_model_dict["embedding_model"],
            embedding_provider=embedding_model_dict["embedding_provider"],
        )

        return chunk.id

    def get_process_config(
        self,
        knowledge_base_id: uuid.UUID,
    ) -> dict:
        """get process config"""
        process_config = self.get(knowledge_base_id).process_config
        return process_config
