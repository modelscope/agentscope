# -*- coding: utf-8 -*-
"""The storage related services"""
from pathlib import Path

from app.core.config import settings
from app.core.storage import Storage


class StorageService(Storage):
    """The storage service"""

    def __init__(self) -> None:
        """init"""
        self.root = Path(settings.LOCAL_STORAGE_DIR).expanduser().resolve()

    def create_upload_directory(self, account_id: str, category: str) -> Path:
        """Create a directory for uploads"""
        upload_path = self._generate_upload_directory(
            account_id=account_id,
            category=category,
        )
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

    def get_upload_directory(self, account_id: str, category: str) -> Path:
        """Get the upload directory"""
        return self.create_upload_directory(
            account_id=account_id,
            category=category,
        )

    def _generate_upload_directory(
        self,
        account_id: str,
        category: str,
    ) -> Path:
        """Generate the upload directory"""
        return Path(self.root) / account_id / category
