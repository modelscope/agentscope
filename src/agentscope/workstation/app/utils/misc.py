# -*- coding: utf-8 -*-
"""get redis client"""
from typing import Generator

import redis
from redis import Redis

from app.core.config import settings


def get_redis_client() -> Generator[Redis, None, None]:
    """get redis client"""
    client = redis.Redis(
        host=settings.REDIS_SERVER,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB_CELERY,
        username=settings.REDIS_USER,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
    )
    try:
        yield client
    finally:
        client.close()
