# -*- coding: utf-8 -*-
"""Model wrapper for OpenAI models"""
from abc import ABC
from typing import Union, Any, List, Sequence, Dict

from loguru import logger

from .model import ModelWrapperBase, ModelResponse
from ..file_manager import file_manager
from ..message import MessageBase
from ..utils.tools import _convert_to_str, _to_openai_image_url

try:
    import openai
except ImportError:
    openai = None

from ..utils.token_utils import get_openai_max_length
from ..constants import _DEFAULT_API_BUDGET


class OpenAIWrapperBase(ModelWrapperBase, ABC):
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

        super().__init__(config_name=config_name)

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
        self._register_budget(model_name, budget)
        self._register_default_metrics()

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> Union[List[dict], str]:
        raise RuntimeError(
            f"Model Wrapper [{type(self).__name__}] doesn't "
            f"need to format the input. Please try to use the "
            f"model wrapper directly.",
        )


class OpenAIChatWrapper(OpenAIWrapperBase):
    """The model wrapper for OpenAI's chat API."""

    model_type: str = "openai_chat"

    deprecated_model_type: str = "openai"

    substrings_in_vision_models_names = ["gpt-4-turbo", "vision", "gpt-4o"]
    """The substrings in the model names of vision models."""

    def _register_default_metrics(self) -> None:
        # Set monitor accordingly
        # TODO: set quota to the following metrics
        self.monitor.register(
            self._metric("call_counter"),
            metric_unit="times",
        )
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
        self.update_monitor(call_counter=1, **response.usage.model_dump())

        # step6: return response
        return ModelResponse(
            text=response.choices[0].message.content,
            raw=response.model_dump(),
        )

    def _format_msg_with_url(
        self,
        msg: MessageBase,
    ) -> Dict:
        """Format a message with image urls into openai chat format.
        This format method is used for gpt-4o, gpt-4-turbo, gpt-4-vision and
        other vision models.
        """
        # Check if the model is a vision model
        if not any(
            _ in self.model_name
            for _ in self.substrings_in_vision_models_names
        ):
            logger.warning(
                f"The model {self.model_name} is not a vision model. "
                f"Skip the url in the message.",
            )
            return {
                "role": msg.role,
                "name": msg.name,
                "content": _convert_to_str(msg.content),
            }

        # Put all urls into a list
        urls = [msg.url] if isinstance(msg.url, str) else msg.url

        # Check if the url refers to an image
        checked_urls = []
        for url in urls:
            try:
                checked_urls.append(_to_openai_image_url(url))
            except TypeError:
                logger.warning(
                    f"The url {url} is not a valid image url for "
                    f"OpenAI Chat API, skipped.",
                )

        if len(checked_urls) == 0:
            # If no valid image url is provided, return the normal message dict
            return {
                "role": msg.role,
                "name": msg.name,
                "content": _convert_to_str(msg.content),
            }
        else:
            # otherwise, use the vision format message
            returned_msg = {
                "role": msg.role,
                "name": msg.name,
                "content": [
                    {
                        "type": "text",
                        "text": _convert_to_str(msg.content),
                    },
                ],
            }

            image_dicts = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": _,
                    },
                }
                for _ in checked_urls
            ]

            returned_msg["content"].extend(image_dicts)

            return returned_msg

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> List[dict]:
        """Format the input string and dictionary into the format that
        OpenAI Chat API required.

        Args:
            args (`Union[MessageBase, Sequence[MessageBase]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `List[dict]`:
                The formatted messages in the format that OpenAI Chat API
                required.
        """
        messages = []
        for arg in args:
            if arg is None:
                continue
            if isinstance(arg, MessageBase):
                if arg.url is not None:
                    messages.append(self._format_msg_with_url(arg))
                else:
                    messages.append(
                        {
                            "role": arg.role,
                            "name": arg.name,
                            "content": _convert_to_str(arg.content),
                        },
                    )

            elif isinstance(arg, list):
                messages.extend(self.format(*arg))
            else:
                raise TypeError(
                    f"The input should be a Msg object or a list "
                    f"of Msg objects, got {type(arg)}.",
                )

        return messages


class OpenAIDALLEWrapper(OpenAIWrapperBase):
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
        self.monitor.register(
            self._metric("call_counter"),
            metric_unit="times",
        )
        for resolution in self._resolutions:
            self.monitor.register(
                self._metric(resolution),
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

        # step4: update monitor accordingly
        self.update_monitor(call_counter=1)

        # step5: return response
        raw_response = response.model_dump()
        if "data" not in raw_response:
            if "error" in raw_response:
                error_msg = raw_response["error"]["message"]
            else:
                error_msg = raw_response
            logger.error(f"Error in OpenAI API call:\n{error_msg}")
            raise ValueError(f"Error in OpenAI API call:\n{error_msg}")
        images = raw_response["data"]
        # Get image urls as a list
        urls = [_["url"] for _ in images]

        if save_local:
            # Return local url if save_local is True
            urls = [file_manager.save_image(_) for _ in urls]
        return ModelResponse(image_urls=urls, raw=raw_response)


class OpenAIEmbeddingWrapper(OpenAIWrapperBase):
    """The model wrapper for OpenAI embedding API."""

    model_type: str = "openai_embedding"

    def _register_default_metrics(self) -> None:
        # Set monitor accordingly
        # TODO: set quota to the following metrics
        self.monitor.register(
            self._metric("call_counter"),
            metric_unit="times",
        )
        self.monitor.register(
            self._metric("prompt_tokens"),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("total_tokens"),
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

        # step4: update monitor accordingly
        self.update_monitor(call_counter=1, **response.usage.model_dump())

        # step5: return response
        response_json = response.model_dump()
        return ModelResponse(
            embedding=[_["embedding"] for _ in response_json["data"]],
            raw=response_json,
        )
