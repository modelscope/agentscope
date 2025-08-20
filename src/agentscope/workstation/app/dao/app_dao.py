# -*- coding: utf-8 -*-
""" AppDAO"""
from app.dao.base_dao import BaseDAO
from app.models.app import AppEntity


class AppDAO(BaseDAO[AppEntity]):
    """AppDAO"""

    _model_class = AppEntity
