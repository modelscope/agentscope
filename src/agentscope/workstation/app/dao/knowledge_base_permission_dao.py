# -*- coding: utf-8 -*-
"""The data access object layer for document in knowledge base."""

from app.dao.base_dao import BaseDAO
from app.models.knowledge_base import KnowledgeBasePermission


class KnowledgeBasePermissionDao(BaseDAO[KnowledgeBasePermission]):
    """Data access object layer for knowledge base permission."""

    _model_class = KnowledgeBasePermission
