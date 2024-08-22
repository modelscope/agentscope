# -*- coding: utf-8 -*-
"""The model manager for AgentScope."""
import json
from typing import Any, Union, Sequence

from loguru import logger

from ..models import ModelWrapperBase, _get_model_wrapper


class ModelManager:
    """The model manager for AgentScope, which is responsible for loading and
    managing model configurations and models."""

    model_configs: dict[str, dict] = {}
    """The model configs"""

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create a singleton instance."""
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        else:
            raise RuntimeError(
                "The Model manager has been initialized. Try to use "
                "ModelManager.get_instance() to get the instance.",
            )
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ModelManager":
        """Get the instance of the singleton class."""
        if cls._instance is None:
            raise ValueError(
                "AgentScope hasn't been initialized. Please call "
                "`agentscope.init` function first.",
            )
        return cls._instance

    def __init__(
        self,
    ) -> None:
        """Initialize the model manager with model configs"""
        self.model_configs = {}

    def initialize(
        self,
        model_configs: Union[dict, str, list, None] = None,
    ) -> None:
        """Initialize the model manager with model configs."""
        if model_configs is not None:
            self.load_model_configs(model_configs)

    def clear_model_configs(self) -> None:
        """Clear the loaded model configs."""
        self.model_configs.clear()

    def load_model_configs(
        self,
        model_configs: Union[dict, str, list],
        clear_existing: bool = False,
    ) -> None:
        """read model configs from a path or a list of dicts.

        Args:
            model_configs (`Union[str, list, dict]`):
                The path of the model configs | a config dict | a list of model
                configs.
            clear_existing (`bool`, defaults to `False`):
                Whether to clear the loaded model configs before reading.

        Returns:
            `dict`:
                The model configs.
        """
        if clear_existing:
            self.clear_model_configs()

        cfgs = None

        if isinstance(model_configs, str):
            with open(model_configs, "r", encoding="utf-8") as f:
                cfgs = json.load(f)

        if isinstance(model_configs, dict):
            cfgs = [model_configs]

        if isinstance(model_configs, list):
            if not all(isinstance(_, dict) for _ in model_configs):
                raise ValueError(
                    "The model config unit should be a dict.",
                )
            cfgs = model_configs

        if cfgs is None:
            raise TypeError(
                f"Invalid type of model_configs, it could be a dict, a list "
                f"of dicts, or a path to a json file (containing a dict or a "
                f"list of dicts), but got {type(model_configs)}",
            )

        formatted_configs = _format_configs(configs=cfgs)

        # check if name is unique
        for cfg in formatted_configs:
            if cfg["config_name"] in self.model_configs:
                logger.warning(
                    f"config_name [{cfg['config_name']}] already exists.",
                )
                continue
            self.model_configs[cfg["config_name"]] = cfg

        # print the loaded model configs
        logger.info(
            "Load configs for model wrapper: {}",
            ", ".join(self.model_configs.keys()),
        )

    def get_model_by_config_name(self, config_name: str) -> ModelWrapperBase:
        """Load the model by config name, and return the model wrapper."""
        if len(self.model_configs) == 0:
            raise ValueError(
                "No model configs loaded, please call "
                "`read_model_configs` first.",
            )

        # Find model config by name
        if config_name not in self.model_configs:
            raise ValueError(
                f"Cannot find [{config_name}] in loaded configurations.",
            )
        config = self.model_configs.get(config_name, None)

        if config is None:
            raise ValueError(
                f"Cannot find [{config_name}] in loaded configurations.",
            )

        model_type = config["model_type"]

        kwargs = {k: v for k, v in config.items() if k != "model_type"}

        return _get_model_wrapper(model_type=model_type)(**kwargs)

    def get_config_by_name(self, config_name: str) -> Union[dict, None]:
        """Load the model config by name, and return the config dict."""
        return self.model_configs.get(config_name, None)

    def state_dict(self) -> dict:
        """Serialize the model manager into a dict."""
        return {
            "model_configs": self.model_configs,
        }

    def load_dict(self, data: dict) -> None:
        """Load the model manager from a dict."""
        self.clear_model_configs()
        assert "model_configs" in data
        self.model_configs = data["model_configs"]

    def flush(self) -> None:
        """Flush the model manager."""
        self.clear_model_configs()


def _format_configs(
    configs: Union[Sequence[dict], dict],
) -> Sequence:
    """Check the format of model configs.

    Args:
        configs (Union[Sequence[dict], dict]): configs in dict format.

    Returns:
        Sequence[dict]: converted ModelConfig list.
    """
    if isinstance(configs, dict):
        configs = [configs]
    for config in configs:
        if "config_name" not in config:
            raise ValueError(
                "The `config_name` field is required for Cfg",
            )
        if "model_type" not in config:
            logger.warning(
                "`model_type` is not provided in config"
                f"[{config['config_name']}],"
                " use `PostAPIModelWrapperBase` by default.",
            )
    return configs
