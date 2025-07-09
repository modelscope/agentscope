# -*- coding: utf-8 -*-
"""The data access object layer for chunk in knowledge base."""
from app.dao.base_dao import BaseDAO
from app.models.knowledge_base import Chunk


class ChunkDao(BaseDAO[Chunk]):
    """Data access object layer for knowledge base."""

    _model_class = Chunk
