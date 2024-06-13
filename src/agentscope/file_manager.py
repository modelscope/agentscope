# -*- coding: utf-8 -*-
"""Manage the file system for saving files, code and logs."""
import json
import os
from typing import Any, Union, Optional, List, Literal
from pathlib import Path
import numpy as np

from agentscope._runtime import _runtime
from agentscope.utils.tools import _download_file, _get_timestamp, _hash_string
from agentscope.utils.tools import _generate_random_code
from agentscope.constants import (
    _DEFAULT_DIR,
    _DEFAULT_SUBDIR_CODE,
    _DEFAULT_SUBDIR_FILE,
    _DEFAULT_SUBDIR_INVOKE,
    _DEFAULT_SQLITE_DB_PATH,
    _DEFAULT_IMAGE_NAME,
    _DEFAULT_CFG_NAME,
)


def _get_text_embedding_record_hash(
    text: str,
    embedding_model: Optional[Union[str, dict]],
    hash_method: Literal["sha256", "md5", "sha1"] = "sha256",
) -> str:
    """Get the hash of the text embedding record."""
    original_data_hash = _hash_string(text, hash_method)

    if isinstance(embedding_model, dict):
        # Format the dict to avoid duplicate keys
        embedding_model = json.dumps(embedding_model, sort_keys=True)
    embedding_model_hash = _hash_string(embedding_model, hash_method)

    # Calculate the embedding id by hashing the hash codes of the
    # original data and the embedding model
    record_hash = _hash_string(
        original_data_hash + embedding_model_hash,
        hash_method,
    )

    return record_hash


class _FileManager:
    """A singleton class for managing the file system for saving files,
    code and logs."""

    _instance = None

    cache_dir: str = str(Path.home() / ".cache" / "agentscope")

    hash_method: Literal["sha256", "md5", "sha1"] = "sha256"

    dir: str = os.path.abspath(_DEFAULT_DIR)
    """The directory for saving files, code and logs."""

    save_api_invoke: bool = False
    """Whether to save api invocation locally."""

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create a singleton instance."""
        if not cls._instance:
            cls._instance = super(_FileManager, cls).__new__(
                cls,
                *args,
                **kwargs,
            )
        return cls._instance

    def _get_and_create_subdir(self, subdir: str) -> str:
        """Get the path of the subdir and create the subdir if it does not
        exist."""
        path = os.path.join(self.dir, _runtime.runtime_id, subdir)
        os.makedirs(path, exist_ok=True)
        return path

    def _get_file_path(self, file_name: str) -> str:
        """Get the path of the file."""
        return os.path.join(self.dir, _runtime.runtime_id, file_name)

    @property
    def dir_cache(self) -> str:
        """The directory for saving cache files."""
        return self.cache_dir

    @property
    def dir_cache_embedding(self) -> str:
        """Obtain the embedding cache directory."""
        dir_cache_embedding = os.path.join(self.cache_dir, "embedding")
        if not os.path.exists(dir_cache_embedding):
            os.makedirs(dir_cache_embedding)
        return dir_cache_embedding

    @property
    def dir_root(self) -> str:
        """The root directory to save code, information and logs."""
        return os.path.join(self.dir, _runtime.runtime_id)

    @property
    def dir_log(self) -> str:
        """The directory for saving logs."""
        return os.path.join(self.dir, _runtime.runtime_id)

    @property
    def dir_file(self) -> str:
        """The directory for saving files, including images, audios and
        videos."""
        return self._get_and_create_subdir(_DEFAULT_SUBDIR_FILE)

    @property
    def dir_code(self) -> str:
        """The directory for saving codes."""
        return self._get_and_create_subdir(_DEFAULT_SUBDIR_CODE)

    @property
    def dir_invoke(self) -> str:
        """The directory for saving api invocations."""
        return self._get_and_create_subdir(_DEFAULT_SUBDIR_INVOKE)

    @property
    def path_db(self) -> str:
        """The path to the sqlite db file."""
        return self._get_file_path(_DEFAULT_SQLITE_DB_PATH)

    def init(self, save_dir: str, save_api_invoke: bool = False) -> None:
        """Set the directory for saving files."""
        self.dir = os.path.abspath(save_dir)
        runtime_dir = os.path.join(save_dir, _runtime.runtime_id)
        os.makedirs(runtime_dir, exist_ok=True)

        self.save_api_invoke = save_api_invoke

        # Save the project and name to the runtime directory
        self._save_config()

    def _save_config(self) -> None:
        """Save the configuration of the runtime in its root directory."""
        cfg = {
            "project": _runtime.project,
            "name": _runtime.name,
            "run_id": _runtime.runtime_id,
            "timestamp": _runtime.timestamp,
            "pid": os.getpid(),
        }
        with open(
            os.path.join(self.dir_root, _DEFAULT_CFG_NAME),
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(cfg, file, indent=4)

    def save_api_invocation(
        self,
        prefix: str,
        record: dict,
    ) -> Union[None, str]:
        """Save api invocation locally."""
        if self.save_api_invoke:
            filename = f"{prefix}_{_generate_random_code()}.json"
            path_save = os.path.join(str(self.dir_invoke), filename)
            with open(path_save, "w", encoding="utf-8") as file:
                json.dump(record, file, indent=4)

            return filename
        else:
            return None

    def save_image(
        self,
        image: Union[str, np.ndarray],
        filename: Optional[str] = None,
    ) -> str:
        """Save image file locally, and return the local image path.

        Args:
            image (`Union[str, np.ndarray]`):
                The image url, or the image array.
            filename (`Optional[str]`):
                The filename of the image. If not specified, a random filename
                will be used.
        """

        if filename is None:
            filename = _DEFAULT_IMAGE_NAME.format(
                _get_timestamp(
                    "%Y%m%d-%H%M%S",
                ),
                _generate_random_code(),
            )

        path_file = os.path.join(self.dir_file, filename)

        if isinstance(image, str):
            # download the image from url
            _download_file(image, path_file)
        else:
            from PIL import Image

            # save image via PIL
            Image.fromarray(image).save(path_file)

        return path_file

    def cache_text_embedding(
        self,
        text: str,
        embedding: List[float],
        embedding_model: Union[str, dict],
    ) -> None:
        """Cache the text embedding locally."""
        record_hash = _get_text_embedding_record_hash(
            text,
            embedding_model,
            self.hash_method,
        )

        # Save the embedding to the cache directory
        np.save(
            os.path.join(
                self.dir_cache_embedding,
                f"{record_hash}.npy",
            ),
            embedding,
        )

    def fetch_cached_text_embedding(
        self,
        text: str,
        embedding_model: Union[str, dict],
    ) -> Union[None, List[float]]:
        """Fetch the text embedding from the cache."""
        record_hash = _get_text_embedding_record_hash(
            text,
            embedding_model,
            self.hash_method,
        )

        try:
            return np.load(
                os.path.join(
                    self.dir_cache_embedding,
                    f"{record_hash}.npy",
                ),
            )
        except FileNotFoundError:
            return None

    @staticmethod
    def _flush() -> None:
        """
        Only for unittest usage. Don't use this function in your code.
        Flush the file_manager singleton.
        """
        global file_manager
        file_manager = _FileManager()


file_manager = _FileManager()
