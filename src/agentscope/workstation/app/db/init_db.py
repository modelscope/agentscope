# -*- coding: utf-8 -*-
"""The database related services"""
import json
import uuid
from datetime import datetime
from typing import Generator, Any

import redis
from redis import Redis
from sqlmodel import Session, SQLModel
from sqlalchemy import event, String, update, MetaData, select
from sqlalchemy.engine import Connection

from loguru import logger

from app.core.config import settings
from app.models.engine import engine
from app.models.account import Account

# from app.models.app import Workspace
from app.models.provider import ProviderBase
from app.models.model import ModelEntity
from app.utils.crypto import encrypt_with_rsa
from app.utils.security import verify_password, get_password_hash


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    """Create the database, tables and default data."""
    SQLModel.metadata.create_all(engine)


def init_db() -> None:
    """Initialize the database."""

    @event.listens_for(SQLModel.metadata, "before_create")
    def _set_varchar_length(
        target: MetaData,
        connection: Connection,  # pylint: disable=unused-argument
        **kw: Any,  # pylint: disable=unused-argument
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
    # Create initial data in dependency order
    # create_initial_user()
    # create_initial_workspace()
    # create_initial_provider()
    # create_initial_models()
    logger.info("Database initialization completed successfully.")


def create_initial_user() -> None:
    """Create an initial administrator user"""

    now = datetime.now()
    admin_password = "123456"

    with Session(engine) as session:
        existing_user = session.execute(
            select(Account).where(Account.username == "admin"),
        ).first()
        if not existing_user:
            account_id = str(
                uuid.uuid4(),
            )  # Use a fixed ID to match SQL initialization
            # script
            new_user = Account(
                account_id=account_id,
                username="admin",
                email="admin@example.com",
                type="admin",
                status=1,
                gmt_create=now,
                gmt_modified=now,
                creator=account_id,
                modifier=account_id,
                gmt_last_login=now,
                password=get_password_hash(admin_password),
            )
            session.add(new_user)
            session.commit()
            logger.info("Created initial administrator user: agentscope")
        else:
            hashed_password = get_password_hash(admin_password)
            session.execute(
                update(Account)
                .where(Account.username == "admin")
                .values(
                    password=hashed_password,
                    gmt_modified=now,
                    modifier="system_reset",
                ),
            )
            session.commit()
            logger.info(
                "The administrator user password has been reset: admin",
            )

            updated_user = (
                session.execute(
                    select(Account).where(Account.username == "admin"),
                )
                .scalars()
                .first()
            )

            if updated_user and verify_password(
                admin_password,
                updated_user.password,
            ):
                logger.info("✅ Password verification successful!")
            else:
                logger.info("❌ Password verification failed!")


def create_initial_provider() -> None:
    """Create the initial provider."""
    now = datetime.now()

    with Session(engine) as session:
        existing_provider = session.execute(
            select(ProviderBase).where(
                ProviderBase.workspace_id == "1",
                ProviderBase.name == "Tongyi",
            ),
        ).first()

        if not existing_provider:
            credential = {
                "endpoint": "https://dashscope.aliyuncs.com/compatible-mode",
                "api_key": encrypt_with_rsa(settings.DASHSCOPE_API_KEY),
            }

            new_provider = ProviderBase(
                workspace_id="1",
                icon=None,
                name="Tongyi",
                description="Tongyi",
                provider="Tongyi",
                enable=1,
                source="preset",
                credential=json.dumps(credential),
                supported_model_types=None,
                protocol="OpenAI",
                gmt_create=now,
                gmt_modified=now,
                creator=None,
                modifier=None,
            )
            session.add(new_provider)
            session.commit()
            logger.info("Created Tongyi provider")

        else:
            credential = {
                "endpoint": "https://dashscope.aliyuncs.com/compatible-mode",
                "api_key": encrypt_with_rsa(settings.DASHSCOPE_API_KEY),
            }

            session.execute(
                update(ProviderBase)
                .where(ProviderBase.provider == "Tongyi")
                .values(
                    credential=json.dumps(credential),
                    gmt_modified=now,
                ),
            )
            session.commit()
            logger.info(
                "The provider credential has been reset.",
            )


def create_initial_models() -> None:
    """Create the initial models."""
    now = datetime.now()

    # Define model data
    models_data = [
        {
            "name": "qwen-max",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen-max",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "web_search,function_call",
        },
        {
            "name": "qwen-max-latest",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen-max-latest",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "web_search,function_call,reasoning",
        },
        {
            "name": "qwen-plus",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen-plus",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "web_search,function_call",
        },
        {
            "name": "qwen-plus-latest",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen-plus-latest",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "web_search,function_call,reasoning",
        },
        {
            "name": "qwen-turbo",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen-turbo",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "web_search,function_call",
        },
        {
            "name": "qwen-turbo-latest",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen-turbo-latest",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "web_search,function_call,reasoning",
        },
        {
            "name": "qwen3-235b-a22b",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen3-235b-a22b",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "function_call,reasoning",
        },
        {
            "name": "qwen3-30b-a3b",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen3-30b-a3b",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "function_call,reasoning",
        },
        {
            "name": "qwen3-32b",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen3-32b",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "function_call,reasoning",
        },
        {
            "name": "qwen3-14b",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen3-14b",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "function_call,reasoning",
        },
        {
            "name": "qwen3-8b",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen3-8b",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "function_call,reasoning",
        },
        {
            "name": "qwen3-4b",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen3-4b",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "function_call,reasoning",
        },
        {
            "name": "qwen3-1.7b",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen3-1.7b",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "function_call,reasoning",
        },
        {
            "name": "qwen3-0.6b",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen3-0.6b",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "function_call,reasoning",
        },
        {
            "name": "qwen-vl-max",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen-vl-max",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "vision,function_call",
        },
        {
            "name": "qwen-vl-plus",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwen-vl-plus",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "vision,function_call",
        },
        {
            "name": "qvq-max",
            "type": "llm",
            "mode": "chat",
            "model_id": "qvq-max",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "vision,reasoning",
        },
        {
            "name": "qwq-plus",
            "type": "llm",
            "mode": "chat",
            "model_id": "qwq-plus",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "reasoning,function_call",
        },
        {
            "name": "text-embedding-v1",
            "type": "text_embedding",
            "mode": "chat",
            "model_id": "text-embedding-v1",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "embedding",
        },
        {
            "name": "text-embedding-v2",
            "type": "text_embedding",
            "mode": "chat",
            "model_id": "text-embedding-v2",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "embedding",
        },
        {
            "name": "text-embedding-v3",
            "type": "text_embedding",
            "mode": "chat",
            "model_id": "text-embedding-v3",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "embedding",
        },
        {
            "name": "gte-rerank-v2",
            "type": "rerank",
            "mode": "chat",
            "model_id": "gte-rerank-v2",
            "provider": "Tongyi",
            "enable": 1,
            "tags": None,
        },
        {
            "name": "deepseek-r1",
            "type": "llm",
            "mode": "chat",
            "model_id": "deepseek-r1",
            "provider": "Tongyi",
            "enable": 1,
            "tags": "reasoning",
        },
    ]

    with Session(engine) as session:
        created_count = 0
        for model_data in models_data:
            # Check if the model already exists
            existing_model = session.execute(
                select(ModelEntity).where(
                    ModelEntity.workspace_id == "1",
                    ModelEntity.name == model_data["name"],
                ),
            ).first()

            if not existing_model:
                # Create a new model
                new_model = ModelEntity(
                    workspace_id="1",
                    icon=None,
                    name=model_data["name"],
                    type=model_data["type"],
                    mode=model_data["mode"],
                    model_id=model_data["model_id"],
                    provider=model_data["provider"],
                    enable=model_data["enable"],
                    tags=model_data["tags"],
                    source="preset",
                    gmt_create=now,
                    gmt_modified=now,
                    creator=None,
                    modifier=None,
                )
                session.add(new_model)
                created_count += 1

        if created_count > 0:
            session.commit()
            logger.info(f"Created {created_count} initial models")
        else:
            logger.info("No new models needed to be created")


async def init_fast_api_limiter_redis() -> Redis:
    """Initialize FastAPI Limiter Redis"""
    from redis.asyncio import (
        Redis,
    )  # Use the new version of the asynchronous client

    return Redis(
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
