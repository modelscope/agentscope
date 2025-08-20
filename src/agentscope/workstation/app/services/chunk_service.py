# -*- coding: utf-8 -*-
"""The knowledge base chunk related services"""
from app.dao.chunk_dao import ChunkDao
from .base_service import BaseService


class ChunkService(BaseService[ChunkDao]):
    """Service layer for document in knowledge base."""

    _dao_cls = ChunkDao
