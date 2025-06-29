# -*- coding: utf-8 -*-
"""The knowledge base chunk related services"""
from .base_service import BaseService
from app.dao.chunk_dao import ChunkDao


class ChunkService(BaseService[ChunkDao]):
    """Service layer for document in knowledge base."""

    _dao_cls = ChunkDao
