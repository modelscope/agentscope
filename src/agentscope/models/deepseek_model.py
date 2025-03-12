# -*- coding: utf-8 -*-
"""Model Wrapper for DeepSeek Models."""

from abc import ABC
from typing import (
    Optional,
    Any,
    Union,
    List,
    Sequence,
    Generator,
)
from loguru import logger
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai._streaming import Stream

from .model import ModelWrapperBase, ModelResponse
from ..message import Msg
from ._model_utils import (
    _verify_text_content_in_openai_delta_response,
    _verify_text_content_in_openai_message_response,
)


def _verify_reasoning_content_in_openai_message_response(
    response: dict,
) -> bool:
    """Verify if the reasoning content exists in the openai message response

    Args:
        response (`dict`):
            The JSON-format OpenAI response (After calling `model_dump`
             function)

    Returns:
        `bool`: If the reasoning content exists
    """

    if len(response.get("choices", [])) == 0:
        return False

    if response["choices"][0].get("message", None) is None:
        return False

    if (
        response["choices"][0]["message"].get("reasoning_content", None)
        is None
    ):
        return False

    return True


def _verify_reasoning_content_in_openai_delta_response(
    response: dict,
) -> bool:
    """Verify if the reasoning content exists in the openai streaming response

    Args:
        response (`dict`):
            The JSON-format OpenAI response (After calling `model_dump`
             function)

    Returns:
        `bool`: If the reasoning content exists
    """

    if len(response.get("choices", [])) == 0:
        return False

    if response["choices"][0].get("delta", None) is None:
        return False

    if response["choices"][0]["delta"].get("reasoning_content", None) is None:
        return False

    return True


class DeepSeekWrapperBase(ModelWrapperBase, ABC):
    """The model wrapper for DeepSeek API."""

    def __init__(
        self,
        config_name: str,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        provider_url: Optional[str] = None,
        client_args: Optional[dict] = None,
        generate_args: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        """Initalize the openai client.
        Args:
            config_name (`str`):
                The name of the model configuration.
            model_name (`Optional[str]`):
                The name of the model. If not provided, the default model
                will be used.
            api_key (`Optional[str]`):
                The API key for the openai client.
            client_args (`Optional[dict]`):
                The arguments for the openai client.
            generate_args (`Optional[dict]`):
                The arguments for the generation. e.g. `temperature`,
                `max_tokens`
        """

        DEEPSEEK_URL: str = "https://api.deepseek.com"

        if model_name is None:
            model_name = config_name
            logger.warning("model_name is not set, use config_name instead.")

        if provider_url is None:
            provider_url = DEEPSEEK_URL
            logger.warning(
                "provider_url is not set," f"use offical {DEEPSEEK_URL}",
            )

        super().__init__(
            config_name=config_name,
            model_name=model_name,
        )

        self.generate_args = generate_args or {}

        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "Cannot find openai package, please install it by"
                "`pip install openai`",
            ) from e

        # Fixed max length for DeepSeek API
        DEEPSEEK_MAX_LENGTH: int = 8192

        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=provider_url,
            **(client_args or {}),
        )
        self.max_length = DEEPSEEK_MAX_LENGTH

    def format(
        self,
        *args: Union[Msg, Sequence[Msg]],
    ) -> Union[List[dict], str]:
        raise RuntimeError(
            f"Model Wrapper [{type(self).__name__}] doesn't "
            f"need to format the input. Please try to use the "
            f"model wrapper directly.",
        )


