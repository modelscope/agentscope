# -*- coding: utf-8 -*-
"""The knowledge base permission related services"""
from app.dao.knowledge_base_permission_dao import KnowledgeBasePermissionDao
from .base_service import BaseService


class KnowledgeBasePermissionService(BaseService[KnowledgeBasePermissionDao]):
    """Service layer for knowledge base permission in knowledge base."""

    _dao_cls = KnowledgeBasePermissionDao
