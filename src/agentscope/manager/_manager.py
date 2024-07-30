# -*- coding: utf-8 -*-
"""A manager for AgentScope."""
import os
from typing import Union, Any

from loguru import logger

from ._monitor import MonitorManager
from ._file import FileManager
from ._model import ModelManager
from ..logging import LOG_LEVEL, setup_logger
from ..utils.tools import (
    _generate_random_code,
    _get_process_creation_time,
    _get_timestamp,
)
from ..constants import _RUNTIME_ID_FORMAT, _RUNTIME_TIMESTAMP_FORMAT
from ..studio._client import _studio_client


class ASManager:
    """A manager for AgentScope."""

    _instance = None

    __serialized_attrs = [
        "project",
        "name",
        "disable_saving",
        "run_id",
        "pid",
        "timestamp",
    ]

    def __new__(cls, *args: Any, **kwargs: Any) -> "ASManager":
        if cls._instance is None:
            cls._instance = super(ASManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ASManager":
        """Get the instance of the singleton class."""
        if cls._instance is None:
            raise ValueError(
                "AgentScope hasn't been initialized. Please call "
                "`agentscope.init` function first.",
            )
        return cls._instance

    def __init__(self) -> None:
        """Initialize the manager. Note we initialize the managers by default
        arguments to avoid unnecessary errors when user doesn't call
        `agentscope.init` function"""
        self.project = ""
        self.name = ""
        self.run_id = ""
        self.pid = -1
        self.timestamp = ""
        self.disable_saving = True

        self.file = FileManager()
        self.model = ModelManager()
        self.monitor = MonitorManager()

        # TODO: unified with logger and studio
        self.logger_level: LOG_LEVEL = "INFO"

    def initialize(
        self,
        model_configs: Union[dict, str, list, None],
        project: Union[str, None],
        name: Union[str, None],
        disable_saving: bool,
        save_dir: str,
        save_log: bool,
        save_code: bool,
        save_api_invoke: bool,
        cache_dir: str,
        use_monitor: bool,
        logger_level: LOG_LEVEL,
        run_id: Union[str, None],
        studio_url: Union[str, None],
    ) -> None:
        """Initialize the package."""
        # =============== Init the runtime ===============
        self.project = project or _generate_random_code()
        self.name = name or _generate_random_code(uppercase=False)

        self.pid = os.getpid()
        timestamp = _get_process_creation_time()

        self.timestamp = timestamp.strftime(_RUNTIME_TIMESTAMP_FORMAT)

        self.run_id = run_id or _get_timestamp(
            _RUNTIME_ID_FORMAT,
            timestamp,
        ).format(self.name)

        self.disable_saving = disable_saving

        # =============== Init the file manager ===============
        if disable_saving:
            save_log = False
            save_code = False
            save_api_invoke = False
            use_monitor = False
            run_dir = None
        else:
            run_dir = os.path.abspath(os.path.join(save_dir, self.run_id))

        self.file.initialize(
            run_dir=run_dir,
            save_log=save_log,
            save_code=save_code,
            save_api_invoke=save_api_invoke,
            cache_dir=cache_dir,
        )
        # Save the python code here to avoid duplicated saving in the child
        # process (when calling deserialize function)
        if save_code:
            self.file.save_python_code()

        # =============== Init the logger         ===============
        # TODO: unified with studio and gradio
        self.logger_level = logger_level
        # run_dir will be None if save_log is False
        setup_logger(self.file.run_dir, logger_level)

        # =============== Init the model manager  ===============
        self.model.initialize(model_configs)

        # =============== Init the monitor manager ===============
        self.monitor.initialize(use_monitor)

        # =============== Init the studio          ===============
        # TODO: unified with studio and gradio

        # Init studio client, which will push messages to web ui and fetch user
        # inputs from web ui
        if studio_url is not None:
            _studio_client.initialize(self.run_id, studio_url)
            # Register in AgentScope Studio
            _studio_client.register_running_instance(
                project=self.project,
                name=self.name,
                timestamp=self.timestamp,
                run_dir=self.file.run_dir,
                pid=self.pid,
            )

    def serialize(self) -> dict:
        """Serialize the runtime information."""
        serialized_data = {
            k: getattr(self, k) for k in self.__serialized_attrs
        }

        serialized_data["file"] = self.file.serialize()
        serialized_data["model"] = self.model.serialize()
        serialized_data["logger"] = {
            "level": self.logger_level,
        }
        serialized_data["studio"] = _studio_client.serialize()
        serialized_data["monitor"] = self.monitor.serialize()

        return serialized_data

    def deserialize(self, data: dict) -> None:
        """Load the runtime information."""
        for k in self.__serialized_attrs:
            assert k in data, f"Key {k} not found in data."
            setattr(self, k, data[k])

        self.file.deserialize(data["file"])
        # TODO: unified the logger with studio and gradio
        self.logger_level = data["logger"]["level"]
        setup_logger(self.file.run_dir, self.logger_level)
        self.model.deserialize(data["model"])
        _studio_client.deserialize(data["studio"])
        self.monitor.deserialize(data["monitor"])

    def flush(self) -> None:
        """Flush the runtime information."""
        self.project = ""
        self.name = ""
        self.run_id = ""
        self.pid = -1
        self.timestamp = ""
        self.disable_saving = True

        self.file.flush()
        self.model.flush()
        self.monitor.flush()
        logger.remove()
        _studio_client.flush()

        self.logger_level = "INFO"