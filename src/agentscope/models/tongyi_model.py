# -*- coding: utf-8 -*-
"""Model wrapper for OpenAI models"""
from typing import Any

import dashscope
from loguru import logger

from .model import ModelWrapperBase, ModelResponse

from ..utils.monitor import MonitorFactory
from ..utils.monitor import get_full_name
from ..utils import QuotaExceededError
from ..constants import _DEFAULT_API_BUDGET


class TongyiWrapper(ModelWrapperBase):
    """The model wrapper for OpenAI API."""

    def __init__(
        self,
        config_name: str,
        model_name: str = None,
        api_key: str = None,
        client_args: dict = None,
        generate_args: dict = None,
        budget: float = _DEFAULT_API_BUDGET,
        **kwargs: Any,
    ) -> None:
        """Initialize the openai client.

        Args:
            config_name (`str`):
                The name of the model config.
            model_name (`str`, default `None`):
                The name of the model to use in OpenAI API.
            api_key (`str`, default `None`):
                The API key for OpenAI API. If not specified, it will
                be read from the environment variable `OPENAI_API_KEY`.
            client_args (`dict`, default `None`):
                The extra keyword arguments to initialize the OpenAI client.
            generate_args (`dict`, default `None`):
                The extra keyword arguments used in openai api generation,
                e.g. `temperature`, `seed`.
            budget (`float`, default `None`):
                The total budget using this model. Set to `None` means no
                limit.
        """
        if model_name is None:
            model_name = config_name
        super().__init__(
            config_name=config_name,
            model_name=model_name,
            client_args=client_args,
            generate_args=generate_args,
            budget=budget,
            **kwargs,
        )
        if dashscope is None:
            raise ImportError(
                "Cannot find dashscope package in current python environment.",
            )

        self.model = model_name or config_name
        self.generate_args = generate_args or {}

        self.api_key = api_key
        dashscope.api_key = self.api_key
        self.max_length = None

        # Set monitor accordingly
        self.monitor = None
        self.budget = budget
        self._register_budget()
        self._register_default_metrics()

    def _register_budget(self) -> None:
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register_budget(
            model_name=self.model,
            value=self.budget,
            prefix=self.model,
        )

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        raise NotImplementedError(
            "The _register_default_metrics function is not Implemented.",
        )

    def _metric(self, metric_name: str) -> str:
        """Add the class name and model name as prefix to the metric name.

        Args:
            metric_name (`str`):
                The metric name.

        Returns:
            `str`: Metric name of this wrapper.
        """
        return get_full_name(name=metric_name, prefix=self.model)


class TongyiChatWrapper(TongyiWrapper):
    """The model wrapper for OpenAI's chat API."""

    model_type: str = "tongyi_chat"

    def _register_default_metrics(self) -> None:
        # Set monitor accordingly
        # TODO: set quota to the following metrics
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register(
            self._metric("prompt_tokens"),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("completion_tokens"),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("total_tokens"),
            metric_unit="token",
        )

    def __call__(
        self,
        messages: list,
        **kwargs: Any,
    ) -> ModelResponse:
        """Processes a list of messages to construct a payload for the OpenAI
        API call. It then makes a request to the OpenAI API and returns the
        response. This method also updates monitoring metrics based on the
        API response.

        Each message in the 'messages' list can contain text content and
        optionally an 'image_urls' key. If 'image_urls' is provided,
        it is expected to be a list of strings representing URLs to images.
        These URLs will be transformed to a suitable format for the OpenAI
        API, which might involve converting local file paths to data URIs.

        Args:
            messages (`list`):
                A list of messages to process.
            **kwargs (`Any`):
                The keyword arguments to OpenAI chat completions API,
                e.g. `temperature`, `max_tokens`, `top_p`, etc. Please refer to
                https://platform.openai.com/docs/api-reference/chat/create
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                The response text in text field, and the raw response in
                raw field.

        Note:
            `parse_func`, `fault_handler` and `max_retries` are reserved for
            `_response_parse_decorator` to parse and check the response
            generated by model wrapper. Their usages are listed as follows:
                - `parse_func` is a callable function used to parse and check
                the response generated by the model, which takes the response
                as input.
                - `max_retries` is the maximum number of retries when the
                `parse_func` raise an exception.
                - `fault_handler` is a callable function which is called
                when the response generated by the model is invalid after
                `max_retries` retries.
        """

        # step1: prepare keyword arguments
        kwargs = {**self.generate_args, **kwargs}

        # step2: checking messages
        if not all("role" in msg and "content" in msg for msg in messages):
            raise ValueError(
                "Each message in the 'messages' list must contain a 'role' "
                "and 'content' key for OpenAI API.",
            )

        # For Tongyi model, the "role" value of the first and the last message
        # must be "user"
        if len(messages) > 0:
            messages[0]["role"] = "user"
            messages[-1]["role"] = "user"

        # step3: forward to generate response
        response = dashscope.Generation.call(
            model=self.model,
            messages=messages,
            result_format="message",  # set the result to be "message" format.
            **kwargs,
        )

        # step4: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model,
                "messages": messages,
                **kwargs,
            },
            json_response=response,
        )

        # step5: update monitor accordingly
        try:
            self.monitor.update(
                response.usage,
                prefix=self.model,
            )
        except QuotaExceededError as e:
            # TODO: optimize quota exceeded error handling process
            logger.error(e.message)

        # step6: return response
        return ModelResponse(
            text=response.output["choices"][0]["message"]["content"],
            raw=response,
        )
