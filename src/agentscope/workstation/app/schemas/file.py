# -*- coding: utf-8 -*-
"""file related schemas"""
import uuid

from app.models.file import FileBase
from sqlmodel import SQLModel


class FileInfo(FileBase):  # type: ignore[call-arg]
    """file info"""

    id: uuid.UUID


class UploadPolicy(SQLModel):
    """upload policy"""

    name: str
    path: str
    extension: str
    content_type: str
    size: int
