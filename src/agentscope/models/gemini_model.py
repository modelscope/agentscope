# -*- coding: utf-8 -*-
"""Google Gemini model wrapper."""
import os
from collections.abc import Iterable
from typing import Sequence, Union, Any

from loguru import logger

from agentscope.message import Msg
from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.utils import QuotaExceededError, MonitorFactory

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiWrapperBase(ModelWrapperBase):
    """The base class for Google Gemini model wrapper."""

    _generation_method = None
    """The generation method used in `__call__` function, which is used to
    filter models in `list_models` function."""

    def __init__(
        self,
        config_name: str,
        model_name: str,
        api_key: str = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the wrapper for Google Gemini model.

        Args:
            model_name (`str`):
                The name of the model.
            api_key (`str`, defaults to `None`):
                The api_key for the model. If it is not provided, it will be
                loaded from environment variable.
        """
        # TODO: remove super().__init__()
        super().__init__(
            config_name,
            model_name=model_name,
            api_key=api_key,
            **kwargs,
        )

        # Load the api_key from argument or environment variable
        api_key = api_key or os.environ.get("GOOGLE_API_KEY")

        if api_key is None:
            raise ValueError(
                "Google api_key must be provided or set as an "
                "environment variable.",
            )

        genai.configure(api_key=api_key)

        self.model_name = model_name

        self.monitor = None
        self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        """Register the default metrics for the model."""
        raise NotImplementedError(
            "The method `_register_default_metrics` must be implemented.",
        )

    def list_models(self) -> Sequence:
        """List all available models for this API calling."""
        support_models = list(genai.list_models())

        if self.generation_method is None:
            return support_models
        else:
            return [
                _
                for _ in support_models
                if self._generation_method in _.supported_generation_methods
            ]

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        """Processing input with the model."""
        raise NotImplementedError(
            f"Model Wrapper [{type(self).__name__}]"
            f" is missing the  the required `__call__`"
            f" method.",
        )


class GeminiChatWrapper(GeminiWrapperBase):
    """The wrapper for Google Gemini chat model, e.g. gemini-pro"""

    model_type: str = "gemini_chat"
    """The type of the model, which is used in model configuration."""

    generation_method = "generateContent"
    """The generation method used in `__call__` function."""

    def __init__(
        self,
        config_name: str,
        model_name: str,
        api_key: str = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            config_name=config_name,
            model_name=model_name,
            api_key=api_key,
            **kwargs,
        )

        # Create the generative model
        self.model = genai.GenerativeModel(model_name, **kwargs)

    def __call__(
        self,
        contents: Union[Sequence, str],
        stream: bool = False,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate response for the given contents.

        Args:
            contents (`Union[Sequence, str]`):
                The content to generate response.
            stream (`bool`, defaults to `False`):
                Whether to use stream mode.
            **kwargs:
                The additional arguments for generating response.

        Returns:
            `ModelResponse`:
                The response text in text field, and the raw response in raw
                field.
        """
        # step1: checking messages
        if isinstance(contents, Iterable):
            pass
        elif not isinstance(contents, str):
            logger.warning(
                "The input content is not a string or a list of "
                "messages, which may cause unexpected behavior.",
            )

        # step2: forward to generate response
        # TODO: support response in stream mode
        response = self.model.generate_content(
            contents,
            stream=stream,
            **kwargs,
        )

        # step3: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "contents": contents,
                "stream": stream,
                **kwargs,
            },
            response=str(response),
        )

        # step5: update monitor accordingly
        # TODO: Up to 2024/03/11, the response from Gemini doesn't contain
        #  the detailed information about cost. Here we simply count
        #  the tokens manually.
        token_prompt = self.model.count_tokens(contents).total_tokens
        token_response = self.model.count_tokens(response.text).total_tokens
        try:
            self.monitor.update(
                {
                    "call_counter": 1,
                    "completion_tokens": token_response,
                    "prompt_tokens": token_prompt,
                    "total_tokens": token_prompt + token_response,
                },
                prefix=self.model.model_name,
            )
        except QuotaExceededError as e:
            logger.error(e.message)

        # step6: return response
        return ModelResponse(
            text=response.text,
            raw=response,
        )

    def _register_default_metrics(self) -> None:
        """Register the default metrics for the model."""
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register(
            self._metric("call_counter", prefix=self.model_name),
            metric_unit="times",
        )
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


class GeminiEmbeddingWrapper(GeminiWrapperBase):
    """The wrapper for Google Gemini embedding model,
    e.g. models/embedding-001"""

    model_type: str = "gemini_embedding"
    """The type of the model, which is used in model configuration."""

    _generation_method = "embedContent"
    """The generation method used in `__call__` function."""

    def __call__(
        self,
        content: Union[Sequence[Msg], str],
        task_type: str = None,
        title: str = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate embedding for the given content. More detailed information
        please refer to
        https://ai.google.dev/tutorials/python_quickstart#use_embeddings

        Args:
            content (`Union[Sequence[Msg], str]`):
                The content to generate embedding.
            task_type (`str`, defaults to `None`):
                The type of the task.
            title (`str`, defaults to `None`):
                The title of the content.
            **kwargs:
                The additional arguments for generating embedding.

        Returns:
            `ModelResponse`:
                The response embedding in embedding field, and the raw response
                in raw field.
        """

        # step1: forward to generate response
        response = genai.embed_content(
            model=self.model_name,
            content=content,
            task_type=task_type,
            title=title,
            **kwargs,
        )

        # step2: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "content": content,
                "task_type": task_type,
                "title": title,
                **kwargs,
            },
            response=response,
        )

        # TODO: Up to 2023/03/11, the embedding model doesn't support to
        #  count tokens.
        try:
            self.monitor.update(
                {
                    "call_counter": 1,
                },
                prefix=self.model_name,
            )
        except QuotaExceededError as e:
            logger.error(e.message)

        return ModelResponse(
            raw=response,
            embedding=response["embedding"],
        )

    def _register_default_metrics(self) -> None:
        """Register the default metrics for the model."""
        self.monitor = MonitorFactory.get_monitor()
        self.monitor.register(
            self._metric("call_counter", prefix=self.model_name),
            metric_unit="times",
        )
