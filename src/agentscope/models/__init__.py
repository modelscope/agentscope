# -*- coding: utf-8 -*-
""" Import modules in models package."""
import json
from typing import Union, Type

from loguru import logger

from .config import _ModelConfig
from .model import ModelWrapperBase
from .response import ModelResponse
from .post_model import (
    PostAPIModelWrapperBase,
    PostAPIChatWrapper,
)
from .openai_model import (
    OpenAIWrapperBase,
    OpenAIChatWrapper,
    OpenAIDALLEWrapper,
    OpenAIEmbeddingWrapper,
)
from .dashscope_model import (
    DashScopeChatWrapper,
    DashScopeImageSynthesisWrapper,
    DashScopeTextEmbeddingWrapper,
    DashScopeMultiModalWrapper,
)
from .ollama_model import (
    OllamaChatWrapper,
    OllamaEmbeddingWrapper,
    OllamaGenerationWrapper,
)
from .gemini_model import (
    GeminiChatWrapper,
    GeminiEmbeddingWrapper,
)
from .zhipu_model import (
    ZhipuAIChatWrapper,
    ZhipuAIEmbeddingWrapper,
)
from .litellm_model import (
    LiteLLMChatWrapper,
)


__all__ = [
    "ModelWrapperBase",
    "ModelResponse",
    "PostAPIModelWrapperBase",
    "PostAPIChatWrapper",
    "OpenAIWrapperBase",
    "OpenAIChatWrapper",
    "OpenAIDALLEWrapper",
    "OpenAIEmbeddingWrapper",
    "DashScopeChatWrapper",
    "DashScopeImageSynthesisWrapper",
    "DashScopeTextEmbeddingWrapper",
    "DashScopeMultiModalWrapper",
    "OllamaChatWrapper",
    "OllamaEmbeddingWrapper",
    "OllamaGenerationWrapper",
    "GeminiChatWrapper",
    "GeminiEmbeddingWrapper",
    "ZhipuAIChatWrapper",
    "ZhipuAIEmbeddingWrapper",
    "LiteLLMChatWrapper",
    "load_model_by_config_name",
    "load_config_by_name",
    "read_model_configs",
    "clear_model_configs",
]

_MODEL_CONFIGS: dict[str, dict] = {}


def _get_model_wrapper(model_type: str) -> Type[ModelWrapperBase]:
    """Get the specific type of model wrapper

    Args:
        model_type (`str`): The model type name.

    Returns:
        `Type[ModelWrapperBase]`: The corresponding model wrapper class.
    """
    wrapper = ModelWrapperBase.get_wrapper(model_type=model_type)
    if wrapper is None:
        logger.warning(
            f"Unsupported model_type [{model_type}],"
            "use PostApiModelWrapper instead.",
        )
        return PostAPIModelWrapperBase
    return wrapper


def load_config_by_name(config_name: str) -> Union[dict, None]:
    """Load the model config by name, and return the config dict."""
    return _MODEL_CONFIGS.get(config_name, None)


def load_model_by_config_name(config_name: str) -> ModelWrapperBase:
    """Load the model by config name, and return the model wrapper."""
    if len(_MODEL_CONFIGS) == 0:
        raise ValueError(
            "No model configs loaded, please call "
            "`read_model_configs` first.",
        )

    # Find model config by name
    if config_name not in _MODEL_CONFIGS:
        raise ValueError(
            f"Cannot find [{config_name}] in loaded configurations.",
        )
    config = _MODEL_CONFIGS.get(config_name, None)

    if config is None:
        raise ValueError(
            f"Cannot find [{config_name}] in loaded configurations.",
        )

    model_type = config.model_type

    kwargs = {k: v for k, v in config.items() if k != "model_type"}

    return _get_model_wrapper(model_type=model_type)(**kwargs)


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

    cfgs = None

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

    if cfgs is None:
        raise TypeError(
            f"Invalid type of model_configs, it could be a dict, a list of "
            f"dicts, or a path to a json file (containing a dict or a list "
            f"of dicts), but got {type(configs)}",
        )

    format_configs = _ModelConfig.format_configs(configs=cfgs)

    # check if name is unique
    for cfg in format_configs:
        if cfg.config_name in _MODEL_CONFIGS:
            logger.warning(
                f"config_name [{cfg.config_name}] already exists.",
            )
            continue
        _MODEL_CONFIGS[cfg.config_name] = cfg

    # print the loaded model configs
    logger.info(
        "Load configs for model wrapper: {}",
        ", ".join(_MODEL_CONFIGS.keys()),
    )
