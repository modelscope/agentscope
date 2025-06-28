# -*- coding: utf-8 -*-
from app.models.file import File

from app.dao.base_dao import BaseDAO


class FileDao(BaseDAO[File]):
    _model_class = File
