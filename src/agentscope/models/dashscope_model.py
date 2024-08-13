# -*- coding: utf-8 -*-
"""Model wrapper for DashScope models"""
import os
from abc import ABC
from http import HTTPStatus
from typing import Any, Union, List, Sequence, Optional, Generator

from dashscope.api_entities.dashscope_response import GenerationResponse
from loguru import logger

from ..manager import FileManager
from ..message import Msg
from ..utils.tools import _convert_to_str, _guess_type_by_extension

try:
    import dashscope
except ImportError:
    dashscope = None

from .model import ModelWrapperBase, ModelResponse


class DashScopeWrapperBase(ModelWrapperBase, ABC):
    """The model wrapper for DashScope API."""

    def __init__(
        self,
        config_name: str,
        model_name: str = None,
        api_key: str = None,
        generate_args: dict = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the DashScope wrapper.

        Args:
            config_name (`str`):
                The name of the model config.
            model_name (`str`, default `None`):
                The name of the model to use in DashScope API.
            api_key (`str`, default `None`):
                The API key for DashScope API.
            generate_args (`dict`, default `None`):
                The extra keyword arguments used in DashScope api generation,
                e.g. `temperature`, `seed`.
        """
        if model_name is None:
            model_name = config_name
            logger.warning("model_name is not set, use config_name instead.")

        super().__init__(config_name=config_name, model_name=model_name)

        if dashscope is None:
            raise ImportError(
                "Cannot find dashscope package in current python environment.",
            )

        self.generate_args = generate_args or {}

        self.api_key = api_key
        if self.api_key:
            dashscope.api_key = self.api_key
        self.max_length = None

    def format(
        self,
        *args: Union[Msg, Sequence[Msg]],
    ) -> Union[List[dict], str]:
        raise RuntimeError(
            f"Model Wrapper [{type(self).__name__}] doesn't "
            f"need to format the input. Please try to use the "
            f"model wrapper directly.",
        )


class DashScopeChatWrapper(DashScopeWrapperBase):
    """The model wrapper for DashScope's chat API, refer to
    https://help.aliyun.com/zh/dashscope/developer-reference/api-details

    Response:
        - Refer to
        https://help.aliyun.com/zh/dashscope/developer-reference/quick-start?spm=a2c4g.11186623.0.0.7e346eb5RvirBw

        ```json
        {
            "status_code": 200,
            "request_id": "a75a1b22-e512-957d-891b-37db858ae738",
            "code": "",
            "message": "",
            "output": {
                "text": null,
                "finish_reason": null,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "xxx"
                        }
                    }
                ]
            },
            "usage": {
                "input_tokens": 25,
                "output_tokens": 77,
                "total_tokens": 102
            }
        }
        ```
    """

    model_type: str = "dashscope_chat"

    deprecated_model_type: str = "tongyi_chat"

    def __init__(
        self,
        config_name: str,
        model_name: str = None,
        api_key: str = None,
        stream: bool = False,
        generate_args: dict = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the DashScope wrapper.

        Args:
            config_name (`str`):
                The name of the model config.
            model_name (`str`, default `None`):
                The name of the model to use in DashScope API.
            api_key (`str`, default `None`):
                The API key for DashScope API.
            stream (`bool`, default `False`):
                If True, the response will be a generator in the `stream`
                field of the returned `ModelResponse` object.
            generate_args (`dict`, default `None`):
                The extra keyword arguments used in DashScope api generation,
                e.g. `temperature`, `seed`.
        """

        super().__init__(
            config_name=config_name,
            model_name=model_name,
            api_key=api_key,
            generate_args=generate_args,
            **kwargs,
        )

        self.stream = stream

    def __call__(
        self,
        messages: list,
        stream: Optional[bool] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Processes a list of messages to construct a payload for the
        DashScope API call. It then makes a request to the DashScope API
        and returns the response. This method also updates monitoring
        metrics based on the API response.

        Each message in the 'messages' list can contain text content and
        optionally an 'image_urls' key. If 'image_urls' is provided,
        it is expected to be a list of strings representing URLs to images.
        These URLs will be transformed to a suitable format for the DashScope
        API, which might involve converting local file paths to data URIs.

        Args:
            messages (`list`):
                A list of messages to process.
            stream (`Optional[bool]`, default `None`):
                The stream flag to control the response format, which will
                overwrite the stream flag in the constructor.
            **kwargs (`Any`):
                The keyword arguments to DashScope chat completions API,
                e.g. `temperature`, `max_tokens`, `top_p`, etc. Please
                refer to
                https://help.aliyun.com/zh/dashscope/developer-reference/api-details
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                A response object with the response text in text field, and
                the raw response in raw field. If stream is True, the response
                will be a generator in the `stream` field.

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
            The rule of roles in messages for DashScope is very rigid,
            for more details, please refer to
            https://help.aliyun.com/zh/dashscope/developer-reference/api-details
        """

        # step1: prepare keyword arguments
        kwargs = {**self.generate_args, **kwargs}

        # step2: checking messages
        if not isinstance(messages, list):
            raise ValueError(
                "Dashscope `messages` field expected type `list`, "
                f"got `{type(messages)}` instead.",
            )
        if not all("role" in msg and "content" in msg for msg in messages):
            raise ValueError(
                "Each message in the 'messages' list must contain a 'role' "
                "and 'content' key for DashScope API.",
            )

        # step3: forward to generate response
        if stream is None:
            stream = self.stream

        kwargs.update(
            {
                "model": self.model_name,
                "messages": messages,
                # Set the result to be "message" format.
                "result_format": "message",
                "stream": stream,
            },
        )

        # Switch to the incremental_output mode
        if stream:
            kwargs["incremental_output"] = True

        response = dashscope.Generation.call(**kwargs)

        # step3: invoke llm api, record the invocation and update the monitor
        if stream:

            def generator() -> Generator[str, None, None]:
                last_chunk = None
                text = ""
                for chunk in response:
                    if chunk.status_code != HTTPStatus.OK:
                        error_msg = (
                            f"Request id: {chunk.request_id}\n"
                            f"Status code: {chunk.status_code}\n"
                            f"Error code: {chunk.code}\n"
                            f"Error message: {chunk.message}"
                        )
                        raise RuntimeError(error_msg)

                    text += chunk.output["choices"][0]["message"]["content"]
                    yield text
                    last_chunk = chunk

                # Replace the last chunk with the full text
                last_chunk.output["choices"][0]["message"]["content"] = text

                # Save the model invocation and update the monitor
                self._save_model_invocation_and_update_monitor(
                    kwargs,
                    last_chunk,
                )

            return ModelResponse(
                stream=generator(),
                raw=response,
            )

        else:
            if response.status_code != HTTPStatus.OK:
                error_msg = (
                    f"Request id: {response.request_id},\n"
                    f"Status code: {response.status_code},\n"
                    f"Error code: {response.code},\n"
                    f"Error message: {response.message}."
                )

                raise RuntimeError(error_msg)

            # Record the model invocation and update the monitor
            self._save_model_invocation_and_update_monitor(
                kwargs,
                response,
            )

            return ModelResponse(
                text=response.output["choices"][0]["message"]["content"],
                raw=response,
            )

    def _save_model_invocation_and_update_monitor(
        self,
        kwargs: dict,
        response: GenerationResponse,
    ) -> None:
        """Save the model invocation and update the monitor accordingly.

        Args:
            kwargs (`dict`):
                The keyword arguments to the DashScope chat API.
            response (`GenerationResponse`):
                The response object returned by the DashScope chat API.
        """
        input_tokens = response.usage.get("input_tokens", 0)
        output_tokens = response.usage.get("output_tokens", 0)

        # Update the token record accordingly
        self.monitor.update_text_and_embedding_tokens(
            model_name=self.model_name,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
        )

        # Save the model invocation after the stream is exhausted
        self._save_model_invocation(
            arguments=kwargs,
            response=response,
        )

    def format(
        self,
        *args: Union[Msg, Sequence[Msg]],
    ) -> List[dict]:
        """A common format strategy for chat models, which will format the
        input messages into a user message.

        Note this strategy maybe not suitable for all scenarios,
        and developers are encouraged to implement their own prompt
        engineering strategies.

        The following is an example:

        .. code-block:: python

            prompt1 = model.format(
                Msg("system", "You're a helpful assistant", role="system"),
                Msg("Bob", "Hi, how can I help you?", role="assistant"),
                Msg("user", "What's the date today?", role="user")
            )

            prompt2 = model.format(
                Msg("Bob", "Hi, how can I help you?", role="assistant"),
                Msg("user", "What's the date today?", role="user")
            )

        The prompt will be as follows:

        .. code-block:: python

            # prompt1
            [
                {
                    "role": "user",
                    "content": (
                        "You're a helpful assistant\\n"
                        "\\n"
                        "## Conversation History\\n"
                        "Bob: Hi, how can I help you?\\n"
                        "user: What's the date today?"
                    )
                }
            ]

            # prompt2
            [
                {
                    "role": "user",
                    "content": (
                        "## Conversation History\\n"
                        "Bob: Hi, how can I help you?\\n"
                        "user: What's the date today?"
                    )
                }
            ]


        Args:
            args (`Union[Msg, Sequence[Msg]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `List[dict]`:
                The formatted messages.
        """

        return ModelWrapperBase.format_for_common_chat_models(*args)


class DashScopeImageSynthesisWrapper(DashScopeWrapperBase):
    """The model wrapper for DashScope Image Synthesis API, refer to
    https://help.aliyun.com/zh/dashscope/developer-reference/quick-start-1

    Response:
        - Refer to
        https://help.aliyun.com/zh/dashscope/developer-reference/api-details-9?spm=a2c4g.11186623.0.0.7108fa70Op6eqF

        ```json
        {
            "status_code": 200,
            "request_id": "b54ffeb8-6212-9dac-808c-b3771cba3788",
            "code": null,
            "message": "",
            "output": {
                "task_id": "996523eb-034d-459b-ac88-b340b95007a4",
                "task_status": "SUCCEEDED",
                "results": [
                    {
                        "url": "RESULT_URL1"
                    },
                    {
                        "url": "RESULT_URL2"
                    },
                ],
                "task_metrics": {
                    "TOTAL": 2,
                    "SUCCEEDED": 2,
                    "FAILED": 0
                }
            },
            "usage": {
                "image_count": 2
            }
        }
        ```
    """

    model_type: str = "dashscope_image_synthesis"

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
                 The keyword arguments to DashScope Image Synthesis API,
                 e.g. `n`, `size`, etc. Please refer to
                 https://help.aliyun.com/zh/dashscope/developer-reference/api-details-9
        for more detailed arguments.

         Returns:
             `ModelResponse`:
                 A list of image urls in image_urls field and the
                 raw response in raw field.

         Note:
             `parse_func`, `fault_handler` and `max_retries` are reserved
             for `_response_parse_decorator` to parse and check the
             response generated by model wrapper. Their usages are listed
             as follows:
                 - `parse_func` is a callable function used to parse and
                 check the response generated by the model, which takes
                 the response as input.
                 - `max_retries` is the maximum number of retries when the
                 `parse_func` raise an exception.
                 - `fault_handler` is a callable function which is called
                 when the response generated by the model is invalid after
                 `max_retries` retries.
        """
        # step1: prepare keyword arguments
        kwargs = {**self.generate_args, **kwargs}

        # step2: forward to generate response
        response = dashscope.ImageSynthesis.call(
            model=self.model_name,
            prompt=prompt,
            **kwargs,
        )
        if response.status_code != HTTPStatus.OK:
            error_msg = (
                f" Request id: {response.request_id},"
                f" Status code: {response.status_code},"
                f" error code: {response.code},"
                f" error message: {response.message}."
            )
            raise RuntimeError(error_msg)

        # step3: record the model api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "prompt": prompt,
                **kwargs,
            },
            response=response,
        )

        # step4: update monitor accordingly
        self.monitor.update_image_tokens(
            model_name=self.model_name,
            image_count=response.usage.image_count,
            resolution=kwargs.get("size", "1024*1024"),
        )

        # step5: return response
        images = response.output["results"]
        # Get image urls as a list
        urls = [_["url"] for _ in images]

        if save_local:
            file_manager = FileManager.get_instance()
            # Return local url if save_local is True
            urls = [file_manager.save_image(_) for _ in urls]
        return ModelResponse(image_urls=urls, raw=response)


class DashScopeTextEmbeddingWrapper(DashScopeWrapperBase):
    """The model wrapper for DashScope Text Embedding API.

    Response:
        - Refer to
        https://help.aliyun.com/zh/dashscope/developer-reference/text-embedding-api-details?spm=a2c4g.11186623.0.i3

        ```json
        {
            "status_code": 200, // 200 indicate success otherwise failed.
            "request_id": "fd564688-43f7-9595-b986", // The request id.
            "code": "", // If failed, the error code.
            "message": "", // If failed, the error message.
            "output": {
                "embeddings": [ // embeddings
                    {
                        "embedding": [ // one embedding output
                            -3.8450357913970947, ...,
                        ],
                        "text_index": 0 // the input index.
                    }
                ]
            },
            "usage": {
                "total_tokens": 3 // the request tokens.
            }
        }
        ```
    """

    model_type: str = "dashscope_text_embedding"

    def __call__(
        self,
        texts: Union[list[str], str],
        **kwargs: Any,
    ) -> ModelResponse:
        """Embed the messages with DashScope Text Embedding API.

        Args:
            texts (`list[str]` or `str`):
                The messages used to embed.
            **kwargs (`Any`):
                The keyword arguments to DashScope Text Embedding API,
                e.g. `text_type`. Please refer to
                https://help.aliyun.com/zh/dashscope/developer-reference/api-details-15
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                A list of embeddings in embedding field and the raw
                response in raw field.

        Note:
            `parse_func`, `fault_handler` and `max_retries` are reserved
            for `_response_parse_decorator` to parse and check the response
            generated by model wrapper. Their usages are listed as follows:
                - `parse_func` is a callable function used to parse and
                check the response generated by the model, which takes the
                response as input.
                - `max_retries` is the maximum number of retries when the
                `parse_func` raise an exception.
                - `fault_handler` is a callable function which is called
                when the response generated by the model is invalid after
                `max_retries` retries.
        """
        # step1: prepare keyword arguments
        kwargs = {**self.generate_args, **kwargs}

        # step2: forward to generate response
        response = dashscope.TextEmbedding.call(
            input=texts,
            model=self.model_name,
            **kwargs,
        )

        if response.status_code != HTTPStatus.OK:
            error_msg = (
                f" Request id: {response.request_id},"
                f" Status code: {response.status_code},"
                f" error code: {response.code},"
                f" error message: {response.message}."
            )
            raise RuntimeError(error_msg)

        # step3: record the model api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "input": texts,
                **kwargs,
            },
            response=response,
        )

        # step4: update monitor accordingly
        self.monitor.update_text_and_embedding_tokens(
            model_name=self.model_name,
            prompt_tokens=response.usage.get("total_tokens"),
            total_tokens=response.usage.get("total_tokens"),
        )

        # step5: return response
        return ModelResponse(
            embedding=[_["embedding"] for _ in response.output["embeddings"]],
            raw=response,
        )


class DashScopeMultiModalWrapper(DashScopeWrapperBase):
    """The model wrapper for DashScope Multimodal API, refer to
    https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-vl-api

    Response:
        - Refer to
        https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-vl-plus-api?spm=a2c4g.11186623.0.0.7fde1f5atQSalN

        ```json
        {
            "status_code": 200,
            "request_id": "a0dc436c-2ee7-93e0-9667-c462009dec4d",
            "code": "",
            "message": "",
            "output": {
                "text": null,
                "finish_reason": null,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "text": "这张图片显..."
                                }
                            ]
                        }
                    }
                ]
            },
            "usage": {
                "input_tokens": 1277,
                "output_tokens": 81,
                "image_tokens": 1247
            }
        }
        ```
    """

    model_type: str = "dashscope_multimodal"

    def __call__(
        self,
        messages: list,
        **kwargs: Any,
    ) -> ModelResponse:
        """Model call for DashScope MultiModal API.

        Args:
            messages (`list`):
                A list of messages to process.
            **kwargs (`Any`):
                The keyword arguments to DashScope MultiModal API,
                e.g. `stream`. Please refer to
                https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-vl-plus-api
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                The response text in text field, and the raw response in
                raw field.

        Note:
            If involving image links, then the messages should be of the
            following form:

            .. code-block:: python

                messages = [
                    {
                        "role": "system",
                        "content": [
                            {"text": "You are a helpful assistant."},
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {"text": "What does this picture depict？"},
                            {"image": "http://example.com/image.jpg"},
                        ],
                    },
                ]

            Therefore, you should input a list matching the content value
            above.
            If only involving words, just input them.
        """
        # step1: prepare keyword arguments
        kwargs = {**self.generate_args, **kwargs}

        # step2: forward to generate response
        response = dashscope.MultiModalConversation.call(
            model=self.model_name,
            messages=messages,
            **kwargs,
        )
        # Unhandle code path here
        # response could be a generator , if stream is yes
        # suggest add a check here
        if response.status_code != HTTPStatus.OK:
            error_msg = (
                f" Request id: {response.request_id},"
                f" Status code: {response.status_code},"
                f" error code: {response.code},"
                f" error message: {response.message}."
            )
            raise RuntimeError(error_msg)

        # step3: record the model api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "messages": messages,
                **kwargs,
            },
            response=response,
        )

        # step4: update monitor accordingly
        input_tokens = response.usage.get("input_tokens", 0)
        image_tokens = response.usage.get("image_tokens", 0)
        output_tokens = response.usage.get("output_tokens", 0)
        # TODO: update the tokens
        self.monitor.update_text_and_embedding_tokens(
            model_name=self.model_name,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens + image_tokens,
        )

        # step5: return response
        content = response.output["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = content[0]["text"]

        return ModelResponse(
            text=content,
            raw=response,
        )

    def format(
        self,
        *args: Union[Msg, Sequence[Msg]],
    ) -> List:
        """Format the messages for DashScope Multimodal API.

        The multimodal API has the following requirements:

            - The roles of messages must alternate between "user" and
                "assistant".
            - The message with the role "system" should be the first message
                in the list.
            - If the system message exists, then the second message must
                have the role "user".
            - The last message in the list should have the role "user".
            - In each message, more than one figure is allowed.

        With the above requirements, we format the messages as follows:

            - If the first message is a system message, then we will keep it as
                system prompt.
            - We merge all messages into a conversation history prompt in a
                single message with the role "user".
            - When there are multiple figures in the given messages, we will
                attach it to the user message by order. Note if there are
                multiple figures, this strategy may cause misunderstanding for
                the model. For advanced solutions, developers are encouraged to
                implement their own prompt engineering strategies.

        The following is an example:

        .. code-block:: python

            prompt = model.format(
                Msg(
                    "system",
                    "You're a helpful assistant",
                    role="system", url="figure1"
                ),
                Msg(
                    "Bob",
                    "How about this picture?",
                    role="assistant", url="figure2"
                ),
                Msg(
                    "user",
                    "It's wonderful! How about mine?",
                    role="user", image="figure3"
                )
            )

        The prompt will be as follows:

        .. code-block:: python

            [
                {
                    "role": "system",
                    "content": [
                        {"text": "You are a helpful assistant"},
                        {"image": "figure1"}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"image": "figure2"},
                        {"image": "figure3"},
                        {
                            "text": (
                                "## Conversation History\\n"
                                "Bob: How about this picture?\\n"
                                "user: It's wonderful! How about mine?"
                            )
                        },
                    ]
                }
            ]

        Note:
            In multimodal API, the url of local files should be prefixed with
            "file://", which will be attached in this format function.

        Args:
            args (`Union[Msg, Sequence[Msg]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `List[dict]`:
                The formatted messages.
        """

        # Parse all information into a list of messages
        input_msgs = []
        for _ in args:
            if _ is None:
                continue
            if isinstance(_, Msg):
                input_msgs.append(_)
            elif isinstance(_, list) and all(isinstance(__, Msg) for __ in _):
                input_msgs.extend(_)
            else:
                raise TypeError(
                    f"The input should be a Msg object or a list "
                    f"of Msg objects, got {type(_)}.",
                )

        messages = []

        # record dialog history as a list of strings
        dialogue = []
        image_or_audio_dicts = []
        for i, unit in enumerate(input_msgs):
            if i == 0 and unit.role == "system":
                # system prompt
                content = self.convert_url(unit.url)
                content.append({"text": _convert_to_str(unit.content)})

                messages.append(
                    {
                        "role": unit.role,
                        "content": content,
                    },
                )
            else:
                # text message
                dialogue.append(
                    f"{unit.name}: {_convert_to_str(unit.content)}",
                )
                # image and audio
                image_or_audio_dicts.extend(self.convert_url(unit.url))

        dialogue_history = "\n".join(dialogue)

        user_content_template = "## Conversation History\n{dialogue_history}"

        messages.append(
            {
                "role": "user",
                "content": [
                    # Place the image or audio before the conversation history
                    *image_or_audio_dicts,
                    {
                        "text": user_content_template.format(
                            dialogue_history=dialogue_history,
                        ),
                    },
                ],
            },
        )

        return messages

    def convert_url(self, url: Union[str, Sequence[str], None]) -> List[dict]:
        """Convert the url to the format of DashScope API. Note for local
        files, a prefix "file://" will be added.

        Args:
            url (`Union[str, Sequence[str], None]`):
                A string of url of a list of urls to be converted.

        Returns:
            `List[dict]`:
                A list of dictionaries with key as the type of the url
                and value as the url. Only "image" and "audio" are supported.
        """
        if url is None:
            return []

        if isinstance(url, str):
            url_type = _guess_type_by_extension(url)
            if url_type in ["audio", "image"]:
                # Add prefix for local files
                if os.path.exists(url):
                    url = "file://" + url
                return [{url_type: url}]
            else:
                # skip unsupported url
                logger.warning(
                    f"Skip unsupported url ({url_type}), "
                    f"expect image or audio.",
                )
                return []
        elif isinstance(url, list):
            dicts = []
            for _ in url:
                dicts.extend(self.convert_url(_))
            return dicts
        else:
            raise TypeError(
                f"Unsupported url type {type(url)}, " f"str or list expected.",
            )
