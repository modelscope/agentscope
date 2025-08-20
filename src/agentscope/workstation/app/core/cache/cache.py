# -*- coding: utf-8 -*-
"""Cache"""
from typing import Any, Optional
import json
import redis
from app.core.config import settings

from loguru import logger


class Cache:
    """Cache"""

    def __init__(
        self,
        host: str = settings.REDIS_SERVER,
        port: int = settings.REDIS_PORT,
        db: int = 0,
        username: str = settings.REDIS_USER,
        password: str = settings.REDIS_PASSWORD,
    ) -> None:
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            username=username,
            password=password,
            decode_responses=True,
        )

    def set(self, key: str, value: dict, ex: Any = None) -> bool:
        """Store or update cache"""
        try:
            serialized = json.dumps(value)
            return self.redis.set(f"cache:{key}", serialized, ex=ex)
        except (TypeError, redis.RedisError) as e:
            logger.error(f"Cache set error: {e}")
            return False

    def get(self, key: str) -> Optional[dict]:
        """Get cache"""
        try:
            data = self.redis.get(f"cache:{key}")
            return json.loads(data) if data else None
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.error(f"Cache get error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete cache"""
        try:
            return self.redis.delete(f"cache:{key}") > 0
        except redis.RedisError as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if cache exists"""
        try:
            return self.redis.exists(f"cache:{key}") == 1
        except redis.RedisError as e:
            logger.error(f"Cache exists check error: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time"""
        try:
            return self.redis.expire(f"cache:{key}", seconds)
        except redis.RedisError as e:
            logger.error(f"Cache expire error: {e}")
            return False