class DeepSeekChatWrapper(DeepSeekWrapperBase):
    """The model wrapper for DeepSeek Chat API."""

    model_type: str = "deepseek_chat"
    # Recommend use aliyun hosted deepseek
    # then the model name is deepseek-r1 and deepseek-v3

    supported_models: list[str] = [
        "deepseek-chat",
        "deepseek-reasoner",
        "deepseek-r1",
        "deepseek-v3",
    ]

    def __init__(
        self,
        config_name: str,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        provider_url: Optional[str] = None,
        stream: bool = True,
        generate_args: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        """Initalize the openai client.

        Args:
            config_name (`str`):
                The name of the model configuration.
            model_name (`Optional[str]`):
                The name of the model. If not provided, the default model
                will be used.
            api_key (`Optional[str]`):
                The API key for the openai client.
            stream (`bool`, default `True`):
                If the model should be used in streaming mode.
            generate_args (`Optional[dict]`):
                The arguments for the generation. e.g. `temperature`,
                `max_tokens`

        """

        super().__init__(
            config_name=config_name,
            model_name=model_name,
            api_key=api_key,
            provider_url=provider_url,
            generate_args=generate_args,
            **kwargs,
        )
        self.stream = stream
        if model_name not in self.supported_models:
            raise ValueError(
                f"DeepSeek model `{model_name}` is not supported, "
                f"only {self.supported_models} are supported",
            )
        self.is_reasoner = model_name in ["deepseek-reasoner", "deepseek-r1"]

    def __call__(
        self,
        messages: list[dict],
        stream: Optional[bool] = None,
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
            messages (`list[dict]`):
                A list of messages, each containing a 'role' and 'content' key.
            stream (`Optional[bool]`, default `None`):
                Whether to enable stream mode, which will override the
                `stream` argument in the constructor if provided.
            **kwargs (`Any`):
                The keyword arguments to OpenAI chat completions API,
                e.g. `temperature`, `max_tokens`, `top_p`, etc. Please refer to
                https://platform.openai.com/docs/api-reference/chat/create
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                The response text in text field, and the raw response in
                raw field.
        """
        # Merge generation arguments
        kwargs = {**self.generate_args, **kwargs}

        # Validate message format
        if not isinstance(messages, list):
            raise ValueError(
                "DeepSeek `messages` field expected type `list`, "
                f"got `{type(messages)}` instead.",
            )
        if not all("role" in msg and "content" in msg for msg in messages):
            raise ValueError(
                "Each message must contain 'role' and 'content' keys",
            )

        # Configure streaming
        stream = stream if stream is not None else self.stream
        kwargs.update(
            {"model": self.model_name, "messages": messages, "stream": stream},
        )
        if stream:
            kwargs["stream_options"] = {"include_usage": True}
        # Make API call
        raw_response = self.client.chat.completions.create(**kwargs)

        # Process response
        if stream:
            return self._handle_stream_response(raw_response, kwargs)
        else:
            return self._handle_normal_response(raw_response, kwargs)

    def _handle_normal_response(
        self,
        raw_response: ChatCompletion,
        kwargs: dict,
    ) -> ModelResponse:
        """Handle the non-streaming response from the DeepSeek API."""
        response = raw_response.model_dump()
        self._save_model_invocation_and_update_monitor(kwargs, response)
        if _verify_text_content_in_openai_message_response(response):
            text = response["choices"][0]["message"]["content"]
            if self.is_reasoner:
                if _verify_reasoning_content_in_openai_message_response(
                    response,
                ):
                    reasoning_content = response["choices"][0]["message"][
                        "reasoning_content"
                    ]
                    text = (
                        f"Reasoning:\n{reasoning_content}\n\n"
                        f"Answer:\n{text}"
                    )
                else:
                    logger.warning("No reasoning content in the response.")
            return ModelResponse(text=text, raw=response)

        else:
            raise RuntimeError(
                f"Invalid response from DeepSeek API: {response}",
            )

    def _handle_stream_response(
        self,
        raw_response: Stream[ChatCompletionChunk],
        kwargs: dict,
    ) -> ModelResponse:
        """Handle the streaming response from the DeepSeek API."""

        def generator() -> Generator[str, None, None]:
            reasoning_content = ""
            answer_content = ""
            is_first_text = True

            yield "Reasoning:\n"

            for raw_chunk in raw_response:
                chunk = raw_chunk.model_dump()

                if _verify_text_content_in_openai_delta_response(chunk):
                    content = chunk["choices"][0]["delta"]["content"]
                    if is_first_text:
                        is_first_text = False
                        # Instead of yielding two separate times, combine them
                        yield reasoning_content + "\n\nAnswer:\n" + content
                        answer_content = content
                    else:
                        # Normal content accumulation
                        answer_content += content
                        yield (
                            reasoning_content
                            + "\n\nAnswer:\n"
                            + answer_content
                        )

                elif _verify_reasoning_content_in_openai_delta_response(chunk):
                    current = chunk["choices"][0]["delta"]["reasoning_content"]
                    reasoning_content += current
                    yield reasoning_content

                # Handle end of stream
                if chunk.get("choices", []) == [None, []]:
                    chunk["choices"] = [{}]
                    chunk["choices"][0]["message"] = {
                        "role": "assistant",
                        "content": answer_content,
                        "reasoning_content": reasoning_content,
                    }
                    self._save_model_invocation_and_update_monitor(
                        kwargs,
                        chunk,
                    )
                    continue

        return ModelResponse(stream=generator())

    def format(self, *args: Union[Msg, Sequence[Msg]]) -> List[dict]:
        return ModelWrapperBase.format_for_common_chat_models(*args)

    def _save_model_invocation_and_update_monitor(
        self,
        kwargs: dict,
        response: dict,
    ) -> None:
        """Save model invocation and update the monitor accordingly.

        Args:
            kwargs (`dict`):
                The keyword arguments used in model invocation
            response (`dict`):
                The response from model API
        """
        self._save_model_invocation(
            arguments=kwargs,
            response=response,
        )
        usage = response.get("usage", None)
        if usage is not None:
            self.monitor.update_text_and_embedding_tokens(
                model_name=self.model_name,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )
