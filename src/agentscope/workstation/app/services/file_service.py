# -*- coding: utf-8 -*-
"""The file related services"""
import uuid
from pathlib import Path

from fastapi import UploadFile
from loguru import logger
from sqlmodel import Session

from app.dao.file_dao import FileDao
from app.models.file import File

from .base_service import BaseService
from .storage_service import StorageService


class FileService(BaseService[File]):
    """The file service"""

    _dao_cls = FileDao

    def __init__(
        self,
        session: Session,
    ):
        super().__init__(session)
        self._storage_service = StorageService()

    def upload_file(
        self,
        account_id: str,
        category: str,
        file: UploadFile,
    ) -> File:
        """Upload a file"""
        filename = Path(file.filename)
        file_content = file.file.read()
        size = len(file_content)
        extension = filename.suffix.lower()
        file_id = uuid.uuid4()
        upload_path = self._storage_service.create_upload_directory(
            account_id=account_id,
            category=category,
        )
        storage_filename = f"{str(file_id)}{extension}"
        storage_path = upload_path / storage_filename

        file_record = File(
            id=file_id,
            filename=file.filename,
            name=file.filename,
            mime_type=file.content_type,
            content_type=file.content_type,
            extension=extension,
            size=size,
            account_id=account_id,
            storage_path=str(storage_path),
            path=str(storage_path),
        )

        self._storage_service.save_file(
            str(storage_path),
            file_content,
        )

        file_record = self.create(file_record.model_dump())
        return file_record

    def load_file(
        self,
        account_id: str,
        file_id: uuid.UUID,
    ) -> bytes:
        """Load a file"""
        file = self.get(file_id)
        if file.account_id != account_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )
        return self._storage_service.load_file(
            file.storage_path,
        )

    def download_file(
        self,
        account_id: str,
        file_id: uuid.UUID,
        target_filename: str,
    ) -> None:
        """Download a file"""
        file = self.get(file_id)
        if file.account_id != account_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )
        self._storage_service.download_file(
            file.storage_path,
            target_filename,
        )

    def delete_file(
        self,
        account_id: str,
        file_id: uuid.UUID,
    ) -> None:
        """Delete a file"""
        file = self.get(file_id)
        if file.account_id != account_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )
        self._storage_service.delete_file(
            file.storage_path,
        )
        logger.info(f"Deleted file: {file.id}")
        self.delete(file_id)
