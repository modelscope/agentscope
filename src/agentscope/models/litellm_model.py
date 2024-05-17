# -*- coding: utf-8 -*-
"""Model wrapper based on litellm https://docs.litellm.ai/docs/"""
from abc import ABC
from typing import Union, Any, List, Sequence

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
        generate_args: dict = None,
        **kwargs: Any,
    ) -> None:
        """
        To use the LiteLLM wrapper, environent variables must be set.
        Different model_name could be using different environment variables.
        For example:
            - for model_name: "gpt-3.5-turbo", you need to set "OPENAI_API_KEY"
            ```
            os.environ["OPENAI_API_KEY"] = "your-api-key"
            ```
            - for model_name: "claude-2", you need to set "ANTHROPIC_API_KEY"
            - for Azure OpenAI, you need to set "AZURE_API_KEY",
            "AZURE_API_BASE", "AZURE_API_VERSION"
        You should refer to the docs in https://docs.litellm.ai/docs/ .
        Args:
            config_name (`str`):
                The name of the model config.
            model_name (`str`, default `None`):
                The name of the model to use in OpenAI API.
            generate_args (`dict`, default `None`):
                The extra keyword arguments used in litellm api generation,
                e.g. `temperature`, `seed`.
                For generate_args, please refer to
                https://docs.litellm.ai/docs/completion/input
                for more detailes.

        """

        if model_name is None:
            model_name = config_name
            logger.warning("model_name is not set, use config_name instead.")

        super().__init__(config_name=config_name)

        if litellm is None:
            raise ImportError(
                "Cannot import litellm package in current python environment."
                "You should try:"
                "1. Install litellm by `pip install litellm`"
                "2. If you still have import error, you should try to "
                "update the openai to higher version, e.g. "
                "by runing `pip install openai==1.25.1",
            )

        self.model_name = model_name
        self.generate_args = generate_args or {}
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
    """The model wrapper based on litellm chat API.
    To use the LiteLLM wrapper, environent variables must be set.
    Different model_name could be using different environment variables.
    For example:
        - for model_name: "gpt-3.5-turbo", you need to set "OPENAI_API_KEY"
        ```
        os.environ["OPENAI_API_KEY"] = "your-api-key"
        ```
        - for model_name: "claude-2", you need to set "ANTHROPIC_API_KEY"
        - for Azure OpenAI, you need to set "AZURE_API_KEY",
        "AZURE_API_BASE", "AZURE_API_VERSION"
    You should refer to the docs in https://docs.litellm.ai/docs/ .
    """

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
        system_content_template = []
        dialogue = []
        for i, unit in enumerate(input_msgs):
            if i == 0 and unit.role == "system":
                # system prompt
                system_prompt = _convert_to_str(unit.content)
                if not system_prompt.endswith("\n"):
                    system_prompt += "\n"
                system_content_template.append(system_prompt)
            else:
                # Merge all messages into a dialogue history prompt
                dialogue.append(
                    f"{unit.name}: {_convert_to_str(unit.content)}",
                )

        if len(dialogue) != 0:
            dialogue_history = "\n".join(dialogue)

            system_content_template.extend(
                ["## Dialogue History", dialogue_history],
            )

        system_content = "\n".join(system_content_template)

        messages = [
            {
                "role": "user",
                "content": system_content,
            },
        ]

        return messages
