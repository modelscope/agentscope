# -*- coding: utf-8 -*-
"""The knowledge base permission related services"""
import uuid

from .base_service import BaseService
from app.dao.knowledge_base_permission_dao import KnowledgeBasePermissionDao


class KnowledgeBasePermissionService(BaseService[KnowledgeBasePermissionDao]):
    """Service layer for knowledge base permission in knowledge base."""

    _dao_cls = KnowledgeBasePermissionDao
