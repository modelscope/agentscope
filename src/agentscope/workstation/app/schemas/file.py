# -*- coding: utf-8 -*-
import uuid

from app.models.file import FileBase
from sqlmodel import SQLModel


class FileInfo(FileBase):  # type: ignore[call-arg]
    id: uuid.UUID


class UploadPolicy(SQLModel):
    name: str
    path: str
    extension: str
    content_type: str
    size: int
