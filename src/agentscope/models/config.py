# -*- coding: utf-8 -*-
"""The model config."""
from typing import Union, Sequence, Any

from loguru import logger


class ModelConfig(dict):
    """Base class for model config."""

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __init__(
        self,
        config_name: str,
        model_type: str = None,
        **kwargs: Any,
    ):
        """Initialize the config with the given arguments, and checking the
        type of the arguments.

        Args:
            config_name (`str`): A unique name of the model config.
            model_type (`str`, optional): The class name (or its model type) of
                the generated model wrapper. Defaults to None.

        Raises:
            `ValueError`: If `config_name` is not provided.
        """
        if config_name is None:
            raise ValueError("The `config_name` field is required for Cfg")
        if model_type is None:
            logger.warning(
                f"`model_type` is not provided in config [{config_name}],"
                " use `PostAPIModelWrapperBase` by default.",
            )
        super().__init__(
            config_name=config_name,
            model_type=model_type,
            **kwargs,
        )

    @classmethod
    def format_configs(
        cls,
        configs: Union[Sequence[dict], dict],
    ) -> Sequence:
        """Covert config dicts into a list of ModelConfig.

        Args:
            configs (Union[Sequence[dict], dict]): configs in dict format.

        Returns:
            Sequence[ModelConfig]: converted ModelConfig list.
        """
        if isinstance(configs, dict):
            return [ModelConfig(**configs)]
        return [ModelConfig(**cfg) for cfg in configs]
