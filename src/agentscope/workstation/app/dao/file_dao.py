# -*- coding: utf-8 -*-
"""The data access object layer for file."""
from app.models.file import File
from app.dao.base_dao import BaseDAO


class FileDao(BaseDAO[File]):
    """The data access object layer for file."""

    _model_class = File
