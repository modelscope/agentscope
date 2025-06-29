# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, Integer
from sqlmodel import SQLModel, Field

from app.models.field import formatted_datetime_field


class ModelEntity(SQLModel, table=True):
    __tablename__ = "model"  # type: ignore

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    workspace_id: Optional[str] = Field(
        sa_column=Column(String(64), nullable=True),
        description="工作空间ID",
    )
    icon: Optional[str] = Field(
        sa_column=Column(String(255), nullable=True),
        description="图标",
    )
    name: Optional[str] = Field(
        sa_column=Column(String(100), nullable=True),
        description="名称",
    )
    type: str = Field(
        default="LLM",
        sa_column=Column(String(100), nullable=True),
        description="模型类型，LLM等",
    )
    mode: str = Field(
        default="chat",
        sa_column=Column(String(100), nullable=True),
        description="模型模式",
    )
    model_id: str = Field(
        sa_column=Column(String(100), nullable=False),
        description="模型ID",
    )
    provider: str = Field(
        sa_column=Column(String(100), nullable=False),
        description="提供商标识",
    )
    enable: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=True),
        description="是否启用",
    )
    tags: Optional[str] = Field(
        sa_column=Column(String(255), nullable=True),
        description="模型标签，多个标签用逗号分隔",
    )
    source: str = Field(
        default="preset",
        sa_column=Column(String(100), nullable=False),
        description="来源-preset:预置,custom:自定义",
    )
    gmt_create: datetime = formatted_datetime_field()
    gmt_modified: datetime = formatted_datetime_field()
    creator: Optional[str] = Field(
        sa_column=Column(String(64), nullable=True),
        description="创建者",
    )
    modifier: Optional[str] = Field(
        sa_column=Column(String(64), nullable=True),
        description="修改者",
    )
