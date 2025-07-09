# -*- coding: utf-8 -*-
"""The knowledge base document related services"""
from app.dao.document_dao import DocumentDao
from .base_service import BaseService


class DocumentService(BaseService[DocumentDao]):
    """Service layer for document in knowledge base."""

    _dao_cls = DocumentDao
