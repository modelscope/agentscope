# -*- coding: utf-8 -*-
"""The knowledge base related tasks"""
import uuid
from typing import Optional

from sqlmodel import Session

from app.models.engine import engine
from app.services.knowledge_base_service import KnowledgeBaseService
from app.db.init_db import get_session
from app.core.config import settings
from loguru import logger


def process_document_task(
    account_id: str,
    knowledge_base_id: str,
    document_ids: list[str],
    process_config: dict,
    workspace_id: str = settings.WORKSPACE_ID,
) -> None:
    """The celery task for processing documents."""
    kb_uuid = uuid.UUID(knowledge_base_id)

    for document_id_str in document_ids:
        doc_uuid = uuid.UUID(document_id_str)
        session = None
        try:
            session = Session(engine)

            knowledge_base_service = KnowledgeBaseService(session=session)

            knowledge_base_service.document_indexing(
                account_id=account_id,
                knowledge_base_id=kb_uuid,
                workspace_id=workspace_id,
                document_id=doc_uuid,
                process_config=process_config,
            )
            session.commit()
            logger.info(f"Document indexing completed for {doc_uuid}")

        except Exception as e:
            if session:
                session.rollback()
                logger.error(
                    f"Document indexing failed for {doc_uuid}:" f" {str(e)}",
                )
            new_session = None
            try:
                new_session = Session(engine)
                kb_service = KnowledgeBaseService(session=new_session)
                kb_service.update_document_indexing_status(
                    account_id=account_id,
                    knowledge_base_id=kb_uuid,
                    document_id=doc_uuid,
                    indexing_status="failed",
                )
                new_session.commit()
            except Exception as status_e:
                logger.error(
                    f"Failed to update status: {str(status_e)}",
                )
            finally:
                if new_session:
                    new_session.close()
        finally:
            if session:
                session.close()


def update_knowledge_base_task(
    # session: SessionDep,
    account_id: str,
    knowledge_base_id: str,
    workspace_id: str,
    kb_type: str,
    name: str,
    description: str,
    index_config: Optional[dict] = None,
    search_config: Optional[dict] = None,
    process_config: Optional[dict] = None,
) -> None:
    """The celery task for updating the knowledge base."""
    try:
        for session in get_session():
            try:
                knowledge_base_service = KnowledgeBaseService(
                    session=session,
                )

                knowledge_base_service.update_knowledge_base(
                    account_id=account_id,
                    knowledge_base_id=uuid.UUID(knowledge_base_id),
                    workspace_id=workspace_id,
                    kb_type=kb_type,
                    name=name,
                    description=description,
                    index_config=index_config,
                    search_config=search_config,
                    process_config=process_config,
                )
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to update knowledge base: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to update knowledge base: {str(e)}")
