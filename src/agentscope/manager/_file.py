# -*- coding: utf-8 -*-
"""Manage the file system for saving files, code and logs."""
import io
import json
import os
import shutil
from typing import Any, Union, Optional, List, Literal, Generator
import numpy as np
from PIL import Image

from agentscope.utils.tools import _download_file
from agentscope.utils.tools import _hash_string
from agentscope.utils.tools import _get_timestamp
from agentscope.utils.tools import _generate_random_code
from agentscope.constants import (
    _DEFAULT_SUBDIR_CODE,
    _DEFAULT_SUBDIR_FILE,
    _DEFAULT_SUBDIR_INVOKE,
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


class FileManager:
    """A singleton class for managing the file system for saving files,
    code and logs."""

    _instance = None

    __serialized_attrs = [
        # Flags
        "save_log",
        "save_code",
        "save_api_invoke",
        # Basic directory
        "base_dir",
        "run_dir",
        "cache_dir",
    ]

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create a singleton instance."""
        if cls._instance is None:
            cls._instance = super(FileManager, cls).__new__(cls)
        else:
            raise RuntimeError(
                "The file manager has been initialized. Try to use "
                "FileManager.get_instance() to get the instance.",
            )

        return cls._instance

    def __init__(self) -> None:
        """Initialize the file manager with default values."""
        self.save_log = False
        self.save_code = False
        self.save_api_invoke = False

        self.cache_dir = None
        self.base_dir = None
        self.run_dir = None

    def initialize(
        self,
        run_dir: Union[str, None],
        save_log: bool,
        save_code: bool,
        save_api_invoke: bool,
        cache_dir: str,
    ) -> None:
        """Set the directory for saving files.

        Args:
            run_dir (`Union[str, None]`):
                The running directory, used to save files, logs and code.
            save_log (`bool`):
                Whether to save logs locally.
            save_code (`bool`):
                Whether to save code locally.
            save_api_invoke (`bool`):
                Whether to save API invocations locally.
            cache_dir (`str`):
                The directory to save cache files.
        """
        self.save_log = save_log
        self.save_code = save_code
        self.save_api_invoke = save_api_invoke

        self.cache_dir = cache_dir

        # Initialize the path of the sub dirs
        self.run_dir = run_dir

        if self.run_dir is not None:
            os.makedirs(self.run_dir, exist_ok=True)

    def _get_and_create_subdir(self, subdir: str) -> str:
        """Get the path of the subdir and create the subdir if it does not
        exist."""
        if self.run_dir is None:
            return "./"
        else:
            path = os.path.join(self.run_dir, subdir)
            os.makedirs(path, exist_ok=True)
            return path

    @property
    def embedding_cache_dir(self) -> str:
        """Obtain the embedding cache directory."""
        if self.cache_dir is None:
            raise ValueError(
                "The cache directory is not specified. Please specify the "
                "cache directory when initializing the file manager.",
            )
        dir_cache_embedding = os.path.join(self.cache_dir, "embedding")
        os.makedirs(dir_cache_embedding, exist_ok=True)
        return dir_cache_embedding

    @property
    def file_dir(self) -> str:
        """The directory for saving files, including images, audios and
        videos."""
        # To be compatible with files saving when disable_saving is True
        return self._get_and_create_subdir(_DEFAULT_SUBDIR_FILE)

    @property
    def code_dir(self) -> str:
        """The directory for saving codes."""
        return self._get_and_create_subdir(_DEFAULT_SUBDIR_CODE)

    @property
    def invoke_dir(self) -> str:
        """The directory for saving api invocations."""
        return self._get_and_create_subdir(_DEFAULT_SUBDIR_INVOKE)

    @classmethod
    def get_instance(cls) -> "FileManager":
        """Get the singleton instance."""
        if cls._instance is None:
            raise ValueError(
                "AgentScope hasn't been initialized. Please call "
                "`agentscope.init` function first.",
            )
        return cls._instance

    def save_api_invocation(
        self,
        prefix: str,
        record: dict,
    ) -> Union[None, str]:
        """Save api invocation locally."""
        if self.save_api_invoke:
            filename = f"{prefix}_{_generate_random_code()}.json"
            path_save = os.path.join(str(self.invoke_dir), filename)
            with open(path_save, "w", encoding="utf-8") as file:
                json.dump(record, file, indent=4, ensure_ascii=False)

            return filename
        else:
            return None

    def save_python_code(self) -> None:
        """Save the code locally."""
        # Copy python file in os.path.curdir into runtime directory
        cur_dir = os.path.abspath(os.path.curdir)
        for filename in os.listdir(cur_dir):
            if filename.endswith(".py"):
                file_abs = os.path.join(cur_dir, filename)
                shutil.copy(file_abs, str(self.code_dir))

    def save_image(
        self,
        image: Union[str, np.ndarray, bytes, Image.Image],
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

        path_file = os.path.join(self.file_dir, filename)

        if isinstance(image, str):
            # download the image from url
            _download_file(image, path_file)
        elif isinstance(image, np.ndarray):
            # save image via PIL
            Image.fromarray(image).save(path_file)
        elif isinstance(image, bytes):
            # save image via bytes
            Image.open(io.BytesIO(image)).save(path_file)
        elif isinstance(image, Image.Image):
            # save image via PIL.Image.Image
            image.save(path_file)
        else:
            raise ValueError(
                f"Unsupported image type: {type(image)} Must be str, "
                f"np.ndarray, bytes, or PIL.Image.Image.",
            )

        return path_file

    def save_file(
        self,
        generator: Generator[bytes, None, None],
        filename: str,
    ) -> str:
        """Save file locally from a binary generator, and return the local
        file path.

        Note we don't block this function when `self.disable_saving==True`,
        because in distribution mode or calling image generation model with
        `save_local == True`, we still have to save files locally. However, we
        save them in "./" instead.

        Args:
            generator (`Generator[bytes, None, None]`):
                The generator of the binary file content.
            filename (`str`):
                The filename of the file.

        Returns:
            `str`: The local file path.
        """

        path_file = os.path.join(self.file_dir, filename)

        with open(path_file, "wb") as file:
            for chunk in generator:
                file.write(chunk)

        return path_file

    def save_runtime_information(self, runtime_info: dict) -> None:
        """Save the runtime information locally."""
        if self.run_dir is None:
            raise ValueError(
                "The run directory is not specified. Please set "
                "`disable_saving` to `False` and provide a valid `save_dir` "
                "in `agentscope.init()`.",
            )

        with open(
            os.path.join(
                self.run_dir,
                _DEFAULT_CFG_NAME,
            ),
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(runtime_info, file, indent=4, ensure_ascii=False)

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
            "sha256",
        )

        # Save the embedding to the cache directory
        np.save(
            os.path.join(
                self.embedding_cache_dir,
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
            "sha256",
        )

        try:
            return np.load(
                os.path.join(
                    self.embedding_cache_dir,
                    f"{record_hash}.npy",
                ),
            )
        except FileNotFoundError:
            return None

    def state_dict(self) -> dict:
        """Serialize the configuration into a dict."""
        serialized_data = {}

        for attr_name in self.__serialized_attrs:
            serialized_data[attr_name] = getattr(self, attr_name)

        return serialized_data

    def load_dict(self, data: dict) -> None:
        """Load the configuration from a dict."""
        for k in self.__serialized_attrs:
            assert k in data, f"Key {k} not found in data."
            setattr(self, k, data[k])

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the file manager has been initialized."""
        return cls._instance is not None

    def flush(self) -> None:
        """Flush the file manager."""
        self.save_log = False
        self.save_code = False
        self.save_api_invoke = False

        self.cache_dir = None
        self.base_dir = None
        self.run_dir = None
