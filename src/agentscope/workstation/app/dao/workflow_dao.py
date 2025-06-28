# -*- coding: utf-8 -*-
"""The workflow related dao"""
from app.dao.base_dao import BaseDAO

from app.models.workflow import WorkflowRuntime


class WorkflowDao(BaseDAO[WorkflowRuntime]):
    """Data access object layer for workflow"""

    _model_class = WorkflowRuntime
