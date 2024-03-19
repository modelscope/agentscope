# -*- coding: utf-8 -*-
"""Model wrapper for OpenAI models"""
from typing import Union, Any

from loguru import logger

from .model import ModelWrapperBase, ModelResponse
from ..file_manager import file_manager

try:
    import openai
except ImportError:
    openai = None

from ..utils.monitor import MonitorFactory
from ..utils import QuotaExceededError
from ..utils.token_utils import get_openai_max_length
from ..constants import _DEFAULT_API_BUDGET


class OpenAIWrapper(ModelWrapperBase):
    """The model wrapper for OpenAI API."""

    def __init__(
        self,
        config_name: str,
        model_name: str = None,
        api_key: str = None,
        organization: str = None,
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
            organization (`str`, default `None`):
                The organization ID for OpenAI API. If not specified, it will
                be read from the environment variable `OPENAI_ORGANIZATION`.
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
            logger.warning("model_name is not set, use config_name instead.")
        super().__init__(
            config_name=config_name,
            model_name=model_name,
            client_args=client_args,
            generate_args=generate_args,
            budget=budget,
            **kwargs,
        )

        if openai is None:
            raise ImportError(
                "Cannot find openai package in current python environment.",
            )

        self.model_name = model_name
        self.generate_args = generate_args or {}

        self.client = openai.OpenAI(
            api_key=api_key,
            organization=organization,
            **(client_args or {}),
        )

        # Set the max length of OpenAI model
        try:
            self.max_length = get_openai_max_length(self.model_name)
        except Exception as e:
            logger.warning(
                f"fail to get max_length for {self.model_name}: " f"{e}",
            )
            self.max_length = None

        # Set monitor accordingly
        self.monitor = None
        self.budget = budget
        self._register_budget(model_name, budget)
        self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        raise NotImplementedError(
            "The _register_default_metrics function is not Implemented.",
        )


class OpenAIChatWrapper(OpenAIWrapper):
    """The model wrapper for OpenAI's chat API."""

    model_type: str = "openai"

    def _register_default_metrics(self) -> None:
        # Set monitor accordingly
        # TODO: set quota to the following metrics
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register(
            self._metric("prompt_tokens", prefix=self.model_name),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("completion_tokens", prefix=self.model_name),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("total_tokens", prefix=self.model_name),
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
        if not isinstance(messages, list):
            raise ValueError(
                "OpenAI `messages` field expected type `list`, "
                f"got `{type(messages)}` instead.",
            )
        if not all("role" in msg and "content" in msg for msg in messages):
            raise ValueError(
                "Each message in the 'messages' list must contain a 'role' "
                "and 'content' key for OpenAI API.",
            )

        # step3: forward to generate response
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs,
        )

        # step4: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "messages": messages,
                **kwargs,
            },
            response=response.model_dump(),
        )

        # step5: update monitor accordingly
        try:
            self.monitor.update(
                response.usage.model_dump(),
                prefix=self.model_name,
            )
        except QuotaExceededError as e:
            # TODO: optimize quota exceeded error handling process
            logger.error(e.message)

        # step6: return response
        return ModelResponse(
            text=response.choices[0].message.content,
            raw=response.model_dump(),
        )


class OpenAIDALLEWrapper(OpenAIWrapper):
    """The model wrapper for OpenAI's DALL·E API."""

    model_type: str = "openai_dall_e"

    _resolutions: list = [
        "1792*1024",
        "1024*1792",
        "1024*1024",
        "512*512",
        "256*256",
    ]

    def _register_default_metrics(self) -> None:
        # Set monitor accordingly
        # TODO: set quota to the following metrics
        self.monitor = MonitorFactory.get_monitor()
        for resolution in self._resolutions:
            self.monitor.register(
                self._metric(resolution, prefix=self.model_name),
                metric_unit="image",
            )

    def __call__(
        self,
        prompt: str,
        save_local: bool = False,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Args:
            prompt (`str`):
                The prompt string to generate images from.
            save_local: (`bool`, default `False`):
                Whether to save the generated images locally, and replace
                the returned image url with the local path.
            **kwargs (`Any`):
                The keyword arguments to OpenAI image generation API, e.g.
                `n`, `quality`, `response_format`, `size`, etc. Please refer to
                https://platform.openai.com/docs/api-reference/images/create
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                A list of image urls in image_urls field and the
                raw response in raw field.

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

        # step2: forward to generate response
        try:
            response = self.client.images.generate(
                model=self.model_name,
                prompt=prompt,
                **kwargs,
            )
        except Exception as e:
            logger.error(
                f"Failed to generate images for prompt '{prompt}': {e}",
            )
            raise e

        # step3: record the model api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "prompt": prompt,
                **kwargs,
            },
            response=response.model_dump(),
        )

        # step4: return response
        raw_response = response.model_dump()
        images = raw_response["data"]
        # Get image urls as a list
        urls = [_["url"] for _ in images]

        if save_local:
            # Return local url if save_local is True
            urls = [file_manager.save_image(_) for _ in urls]
        return ModelResponse(image_urls=urls, raw=raw_response)


class OpenAIEmbeddingWrapper(OpenAIWrapper):
    """The model wrapper for OpenAI embedding API."""

    model_type: str = "openai_embedding"

    def _register_default_metrics(self) -> None:
        # Set monitor accordingly
        # TODO: set quota to the following metrics
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register(
            self._metric("prompt_tokens", prefix=self.model_name),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("total_tokens", prefix=self.model_name),
            metric_unit="token",
        )

    def __call__(
        self,
        texts: Union[list[str], str],
        **kwargs: Any,
    ) -> ModelResponse:
        """Embed the messages with OpenAI embedding API.

        Args:
            texts (`list[str]` or `str`):
                The messages used to embed.
            **kwargs (`Any`):
                The keyword arguments to OpenAI embedding API,
                e.g. `encoding_format`, `user`. Please refer to
                https://platform.openai.com/docs/api-reference/embeddings
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                A list of embeddings in embedding field and the
                raw response in raw field.

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

        # step2: forward to generate response
        response = self.client.embeddings.create(
            input=texts,
            model=self.model_name,
            **kwargs,
        )

        # step3: record the model api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "input": texts,
                **kwargs,
            },
            response=response.model_dump(),
        )

        # step4: return response
        response_json = response.model_dump()
        if len(response_json["data"]) == 0:
            return ModelResponse(
                embedding=response_json["data"]["embedding"][0],
                raw=response_json,
            )
        else:
            return ModelResponse(
                embedding=[_["embedding"] for _ in response_json["data"]],
                raw=response_json,
            )
