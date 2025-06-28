# -*- coding: utf-8 -*-
from app.dao.base_dao import BaseDAO
from app.models.api_key import ApiKeyEntity


class ApiKeyDAO(BaseDAO[ApiKeyEntity]):
    _model_class = ApiKeyEntity
