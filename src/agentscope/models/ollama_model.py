# -*- coding: utf-8 -*-
"""Model wrapper for Ollama models."""
from typing import Sequence, Any, Optional

from loguru import logger

from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.utils import QuotaExceededError, MonitorFactory

try:
    import ollama
except ImportError:
    ollama = None


class OllamaWrapperBase(ModelWrapperBase):
    """The base class for Ollama model wrappers.

    To use Ollama API, please
    1. First install ollama server from https://ollama.com/download and
    start the server
    2. Pull the model by `ollama pull {model_name}` in terminal
    After that, you can use the ollama API.
    """

    model: str
    """The model name used in ollama API."""

    options: dict
    """A dict contains the options for ollama generation API,
    e.g. {"temperature": 0, "seed": 123}"""

    keep_alive: str
    """Controls how long the model will stay loaded into memory following
    the request."""

    def __init__(
        self,
        config_name: str,
        model: str,
        options: dict = None,
        keep_alive: str = "5m",
    ) -> None:
        """Initialize the model wrapper for Ollama API.

        Args:
            model (`str`):
                The model name used in ollama API.
            options (`dict`, default `None`):
                The extra keyword arguments used in Ollama api generation,
                e.g. `{"temperature": 0., "seed": 123}`.
            keep_alive (`str`, default `5m`):
                Controls how long the model will stay loaded into memory
                following the request.
        """

        super().__init__(config_name=config_name)

        self.model = model
        self.options = options
        self.keep_alive = keep_alive

        self.monitor = None

        self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        raise NotImplementedError(
            "The _register_default_metrics function is not Implemented.",
        )


class OllamaChatWrapper(OllamaWrapperBase):
    """The model wrapper for Ollama chat API."""

    model_type: str = "ollama_chat"

    def __call__(
        self,
        messages: Sequence[dict],
        options: Optional[dict] = None,
        keep_alive: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate response from the given messages.

        Args:
            messages (`Sequence[dict]`):
                A list of messages, each message is a dict contains the `role`
                and `content` of the message.
            options (`dict`, default `None`):
                The extra arguments used in ollama chat API, which takes
                effect only on this call, and will be merged with the
                `options` input in the constructor,
                e.g. `{"temperature": 0., "seed": 123}`.
            keep_alive (`str`, default `None`):
                How long the model will stay loaded into memory following
                the request, which takes effect only on this call, and will
                override the `keep_alive` input in the constructor.

        Returns:
            `ModelResponse`:
                The response text in `text` field, and the raw response in
                `raw` field.
        """
        # step1: prepare parameters accordingly
        if options is None:
            options = self.options
        else:
            options = {**self.options, **options}

        keep_alive = keep_alive or self.keep_alive

        # step2: forward to generate response
        response = ollama.chat(
            model=self.model,
            messages=messages,
            options=options,
            keep_alive=keep_alive,
            **kwargs,
        )

        # step2: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model,
                "messages": messages,
                "options": options,
                "keep_alive": keep_alive,
                **kwargs,
            },
            response=response,
        )

        # step3: monitor the response
        try:
            prompt_tokens = response["prompt_eval_count"]
            completion_tokens = response["eval_count"]
            self.monitor.update(
                {
                    "call_counter": 1,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            )
        except (QuotaExceededError, KeyError) as e:
            logger.error(e.message)

        # step4: return response
        return ModelResponse(
            text=response["message"]["content"],
            raw=response,
        )

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register(
            self._metric("call_counter", self.model),
            metric_unit="times",
        )
        self.monitor.register(
            self._metric("prompt_tokens", self.model),
            metric_unit="tokens",
        )
        self.monitor.register(
            self._metric("completion_tokens", self.model),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("total_tokens", self.model),
            metric_unit="token",
        )


class OllamaEmbeddingWrapper(OllamaWrapperBase):
    """The model wrapper for Ollama embedding API."""

    model_type: str = "ollama_embedding"

    def __call__(
        self,
        prompt: str,
        options: Optional[dict] = None,
        keep_alive: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate embedding from the given prompt.

        Args:
            prompt (`str`):
                The prompt to generate response.
            options (`dict`, default `None`):
                The extra arguments used in ollama embedding API, which takes
                effect only on this call, and will be merged with the
                `options` input in the constructor,
                e.g. `{"temperature": 0., "seed": 123}`.
            keep_alive (`str`, default `None`):
                How long the model will stay loaded into memory following
                the request, which takes effect only on this call, and will
                override the `keep_alive` input in the constructor.

        Returns:
            `ModelResponse`:
                The response embedding in `embedding` field, and the raw
                response in `raw` field.
        """
        # step1: prepare parameters accordingly
        if options is None:
            options = self.options
        else:
            options = {**self.options, **options}

        keep_alive = keep_alive or self.keep_alive

        # step2: forward to generate response
        response = ollama.embeddings(
            model=self.model,
            prompt=prompt,
            options=options,
            keep_alive=keep_alive,
            **kwargs,
        )

        # step3: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model,
                "prompt": prompt,
                "options": options,
                "keep_alive": keep_alive,
                **kwargs,
            },
            response=response,
        )

        # step4: monitor the response
        try:
            self.monitor.update(
                {"call_counter": 1},
                prefix=self.model,
            )
        except (QuotaExceededError, KeyError) as e:
            logger.error(e.message)

        # step5: return response
        return ModelResponse(
            embedding=response["embedding"],
            raw=response,
        )

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register(
            self._metric("call_counter", self.model),
            metric_unit="times",
        )


class OllamaGenerationWrapper(OllamaWrapperBase):
    """The model wrapper for Ollama generation API."""

    model_type: str = "ollama_generate"

    def __call__(
        self,
        prompt: str,
        options: Optional[dict] = None,
        keep_alive: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate response from the given prompt.

        Args:
            prompt (`str`):
                The prompt to generate response.
            options (`dict`, default `None`):
                The extra arguments used in ollama generation API, which takes
                effect only on this call, and will be merged with the
                `options` input in the constructor,
                e.g. `{"temperature": 0., "seed": 123}`.
            keep_alive (`str`, default `None`):
                How long the model will stay loaded into memory following
                the request, which takes effect only on this call, and will
                override the `keep_alive` input in the constructor.

        Returns:
            `ModelResponse`:
                The response text in `text` field, and the raw response in
                `raw` field.

        """
        # step1: prepare parameters accordingly
        if options is None:
            options = self.options
        else:
            options = {**self.options, **options}

        keep_alive = keep_alive or self.keep_alive

        # step2: forward to generate response
        response = ollama.generate(
            model=self.model,
            prompt=prompt,
            options=options,
            keep_alive=keep_alive,
        )

        # step3: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model,
                "prompt": prompt,
                "options": options,
                "keep_alive": keep_alive,
                **kwargs,
            },
            response=response,
        )

        # step4: monitor the response
        try:
            prompt_tokens = response["prompt_eval_count"]
            completion_tokens = response["eval_count"]
            self.monitor.update(
                {
                    "call_counter": 1,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            )
        except (QuotaExceededError, KeyError) as e:
            logger.error(e.message)

        # step5: return response
        return ModelResponse(
            text=response["response"],
            raw=response,
        )

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register(
            self._metric("call_counter", self.model),
            metric_unit="times",
        )
        self.monitor.register(
            self._metric("prompt_tokens", self.model),
            metric_unit="tokens",
        )
        self.monitor.register(
            self._metric("completion_tokens", self.model),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("total_tokens", self.model),
            metric_unit="token",
        )
