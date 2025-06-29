# -*- coding: utf-8 -*-
import uuid

from sqlmodel import Field, SQLModel

from .field import formatted_datetime_field


class FileBase(SQLModel):
    filename: str
    mime_type: str
    content_type: str
    extension: str
    size: int
    storage_path: str = Field(nullable=False)
    storage_type: str = Field(default="local", nullable=False)
    gmt_create: str = formatted_datetime_field()
    gmt_modified: str = formatted_datetime_field()
    account_id: str = Field(foreign_key="account.account_id")
    name: str
    path: str


class File(FileBase, table=True):  # type: ignore[call-arg]
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
