# -*- coding: utf-8 -*-
"""The database related services"""
from typing import Generator, Any

import redis
from redis import Redis
from sqlmodel import Session, SQLModel
from sqlalchemy import event, String, MetaData
from sqlalchemy.engine import Connection

from loguru import logger

from app.core.config import settings
from app.models.engine import engine


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    """Create the database, tables and default data."""
    SQLModel.metadata.create_all(engine)


def init_db() -> None:
    """Initialize the database."""

    # pylint: disable=unused-argument
    @event.listens_for(SQLModel.metadata, "before_create")
    def _set_varchar_length(
        target: MetaData,
        connection: Connection,
        **kw: Any,
    ) -> None:
        for table in target.tables.values():
            for column in table.columns:
                if (
                    isinstance(
                        column.type,
                        String,
                    )
                    and column.type.length is None
                ):
                    column.type.length = 255

    create_db_and_tables()
    logger.info("Database initialization completed successfully.")


async def init_fast_api_limiter_redis() -> Redis:
    """Initialize FastAPI Limiter Redis"""
    from redis.asyncio import Redis as AsyncRedis

    return AsyncRedis(
        host=settings.REDIS_SERVER,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB_FASTAPI_LIMITER,
        password=settings.REDIS_PASSWORD,  # Add password support
    )


def init_redis(endpoint: int = 0) -> Redis:
    """Initialize Redis"""
    redis_client = redis.from_url(
        f"redis://{settings.REDIS_SERVER}:{settings.REDIS_PORT}"
        f"/{endpoint}",
    )
    return redis_client
