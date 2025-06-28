# -*- coding: utf-8 -*-
from datetime import datetime
from enum import unique, Enum
from typing import Optional

from sqlalchemy import Column, Integer, String
from sqlmodel import SQLModel, Field

from app.models.base import IntEnum


@unique
class ApiKeyStatus(int, Enum):
    DELETED = 0
    NORMAL = 1


class ApiKeyEntity(SQLModel, table=True):
    """
    Api key model
    """

    __tablename__ = "api_key"  # type: ignore

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
    )
    api_key: str = Field(
        default=None,
        sa_column=Column(String(512), nullable=False),
    )
    account_id: str = Field(
        default=None,
        sa_column=Column(String(64), nullable=False, index=True),
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(String(4096), nullable=True),
    )
    status: ApiKeyStatus = Field(
        default=1,
        sa_column=Column(IntEnum(ApiKeyStatus)),
    )
    gmt_create: datetime = Field(default_factory=datetime.now)
    gmt_modified: datetime = Field(default_factory=datetime.now)
    creator: str = Field(
        default=None,
        sa_column=Column(String(64), nullable=False),
    )
    modifier: str = Field(
        default=None,
        sa_column=Column(String(64), nullable=False),
    )
