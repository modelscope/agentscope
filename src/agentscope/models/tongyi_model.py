# -*- coding: utf-8 -*-
from typing import Any, Union
from http import HTTPStatus

try:
    import dashscope
except ImportError:
    dashscope = None

from .model import ModelWrapperBase


class TongyiWrapper(ModelWrapperBase):
    """The model wrapper for dashscope API (with Qwen models)."""

    def __init__(
        self,
        name: str,
        model_name: str = None,
        api_key: str = None,
        organization: str = None,
        client_args: dict = None,
        generate_args: dict = None,
        **kwargs,
    ) -> None:
        """Initialize the openai client."""
        super().__init__(name)

        if dashscope is None:
            raise ImportError(
                "Cannot find dashscope package in current python environment.",
            )

        self.model_name = model_name or name
        self.generate_args = generate_args or {}

        self.api_key = api_key
        dashscope.api_key = self.api_key
        self.max_length = 8000


class TongyiChatModel(TongyiWrapper):
    def __call__(
        self,
        messages: list,
        return_raw: bool = False,
        **kwargs: Any,
    ) -> Union[str, dict]:
        response = dashscope.Generation.call(
            model=self.model_name,
            messages=messages,
            result_format="message",  # set the result to be "message" format.
        )

        if response.status_code == HTTPStatus.OK:
            if return_raw:
                return response
            else:
                return response.output.choices[0].message.content
        else:
            raise ValueError(response)
