# -*- coding: utf-8 -*-
"""Celery configuration"""
# flake8: noqa: E402
# pylint: disable=wrong-import-position, unused-import,
from celery import Celery
from app.core.config import settings
from loguru import logger


broker_url = (
    f"redis://{settings.REDIS_USER}:{settings.REDIS_PASSWORD}"
    f"@{settings.REDIS_SERVER}"
    f":{settings.REDIS_PORT}/"
    f"{settings.REDIS_DB_CELERY}"
)
logger.info(f"Generated Redis URL: {broker_url}")

# Configure the Celery app with the broker and backend
celery_app = Celery(
    settings.PROJECT_NAME,
    broker=broker_url,
    backend=broker_url,
)

logger.info(
    f"Celery configuration broker: {celery_app.conf.broker_url}",
)
logger.info(
    f"Celery configuration backend: {celery_app.conf.result_backend}",
)

# Import task modules to ensure they're registered with Celery
from app.tasks import workflow
