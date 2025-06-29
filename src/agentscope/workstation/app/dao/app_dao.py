# -*- coding: utf-8 -*-
from app.dao.base_dao import BaseDAO
from app.models.app import AppEntity


class AppDAO(BaseDAO[AppEntity]):
    _model_class = AppEntity
