# -*- coding: utf-8 -*-
"""Model wrapper based on litellm https://docs.litellm.ai/docs/"""
from abc import ABC
from typing import Union, Any, List, Sequence
import os

from loguru import logger

from .model import ModelWrapperBase, ModelResponse
from ..message import MessageBase
from ..utils.tools import _convert_to_str

try:
    import litellm
except ImportError:
    litellm = None


class LiteLLMWrapperBase(ModelWrapperBase, ABC):
    """The model wrapper based on LiteLLM API."""

    def __init__(
        self,
        config_name: str,
        model_name: str = None,
        api_key: str = None,
        api_key_name: str = None,
        generate_args: dict = None,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            config_name (`str`):
                The name of the model config.
            model_name (`str`, default `None`):
                The name of the model to use in OpenAI API.
            api_key (`str`, default `None`):
                The API key used.
            api_key_name (`str`, default `None`):
                The API key name used, related to the model_name.
            generate_args (`dict`, default `None`):
                The extra keyword arguments used in litellm api generation,
                e.g. `temperature`, `seed`.

        """

        if model_name is None:
            model_name = config_name
            logger.warning("model_name is not set, use config_name instead.")

        super().__init__(config_name=config_name)

        if litellm is None:
            raise ImportError(
                "Cannot find litellm package in current python environment.",
            )

        self.model_name = model_name
        self.generate_args = generate_args or {}
        self.api_key = api_key
        self.api_key_name = api_key_name
        if api_key is not None and api_key_name is not None:
            os.environ[api_key_name] = api_key
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


class LiteLLMChatWrapper(LiteLLMWrapperBase):
    """The model wrapper based on litellm chat API."""

    model_type: str = "litellm_chat"

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
        """
        Args:
            messages (`list`):
                A list of messages to process.
            **kwargs (`Any`):
                The keyword arguments to litellm chat completions API,
                e.g. `temperature`, `max_tokens`, `top_p`, etc. Please refer to
                https://docs.litellm.ai/docs/completion/input
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                The response text in text field, and the raw response in
                raw field.
        """

        # step1: prepare keyword arguments
        kwargs = {**self.generate_args, **kwargs}

        # step2: checking messages
        if not isinstance(messages, list):
            raise ValueError(
                "LiteLLM `messages` field expected type `list`, "
                f"got `{type(messages)}` instead.",
            )
        if not all("role" in msg and "content" in msg for msg in messages):
            raise ValueError(
                "Each message in the 'messages' list must contain a 'role' "
                "and 'content' key for LiteLLM API.",
            )

        # step3: forward to generate response
        response = litellm.completion(
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

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> List[dict]:
        """Format the input string and dictionary into the unified format.
        Note that the format function might not be the optimal way to contruct
        prompt for every model, but a common way to do so.
        Developers are encouraged to implement their own prompt
        engineering strategies if have strong performance concerns.

        Args:
            args (`Union[MessageBase, Sequence[MessageBase]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.
        Returns:
            `List[dict]`:
                The formatted messages in the format that anthropic Chat API
                required.
        """

        # Parse all information into a list of messages
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
                "content": user_content_template.format(
                    sys_prompt=sys_prompt,
                    dialogue_history=dialogue_history,
                ),
            },
        ]

        return messages
