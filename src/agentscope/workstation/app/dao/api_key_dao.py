# -*- coding: utf-8 -*-
""" ApiKeyDAO"""
from app.dao.base_dao import BaseDAO
from app.models.api_key import ApiKeyEntity


class ApiKeyDAO(BaseDAO[ApiKeyEntity]):
    """ApiKeyDAO"""

    _model_class = ApiKeyEntity
