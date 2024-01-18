# -*- coding: utf-8 -*-
"""Manage the file system for saving files, code and logs."""
import json
import os
from typing import Any, Union, Optional

import numpy as np

from agentscope._runtime import Runtime
from agentscope.utils.tools import _download_file, _get_timestamp
from agentscope.utils.tools import _generate_random_code
from agentscope.constants import (
    _DEFAULT_DIR,
    _DEFAULT_SUBDIR_CODE,
    _DEFAULT_SUBDIR_FILE,
    _DEFAULT_SUBDIR_INVOKE,
    _DEFAULT_SQLITE_DB_FILE,
    _DEFAULT_IMAGE_NAME,
)


class _FileManager:
    """A singleton class for managing the file system for saving files,
    code and logs."""

    _instance = None

    dir: str = _DEFAULT_DIR
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
        path = os.path.join(self.dir, Runtime.runtime_id, subdir)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def _get_file_path(self, file_name: str) -> str:
        """Get the path of the file."""
        return os.path.join(self.dir, Runtime.runtime_id, file_name)

    @property
    def dir_log(self) -> str:
        """The directory for saving logs."""
        return os.path.join(self.dir, Runtime.runtime_id)

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
    def file_db(self) -> str:
        """The path to the sqlite db file."""
        return self._get_file_path(_DEFAULT_SQLITE_DB_FILE)

    def init(self, save_dir: str, save_api_invoke: bool = False) -> None:
        """Set the directory for saving files."""
        self.dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        self.save_api_invoke = save_api_invoke

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


file_manager = _FileManager()
