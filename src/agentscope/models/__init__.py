# -*- coding: utf-8 -*-
""" Import modules in models package."""
import json
from typing import Union

from loguru import logger

from .model import ModelWrapperBase
from .post_model import PostApiModelWrapper
from .openai_model import (
    OpenAIWrapper,
    OpenAIChatWrapper,
    OpenAIDALLEWrapper,
    OpenAIEmbeddingWrapper,
)
from .tongyi_model import TongyiChatModel

__all__ = [
    "ModelWrapperBase",
    "PostApiModelWrapper",
    "OpenAIWrapper",
    "OpenAIChatWrapper",
    "OpenAIDALLEWrapper",
    "OpenAIEmbeddingWrapper",
    "load_model_by_name",
    "read_model_configs",
    "clear_model_configs",
]

from ..configs.model_config import OpenAICfg, PostApiCfg, TongyiCfg


_MODEL_CONFIGS = []


def load_model_by_name(model_name: str) -> ModelWrapperBase:
    """Load the model by name."""
    if len(_MODEL_CONFIGS) == 0:
        raise ValueError(
            "No model configs loaded, please call "
            "`read_model_configs` first.",
        )

    # Find model config by name
    config = None
    for _ in _MODEL_CONFIGS:
        if _["name"] == model_name:
            config = {**_}
            break

    if config is None:
        raise ValueError(
            f"Cannot find [{model_name}] in loaded configurations.",
        )

    model_type = config.pop("type")
    if model_type == "openai":
        return OpenAIChatWrapper(**config)
    elif model_type == "openai_dall_e":
        return OpenAIDALLEWrapper(**config)
    elif model_type == "openai_embedding":
        return OpenAIEmbeddingWrapper(**config)
    elif model_type == "post_api":
        return PostApiModelWrapper(**config)
    elif model_type == "tongyi":
        return TongyiChatModel(**config)
    else:
        raise ValueError(
            f"Cannot find [{config['type']}] in loaded configurations.",
        )


def clear_model_configs() -> None:
    """Clear the loaded model configs."""
    global _MODEL_CONFIGS
    _MODEL_CONFIGS = []


def read_model_configs(
    configs: Union[dict, str, list],
    empty_first: bool = False,
) -> None:
    """read model configs from a path or a list of dicts.

    Args:
        configs (`Union[str, list, dict]`):
            The path of the model configs | a config dict | a list of model
            configs.
        empty_first (`bool`, defaults to `False`):
            Whether to clear the loaded model configs before reading.

    Returns:
        `dict`:
            The model configs.
    """
    if empty_first:
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

    # Checking
    format_configs: list[Union[OpenAICfg, PostApiCfg]] = []
    for cfg in cfgs:
        if "type" not in cfg:
            raise ValueError(
                f"Cannot find `type` in model config: {cfg}, "
                f'whose value should be choice from ["openai", '
                f'"post_api"]',
            )

        if cfg["type"] == "openai":
            openai_cfg = OpenAICfg()
            openai_cfg.init(**cfg)
            format_configs += [openai_cfg]

        elif cfg["type"] == "post_api":
            post_api_cfg = PostApiCfg()
            post_api_cfg.init(**cfg)
            format_configs += [post_api_cfg]

        elif cfg["type"] == "tongyi":
            tongyi_cfg = TongyiCfg()
            tongyi_cfg.init(**cfg)
            format_configs += [tongyi_cfg]

        else:
            raise ValueError(
                f"Unknown model type: {cfg['type']}, please "
                f"choice from ['openai', 'post_api']]",
            )

    # check if name is unique
    global _MODEL_CONFIGS
    for cfg in format_configs:
        if cfg["name"] in [_["name"] for _ in _MODEL_CONFIGS]:
            raise ValueError(f'Model name "{cfg.name}" already exists.')

        _MODEL_CONFIGS.append(cfg)

    # print the loaded model configs
    model_names = [_["name"] for _ in _MODEL_CONFIGS]
    logger.info("Load configs for model: {}", ", ".join(model_names))
