# -*- coding: utf-8 -*-
"""The data access object layer for knowledge base."""
# pylint: disable=too-many-public-methods
import datetime
import uuid
from typing import Literal, Optional, List, Union, Any

from sqlmodel import select, delete, update
from app.dao.base_dao import BaseDAO


from app.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBasePermission,
    Document,
    Chunk,
    ChildChunk,
)


class KnowledgeBaseDao(BaseDAO[KnowledgeBase]):
    """Data access object layer for knowledge base."""

    _model_class = KnowledgeBase

    def _create_permission_record(
        self,
        knowledge_base_id: uuid.UUID,
        creator_id: uuid.UUID,
    ) -> None:
        """Create a permission record for the knowledge base."""
        permission = KnowledgeBasePermission(
            knowledge_base_id=knowledge_base_id,
            account_id=creator_id,
            has_permission=True,
            team_id=creator_id,
        )
        self.session.add(permission)
        self.session.commit()

    def check_permission(
        self,
        knowledge_base_id: Union[uuid.UUID, List[uuid.UUID]],
        account_id: Optional[str] = None,
    ) -> bool:
        """
        Check if the user has permission to access the given knowledge base.
        """
        if not account_id:
            return True
        if not isinstance(knowledge_base_id, list):
            knowledge_base_id = [knowledge_base_id]
        query = select(KnowledgeBasePermission).where(
            KnowledgeBasePermission.knowledge_base_id.in_(
                knowledge_base_id,
            ),
            KnowledgeBasePermission.account_id == account_id,
            KnowledgeBasePermission.has_permission,
        )
        permissions = self.session.exec(query).all()
        return len(permissions) == len(knowledge_base_id)

    def list_knowledge_base_ids(
        self,
        account_id: str,
        knowledge_base_ids: List[uuid.UUID],
    ) -> List[KnowledgeBase]:
        """Get knowledge base"""
        query = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.id.in_(knowledge_base_ids),
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == KnowledgeBase.id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        knowledge_bases = self.session.exec(query).all()

        return knowledge_bases

    def get_knowledge_base(
        self,
        knowledge_base_id: uuid.UUID,
        account_id: Optional[str] = None,
    ) -> KnowledgeBase:
        """Get knowledge base"""
        if account_id is None:
            query = select(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_base_id,
            )
        else:
            query = (
                select(KnowledgeBase)
                .where(
                    KnowledgeBase.id == knowledge_base_id,
                )
                .join(
                    KnowledgeBasePermission,
                    KnowledgeBasePermission.knowledge_base_id
                    == knowledge_base_id,
                )
                .where(
                    KnowledgeBasePermission.account_id == account_id,
                    KnowledgeBasePermission.has_permission,
                )
            )
        knowledge_base = self.session.exec(query).first()

        return knowledge_base

    def update_documents_indexing_status(
        self,
        knowledge_base_id: uuid.UUID,
        document_ids: list[uuid.UUID],
        new_status: str,
    ) -> None:
        """Update indexing status for a list of documents"""
        stmt = (
            update(Document)
            .where(
                Document.id.in_(document_ids),
                Document.knowledge_base_id == knowledge_base_id,
            )
            .values(indexing_status=new_status)
        )
        self.session.execute(stmt)
        self.session.commit()

    def update_knowledge_base(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        **kwargs: Any,
    ) -> KnowledgeBase:
        """Update the knowledge base"""
        query = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.id == knowledge_base_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        knowledge_base = self.session.exec(query).first()
        updated = False
        for key, value in kwargs.items():
            if (
                value is not None
                and hasattr(knowledge_base, key)
                and value != getattr(knowledge_base, key)
            ):
                setattr(knowledge_base, key, value)
                updated = True

        if updated:
            knowledge_base.updater_id = account_id
            knowledge_base.gmt_modified = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S",
            )
        self.session.commit()
        return knowledge_base

    def update_document_indexing_status(
        self,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        indexing_status: str,
    ) -> None:
        """Update document indexing status"""
        query = (
            update(Document)
            .where(
                Document.id == document_id,
                Document.knowledge_base_id == knowledge_base_id,
            )
            .values(indexing_status=indexing_status)
        )
        self.session.execute(query)
        self.session.commit()

    def delete_knowledge_base(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
    ) -> None:
        """Delete a specified knowledge base"""
        subquery = (
            select(KnowledgeBase.id)
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
                KnowledgeBase.id == knowledge_base_id,
            )
            .scalar_subquery()
        )
        query = delete(KnowledgeBase).where(KnowledgeBase.id.in_(subquery))
        self.session.execute(query)
        self.session.execute(
            delete(ChildChunk).where(
                ChildChunk.knowledge_base_id == knowledge_base_id,
            ),
        )
        self.session.execute(
            delete(Chunk).where(
                Chunk.knowledge_base_id == knowledge_base_id,
            ),
        )
        self.session.execute(
            delete(Document).where(
                Document.knowledge_base_id == knowledge_base_id,
            ),
        )

        self.session.commit()

    def delete_knowledge_base_permission(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
    ) -> None:
        """Delete the record in KnowledgeBasePermission"""
        query = delete(KnowledgeBasePermission).where(
            KnowledgeBasePermission.account_id == account_id,
            KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
        )
        self.session.execute(query)
        self.session.commit()

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
        """Create a new document record in the specified knowledge base"""
        # Check if the knowledge base exists and the user has permission to
        # access it
        knowledge_base = self.session.exec(
            select(KnowledgeBase)
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            ),
        ).first()

        existing_document = next(
            (doc for doc in knowledge_base.documents if doc.name == name),
            None,
        )
        if existing_document:
            # Update the existing document
            existing_document.path = path
            existing_document.extension = extension
            existing_document.content_type = content_type
            existing_document.size = size
            existing_document.process_config = process_config
            existing_document.updater_id = account_id
            existing_document.indexing_status = indexing_status
            existing_document.tabs = tabs
            existing_document.gmt_modified = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S",
            )
        else:
            # Create a new document
            existing_document = Document(
                knowledge_base_id=knowledge_base_id,
                name=name,
                path=path,
                extension=extension,
                content_type=content_type,
                size=size,
                process_config=process_config,
                creator_id=account_id,
                gmt_create=datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S",
                ),
                tabs=tabs,
                indexing_status=indexing_status,
            )
            # Add the new document to the session
            knowledge_base.documents.append(existing_document)

        # Commit changes to the session
        try:
            # 在commit前确认ID已存在
            print(
                f"Debug - Before commit - Document ID: {existing_document.id}",
            )
            self.session.add(existing_document)
            self.session.commit()

            # 在commit后保存ID (commit可能会刷新对象)
            document_id = existing_document.id
            print(f"Debug - After commit - Document ID: {document_id}")

            # 直接返回UUID对象而不是调用.id
            return document_id
        except Exception as e:
            import traceback

            print(f"Commit error: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            self.session.rollback()
            raise

        # return existing_document.id

    def update_before_document_indexing(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> None:
        """Clean up before document indexing"""
        query = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.knowledge_base_id == knowledge_base_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        if document:
            # Update the existing document
            document.updater_id = account_id
            document.gmt_modified = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S",
            )
        self.session.commit()

    def clear_document_chunks(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        position: int = None,
    ) -> None:
        """Clear chunk corresponding to the document"""
        query = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.knowledge_base_id == knowledge_base_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        if document:
            if position is not None:
                # If chunk_idx is provided, filter to find the specific
                # chunk
                chunk = next(
                    (
                        seg
                        for seg in document.chunks
                        if seg.position == position
                    ),
                    None,
                )
                if chunk:
                    self.clear_chunk_child_chunks(
                        account_id,
                        knowledge_base_id,
                        chunk.id,
                    )
                    self.session.delete(chunk)
            else:
                for chunk in document.chunks[:]:
                    self.clear_chunk_child_chunks(
                        account_id,
                        knowledge_base_id,
                        chunk.id,
                    )
                    self.session.delete(chunk)
            self.session.commit()

    def clear_chunk_child_chunks(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        chunk_id: uuid.UUID,
        position: int = None,
    ) -> None:
        """Clear child chunks corresponding to the chunk"""
        query = (
            select(Chunk)
            .where(
                Chunk.id == chunk_id,
                Chunk.knowledge_base_id == knowledge_base_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        chunk = self.session.exec(query).first()
        if chunk:
            if position is not None:
                child_chunk = next(
                    (
                        child
                        for child in chunk.child_chunks
                        if child.position == position
                    ),
                    None,
                )
                if child_chunk:
                    self.session.delete(child_chunk)
            else:
                for child_chunk in chunk.child_chunks[:]:
                    if child_chunk:
                        self.session.delete(child_chunk)
            self.session.commit()

    def update_document_content(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        content: str,
    ) -> None:
        """Update document content"""
        query = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.knowledge_base_id == knowledge_base_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        document.content = content
        self.session.commit()

    def get_document(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Document:
        """Get a document from the knowledge base"""
        query = (
            select(Document)
            .where(
                Document.knowledge_base_id == knowledge_base_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                Document.id == document_id,
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        return document

    def create_chunk(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        document_name: str,
        content: str,
        word_count: int,
        position: int,
        keywords: list,
    ) -> uuid.UUID:
        """Create a new chunk in the specified document"""
        self.clear_document_chunks(
            account_id=account_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            position=position,
        )
        chunk = Chunk(
            document_id=document_id,
            document_name=document_name,
            content=content,
            creator_id=account_id,
            knowledge_base_id=knowledge_base_id,
            word_count=word_count,
            position=position,
            keywords=keywords,
        )
        self.session.add(chunk)
        self.session.commit()
        return chunk.id

    def create_child_chunk(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        chunk_id: uuid.UUID,
        content: str,
        word_count: int,
        position: int,
    ) -> uuid.UUID:
        """Create a new child chunk in the specified chunk"""
        child_chunk = ChildChunk(
            document_id=document_id,
            chunk_id=chunk_id,
            content=content,
            creator_id=account_id,
            knowledge_base_id=knowledge_base_id,
            word_count=word_count,
            position=position,
        )
        chunk = self.session.get(Chunk, chunk_id)
        child_chunk.chunk = chunk
        self.session.add(child_chunk)
        chunk.child_chunks.append(child_chunk)
        self.session.commit()
        return child_chunk.id

    def get_enabled_document_ids(
        self,
        knowledge_base_id: uuid.UUID,
        account_id: Optional[str] = None,
    ) -> list[uuid.UUID]:
        """get enabled document ids for retrieval"""

        if account_id:
            query = (
                select(Document)
                .where(
                    Document.knowledge_base_id == knowledge_base_id,
                    Document.enabled,
                )
                .join(
                    KnowledgeBasePermission,
                    KnowledgeBasePermission.knowledge_base_id
                    == knowledge_base_id,
                )
                .where(
                    KnowledgeBasePermission.account_id == account_id,
                    KnowledgeBasePermission.has_permission,
                )
            )
        else:
            query = select(Document).where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.enabled,
            )
        documents = self.session.exec(query).all()
        return [document.id for document in documents]

    def get_chunk(
        self,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        account_id: Optional[str] = None,
    ) -> Chunk:
        """get chunk ids"""
        if account_id:
            query = (
                select(Chunk)
                .where(
                    Document.id == document_id,
                )
                .join(
                    KnowledgeBasePermission,
                    KnowledgeBasePermission.knowledge_base_id
                    == knowledge_base_id,
                )
                .where(
                    KnowledgeBasePermission.account_id == account_id,
                    KnowledgeBasePermission.has_permission,
                )
            )
        else:
            query = select(Chunk).where(
                Document.id == document_id,
            )
        chunks = self.session.exec(query).all()
        return chunks

    def get_embedding_model_dict(
        self,
        knowledge_base_id: uuid.UUID,
        account_id: Optional[str] = None,
    ) -> dict:
        """Get embedding model dict"""
        if account_id:
            query = (
                select(KnowledgeBase)
                .where(
                    KnowledgeBase.id == knowledge_base_id,
                )
                .join(
                    KnowledgeBasePermission,
                    KnowledgeBasePermission.knowledge_base_id
                    == knowledge_base_id,
                )
                .where(
                    KnowledgeBasePermission.account_id == account_id,
                    KnowledgeBasePermission.has_permission,
                )
            )
        else:
            query = select(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_base_id,
            )
        knowledge_base = self.session.exec(query).first()
        return knowledge_base.get_embedding_model_dict

    def set_document_status(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        enabled: bool,
    ) -> None:
        """Disable a specified document"""
        query = (
            select(Document)
            .where(
                Document.id == document_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        if not enabled:
            document.disable_time = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S",
            )
            document.disabler_id = account_id
        document.enabled = enabled

        # for chunk in document.chunks:
        #     self.set_chunk_status(
        #         account_id,
        #         knowledge_base_id,
        #         chunk.id,
        #         status,
        #     )

        self.session.commit()

    def set_chunk_status(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        chunk_id: uuid.UUID,
        enabled: bool,
    ) -> None:
        """Disable a specified chunk"""
        query = (
            select(Chunk)
            .where(
                Chunk.id == chunk_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        chunk = self.session.exec(query).first()
        if not enabled:
            chunk.gmt_disabled = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S",
            )
            chunk.disabler_id = account_id
        chunk.enabled = enabled
        self.session.commit()

    def update_chunk(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        chunk_id: uuid.UUID,
        content: str,
        doc_name: Optional[str],
        title: Optional[str] = None,
    ) -> None:
        """Update chunk content"""
        query = (
            select(Chunk)
            .where(
                Chunk.id == chunk_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        chunk = self.session.exec(query).first()
        chunk.content = content
        if doc_name:
            chunk.document_name = doc_name
        if title:
            chunk.title = title
        self.session.commit()

    def set_document_process_config(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        process_config: dict,
    ) -> None:
        """set document chunk type"""
        query = (
            select(Document)
            .where(
                Document.id == document_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        document.process_config = process_config
        self.session.commit()

    def get_document_chunk_type(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> str:
        """get document chunk type"""
        query = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.knowledge_base_id == knowledge_base_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        return document.chunk_type

    def get_document_chunks_number(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> int:
        """Get the document chunks number"""
        query = (
            select(Document)
            .where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.id == document_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        if document:
            return len(document.chunks)
        return 0

    def get_document_chunks(
        self,
        account_id: str,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
        page: int,
        size: int,
        sort_order: Literal["desc", "asc"],
        sort_by: Literal["position"],
        search: Optional[str] = None,
    ) -> list:
        """Get the chunks of a document"""
        query = (
            select(Document)
            .where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.id == document_id,
            )
            .join(
                KnowledgeBasePermission,
                KnowledgeBasePermission.knowledge_base_id == knowledge_base_id,
            )
            .where(
                KnowledgeBasePermission.account_id == account_id,
                KnowledgeBasePermission.has_permission,
            )
        )
        document = self.session.exec(query).first()
        if not document or not document.chunks:
            return []

        chunks = document.chunks
        if search:
            chunks = [
                chunk
                for chunk in chunks
                if search.lower() in chunk.content.lower()
            ]

        if sort_order == "desc":
            chunks.sort(key=lambda x: getattr(x, sort_by), reverse=True)
        else:
            chunks.sort(key=lambda x: getattr(x, sort_by))

        start = (page - 1) * size
        end = start + size
        chunks = chunks[start:end]
        return [
            {
                "id": chunk.id,
                "content": chunk.content,
                "position": chunk.position,
            }
            for chunk in chunks
        ]
