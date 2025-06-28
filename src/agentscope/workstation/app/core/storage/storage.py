# -*- coding: utf-8 -*-
import shutil
from pathlib import Path


class Storage:
    def save_file(self, filename: str, data: bytes) -> None:
        filename_path = Path(filename).expanduser().resolve()
        filename_path.write_bytes(data)

    def load_file(self, filename: str) -> bytes:
        filename_path = Path(filename).expanduser().resolve()
        if not filename_path.exists():
            msg = f"File not found: {filename_path}"
            raise FileNotFoundError(msg)
        return filename_path.read_bytes()

    def download_file(self, filename: str, target_filename: str) -> None:
        filename_path = Path(filename).expanduser().resolve()
        if not filename_path.exists():
            msg = f"File not found: {filename_path}"
            raise FileNotFoundError(msg)
        target_filename_path = Path(target_filename).expanduser().resolve()
        target_filename_path.write_bytes(filename_path.read_bytes())

    def delete_file(self, filename: str) -> None:
        filename_path = Path(filename).expanduser().resolve()
        if not filename_path.exists():
            msg = f"File not found: {filename_path}"
            raise FileNotFoundError(msg)
        filename_path.unlink()

    def mkdir(self, path: str) -> None:
        path = Path(path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)

    def create_directory(self, directory: str) -> None:
        self.mkdir(directory)

    def delete_directory(self, directory: str) -> None:
        directory_path = Path(directory).expanduser().resolve()
        if not directory_path.exists():
            msg = f"Directory not found: {directory_path}"
            raise FileNotFoundError(msg)
        elif not directory_path.is_dir():
            msg = f"{directory_path} is not a directory"
            raise NotADirectoryError(msg)
