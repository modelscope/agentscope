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
        model_id: str,
        model_type: str = None,
        **kwargs: Any,
    ):
        """Initialize the config with the given arguments, and checking the
        type of the arguments.

        Args:
            model_id (`str`): The id of the generated model wrapper.
            model_type (`str`, optional): The class name (or its alias) of
                the generated model wrapper. Defaults to None.

        Raises:
            `ValueError`: If `model_id` is not provided.
        """
        if model_id is None:
            raise ValueError("The `model_id` field is required for Cfg")
        if model_type is None:
            logger.warning(
                f"`model_type` is not provided in config [{model_id}],"
                " use `PostAPIModelWrapperBase` by default.",
            )
        super().__init__(
            model_id=model_id,
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
