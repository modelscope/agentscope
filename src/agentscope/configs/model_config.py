# -*- coding: utf-8 -*-
"""The model config."""
from typing import Any


DEFAULT_MAX_RETRIES = 3
DEFAULT_MESSAGES_KEY = "inputs"


class CfgBase(dict):
    """Base class for model config."""

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def init(self, **kwargs: Any) -> None:
        """Initialize the config with the given arguments, and checking the
        type of the arguments."""
        cls = self.__class__
        for k, v in kwargs.items():
            if k in cls.__dict__["__annotations__"]:
                required_type = cls.__dict__["__annotations__"][k]
                if isinstance(v, required_type):
                    self[k] = v
                else:
                    raise TypeError(
                        f"The argument {k} should be "
                        f"{required_type}, but got {type(v)} "
                        f"instead.",
                    )


class OpenAICfg(CfgBase):
    """The config for OpenAI models."""

    type: str = "openai"
    """The typing of this config."""

    name: str
    """The name of the model."""

    model_name: str = None
    """The name of the model, (e.g. gpt-4, gpt-3.5-turbo). Default to `name` if
    not provided."""

    api_key: str = None
    """The api key used for OpenAI API. Will be read from env if not
    provided."""

    organization: str = None
    """The organization used for OpenAI API. Will be read from env if not
    provided."""

    client_args: dict = None
    """The arguments used to initialize openai client, e.g. `timeout`,
    `max_retries`."""

    generate_args: dict = None
    """The arguments used in openai api generation, e.g. `temperature`,
    `seed`."""


class PostApiCfg(CfgBase):
    """The config for Post API. The final request post will be

    .. code-block:: python

        cfg = PostApiCfg(...)
        request.post(
            url=cfg.api_url,
            headers=cfg.headers,
            json={
                cfg.message_key: messages,
                **cfg.json_args
            },
            **cfg.post_args
        )

    """

    type: str = "post_api"
    """The typing of this config."""

    name: str
    """The name of the model."""

    api_url: str
    """The url of the model."""

    headers: dict = {}
    """The headers used for the request."""

    max_length: int = 2048
    """The max length of the model, if not provided, defaults to 2048 in
    model wrapper."""

    # TODO: add support for timeout
    timeout: int = 30
    """The timeout of the request."""

    json_args: dict = None
    """The additional arguments used within "json" keyword argument,
    e.g. `request.post(json={..., **json_args})`, which depends on the
    specific requirements of the model API."""

    post_args: dict = None
    """The keywords args used within `requests.post()`, e.g. `request.post(...,
    **generate_args)`, which depends on the specific requirements of the
    model API."""

    max_retries: int = DEFAULT_MAX_RETRIES
    """The max retries of the request."""

    messages_key: str = DEFAULT_MESSAGES_KEY
    """The key of the prompt messages in `requests.post()`,
    e.g. `request.post(json={${messages_key}: messages, **json_args})`. For
    huggingface and modelscope inference API, the key is `inputs`"""


class TongyiCfg(CfgBase):
    """The config for OpenAI models."""

    type: str = "tongyi"
    """The typing of this config."""

    name: str
    """The name of the model."""

    model_name: str = None
    """The name of the model, (e.g. qwen-72b-chat). Default to `name` if
    not provided."""

    api_key: str = None
    """The api key used for OpenAI API. Will be read from env if not
    provided."""

    organization: str = None
    """The organization used for OpenAI API. Will be read from env if not
    provided."""

    client_args: dict = None
    """The arguments used to initialize openai client, e.g. `timeout`,
    `max_retries`."""

    generate_args: dict = None
    """The arguments used in openai api generation, e.g. `temperature`,
    `seed`."""
