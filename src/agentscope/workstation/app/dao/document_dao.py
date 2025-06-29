# -*- coding: utf-8 -*-
"""The data access object layer for document in knowledge base."""
import uuid
from sqlmodel import Session, select, func, delete, update

from app.dao.base_dao import BaseDAO
from app.models.knowledge_base import Document


class DocumentDao(BaseDAO[Document]):
    """Data access object layer for knowledge base."""

    _model_class = Document
