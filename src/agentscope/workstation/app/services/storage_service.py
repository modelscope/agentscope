# -*- coding: utf-8 -*-
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.storage import Storage


class StorageService(Storage):
    def __init__(self) -> None:
        self.root = Path(settings.LOCAL_STORAGE_DIR).expanduser().resolve()

    def create_upload_directory(self, account_id: str, category: str) -> Path:
        upload_path = self._generate_upload_directory(
            account_id=account_id,
            category=category,
        )
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

    def get_upload_directory(self, account_id: str, category: str) -> Path:
        return self.create_upload_directory(
            account_id=account_id,
            category=category,
        )

    def _generate_upload_directory(
        self,
        account_id: str,
        category: str,
    ) -> Path:
        return Path(self.root) / account_id / category
