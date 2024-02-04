# -*- coding: utf-8 -*-
""" Import modules in models package."""
import json
from typing import Union, Type

from loguru import logger

from .config import ModelConfig
from .model import ModelWrapperBase, ModelResponse
from .post_model import (
    PostAPIModelWrapperBase,
    PostAPIChatWrapper,
)
from .openai_model import (
    OpenAIWrapper,
    OpenAIChatWrapper,
    OpenAIDALLEWrapper,
    OpenAIEmbeddingWrapper,
)


__all__ = [
    "ModelWrapperBase",
    "ModelResponse",
    "PostAPIModelWrapperBase",
    "OpenAIWrapper",
    "OpenAIChatWrapper",
    "OpenAIDALLEWrapper",
    "OpenAIEmbeddingWrapper",
    "load_model_by_id",
    "read_model_configs",
    "clear_model_configs",
]

_MODEL_CONFIGS: dict[str, dict] = {}

_MODEL_MAP: dict[str, Type[ModelWrapperBase]] = {
    "openai": OpenAIChatWrapper,
    "openai_dall_e": OpenAIDALLEWrapper,
    "openai_embedding": OpenAIEmbeddingWrapper,
    "post_api": PostAPIModelWrapperBase,
    "post_api_chat": PostAPIChatWrapper,
}


def get_model(model_type: str) -> Type[ModelWrapperBase]:
    """Get the specific type of model wrapper

    Args:
        model_type (`str`): The model type name.

    Returns:
        `Type[ModelWrapperBase]`: The corresponding model wrapper class.
    """
    if model_type in _MODEL_MAP:
        return _MODEL_MAP[model_type]
    elif model_type in ModelWrapperBase.registry:
        return ModelWrapperBase.registry[  # type: ignore [return-value]
            model_type
        ]
    else:
        logger.warning(
            f"Unsupported model_type [{model_type}],"
            "use PostApiModelWrapper instead.",
        )
        return PostAPIModelWrapperBase


def load_model_by_id(model_id: str) -> ModelWrapperBase:
    """Load the model by name."""
    if len(_MODEL_CONFIGS) == 0:
        raise ValueError(
            "No model configs loaded, please call "
            "`read_model_configs` first.",
        )

    # Find model config by name
    if model_id not in _MODEL_CONFIGS:
        raise ValueError(
            f"Cannot find [{model_id}] in loaded configurations.",
        )
    config = _MODEL_CONFIGS[model_id]

    if config is None:
        raise ValueError(
            f"Cannot find [{model_id}] in loaded configurations.",
        )

    model_type = config.model_type
    return get_model(model_type=model_type)(**config)


def clear_model_configs() -> None:
    """Clear the loaded model configs."""
    _MODEL_CONFIGS.clear()


def read_model_configs(
    configs: Union[dict, str, list],
    clear_existing: bool = False,
) -> None:
    """read model configs from a path or a list of dicts.

    Args:
        configs (`Union[str, list, dict]`):
            The path of the model configs | a config dict | a list of model
            configs.
        clear_existing (`bool`, defaults to `False`):
            Whether to clear the loaded model configs before reading.

    Returns:
        `dict`:
            The model configs.
    """
    if clear_existing:
        clear_model_configs()

    if isinstance(configs, str):
        with open(configs, "r", encoding="utf-8") as f:
            cfgs = json.load(f)

    if isinstance(configs, dict):
        cfgs = [configs]

    if isinstance(configs, list):
        if not all(isinstance(_, dict) for _ in configs):
            raise ValueError(
                "The model config unit should be a dict.",
            )
        cfgs = configs

    format_configs = ModelConfig.format_configs(configs=cfgs)

    # check if name is unique
    for cfg in format_configs:
        if cfg.model_id in _MODEL_CONFIGS:
            raise ValueError(f"model_id [{cfg.model_id}] already exists.")
        _MODEL_CONFIGS[cfg.model_id] = cfg

    # print the loaded model configs
    logger.info(
        "Load configs for model wrapper: {}",
        ", ".join(_MODEL_CONFIGS.keys()),
    )
