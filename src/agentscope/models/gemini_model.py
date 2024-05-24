# -*- coding: utf-8 -*-
"""Google Gemini model wrapper."""
import os
from abc import ABC
from collections.abc import Iterable
from typing import Sequence, Union, Any, List

from loguru import logger

from agentscope.message import Msg, MessageBase
from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.utils.tools import _convert_to_str

try:
    import google.generativeai as genai

    # This package will be installed when the google-generativeai is installed
    import google.ai.generativelanguage as glm
except ImportError:
    genai = None
    glm = None


class GeminiWrapperBase(ModelWrapperBase, ABC):
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
        super().__init__(config_name=config_name)

        # Test if the required package is installed
        if genai is None:
            raise ImportError(
                "The google-generativeai package is not installed, "
                "please install it first.",
            )

        # Load the api_key from argument or environment variable
        api_key = api_key or os.environ.get("GOOGLE_API_KEY")

        if api_key is None:
            raise ValueError(
                "Google api_key must be provided or set as an "
                "environment variable.",
            )

        genai.configure(api_key=api_key, **kwargs)

        self.model_name = model_name

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

        # step3: Check for candidates and handle accordingly
        if (
            not response.candidates[0].content
            or not response.candidates[0].content.parts
            or not response.candidates[0].content.parts[0].text
        ):
            # If we cannot get the response text from the model
            finish_reason = response.candidates[0].finish_reason
            reasons = glm.Candidate.FinishReason

            if finish_reason == reasons.STOP:
                error_info = (
                    "Natural stop point of the model or provided stop "
                    "sequence."
                )
            elif finish_reason == reasons.MAX_TOKENS:
                error_info = (
                    "The maximum number of tokens as specified in the request "
                    "was reached."
                )
            elif finish_reason == reasons.SAFETY:
                error_info = (
                    "The candidate content was flagged for safety reasons."
                )
            elif finish_reason == reasons.RECITATION:
                error_info = (
                    "The candidate content was flagged for recitation reasons."
                )
            elif finish_reason in [
                reasons.FINISH_REASON_UNSPECIFIED,
                reasons.OTHER,
            ]:
                error_info = "Unknown error."
            else:
                error_info = "No information provided from Gemini API."

            raise ValueError(
                "The Google Gemini API failed to generate text response with "
                f"the following finish reason: {error_info}\n"
                f"YOUR INPUT: {contents}\n"
                f"RAW RESPONSE FROM GEMINI API: {response}\n",
            )

        # step4: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "contents": contents,
                "stream": stream,
                **kwargs,
            },
            response=str(response),
        )

        # step5: update monitor accordingly
        token_prompt = self.model.count_tokens(contents).total_tokens
        token_response = self.model.count_tokens(response.text).total_tokens
        self.update_monitor(
            call_counter=1,
            completion_tokens=token_response,
            prompt_tokens=token_prompt,
            total_tokens=token_prompt + token_response,
        )

        # step6: return response
        return ModelResponse(
            text=response.text,
            raw=response,
        )

    def _register_default_metrics(self) -> None:
        """Register the default metrics for the model."""
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

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> List[dict]:
        """This function provide a basic prompting strategy for Gemini Chat
        API in multi-party conversation, which combines all input into a
        single string, and wrap it into a user message.

        We make the above decision based on the following constraints of the
        Gemini generate API:

        1. In Gemini `generate_content` API, the `role` field must be either
        `user` or `model`.

        2. If we pass a list of messages to the `generate_content` API,
        the `user` role must speak in the beginning and end of the
        messages, and `user` and `model` must alternative. This prevents
        us to build a multi-party conversations, where `model` may keep
        speaking in different names.

        The above information is updated to 2024/03/21. More information
        about the Gemini `generate_content` API can be found in
        https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini

        Based on the above considerations, we decide to combine all messages
        into a single user message. This is a simple and straightforward
        strategy, if you have any better ideas, pull request and
        discussion are welcome in our GitHub repository
        https://github.com/agentscope/agentscope!

        Args:
            args (`Union[MessageBase, Sequence[MessageBase]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `List[dict]`:
                A list with one user message.
        """
        input_msgs = []
        for _ in args:
            if _ is None:
                continue
            if isinstance(_, MessageBase):
                input_msgs.append(_)
            elif isinstance(_, list) and all(
                isinstance(__, MessageBase) for __ in _
            ):
                input_msgs.extend(_)
            else:
                raise TypeError(
                    f"The input should be a Msg object or a list "
                    f"of Msg objects, got {type(_)}.",
                )

        # record dialog history as a list of strings
        sys_prompt = None
        dialogue = []
        for i, unit in enumerate(input_msgs):
            if i == 0 and unit.role == "system":
                # system prompt
                sys_prompt = _convert_to_str(unit.content)
            else:
                # Merge all messages into a dialogue history prompt
                dialogue.append(
                    f"{unit.name}: {_convert_to_str(unit.content)}",
                )

        dialogue_history = "\n".join(dialogue)

        if sys_prompt is None:
            user_content_template = "## Dialogue History\n{dialogue_history}"
        else:
            user_content_template = (
                "{sys_prompt}\n"
                "\n"
                "## Dialogue History\n"
                "{dialogue_history}"
            )

        messages = [
            {
                "role": "user",
                "parts": [
                    user_content_template.format(
                        sys_prompt=sys_prompt,
                        dialogue_history=dialogue_history,
                    ),
                ],
            },
        ]

        return messages


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
        # step3: update monitor accordingly
        self.update_monitor(call_counter=1)

        return ModelResponse(
            raw=response,
            embedding=response["embedding"],
        )

    def _register_default_metrics(self) -> None:
        """Register the default metrics for the model."""
        self.monitor.register(
            self._metric("call_counter"),
            metric_unit="times",
        )
