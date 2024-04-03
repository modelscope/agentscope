# -*- coding: utf-8 -*-
"""Model wrapper for Ollama models."""
from abc import ABC
from typing import Sequence, Any, Optional, List, Union

from loguru import logger

from agentscope.message import MessageBase
from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.utils.tools import _convert_to_str

try:
    import ollama
except ImportError:
    ollama = None


class OllamaWrapperBase(ModelWrapperBase, ABC):
    """The base class for Ollama model wrappers.

    To use Ollama API, please
    1. First install ollama server from https://ollama.com/download and
    start the server
    2. Pull the model by `ollama pull {model_name}` in terminal
    After that, you can use the ollama API.
    """

    model_type: str
    """The type of the model wrapper, which is to identify the model wrapper
    class in model configuration."""

    model_name: str
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
        model_name: str,
        options: dict = None,
        keep_alive: str = "5m",
    ) -> None:
        """Initialize the model wrapper for Ollama API.

        Args:
            model_name (`str`):
                The model name used in ollama API.
            options (`dict`, default `None`):
                The extra keyword arguments used in Ollama api generation,
                e.g. `{"temperature": 0., "seed": 123}`.
            keep_alive (`str`, default `5m`):
                Controls how long the model will stay loaded into memory
                following the request.
        """

        super().__init__(config_name=config_name)

        self.model_name = model_name
        self.options = options
        self.keep_alive = keep_alive

        self._register_default_metrics()


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
            model=self.model_name,
            messages=messages,
            options=options,
            keep_alive=keep_alive,
            **kwargs,
        )

        # step2: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "messages": messages,
                "options": options,
                "keep_alive": keep_alive,
                **kwargs,
            },
            response=response,
        )

        # step3: monitor the response
        self.update_monitor(
            call_counter=1,
            prompt_tokens=response["prompt_eval_count"],
            completion_tokens=response["eval_count"],
            total_tokens=response["prompt_eval_count"]
            + response["eval_count"],
        )

        # step4: return response
        return ModelResponse(
            text=response["message"]["content"],
            raw=response,
        )

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        self.monitor.register(
            self._metric("call_counter"),
            metric_unit="times",
        )
        self.monitor.register(
            self._metric("prompt_tokens"),
            metric_unit="tokens",
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
        """A basic strategy to format the input into the required format of
        Ollama Chat API.

        Note for ollama chat api, the content field shouldn't be empty string.

        Args:
            args (`Union[MessageBase, Sequence[MessageBase]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `List[dict]`:
                The formatted messages.
        """
        ollama_msgs = []
        for msg in args:
            if msg is None:
                continue
            if isinstance(msg, MessageBase):
                # content shouldn't be empty string
                if msg.content == "":
                    logger.warning(
                        "In ollama chat API, the content field cannot be "
                        "empty string. To avoid error, the empty string is "
                        "replaced by a blank space automatically, but the "
                        "model may not work as expected.",
                    )
                    msg.content = " "

                ollama_msg = {
                    "role": msg.role,
                    "content": _convert_to_str(msg.content),
                }

                # image url
                if msg.url is not None:
                    ollama_msg["images"] = [msg.url]

                ollama_msgs.append(ollama_msg)
            elif isinstance(msg, list):
                ollama_msgs.extend(self.format(*msg))
            else:
                raise TypeError(
                    f"Invalid message type: {type(msg)}, `Msg` is expected.",
                )

        return ollama_msgs


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
            model=self.model_name,
            prompt=prompt,
            options=options,
            keep_alive=keep_alive,
            **kwargs,
        )

        # step3: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "prompt": prompt,
                "options": options,
                "keep_alive": keep_alive,
                **kwargs,
            },
            response=response,
        )

        # step4: monitor the response
        self.update_monitor(call_counter=1)

        # step5: return response
        return ModelResponse(
            embedding=response["embedding"],
            raw=response,
        )

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        self.monitor.register(
            self._metric("call_counter"),
            metric_unit="times",
        )

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> Union[List[dict], str]:
        raise RuntimeError(
            f"Model Wrapper [{type(self).__name__}] doesn't "
            f"need to format the input. Please try to use the "
            f"model wrapper directly.",
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
            model=self.model_name,
            prompt=prompt,
            options=options,
            keep_alive=keep_alive,
        )

        # step3: record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "prompt": prompt,
                "options": options,
                "keep_alive": keep_alive,
                **kwargs,
            },
            response=response,
        )

        # step4: monitor the response
        self.update_monitor(
            call_counter=1,
            prompt_tokens=response["prompt_eval_count"],
            completion_tokens=response["eval_count"],
            total_tokens=response["prompt_eval_count"]
            + response["eval_count"],
        )

        # step5: return response
        return ModelResponse(
            text=response["response"],
            raw=response,
        )

    def _register_default_metrics(self) -> None:
        """Register metrics to the monitor."""
        self.monitor.register(
            self._metric("call_counter"),
            metric_unit="times",
        )
        self.monitor.register(
            self._metric("prompt_tokens"),
            metric_unit="tokens",
        )
        self.monitor.register(
            self._metric("completion_tokens"),
            metric_unit="token",
        )
        self.monitor.register(
            self._metric("total_tokens"),
            metric_unit="token",
        )

    def format(self, *args: Union[MessageBase, Sequence[MessageBase]]) -> str:
        """Forward the input to the model.

        Args:
            args (`Union[MessageBase, Sequence[MessageBase]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `str`:
                The formatted string prompt.
        """
        input_msgs = []
        for _ in args:
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
            prompt_template = "## Dialogue History\n{dialogue_history}"
        else:
            prompt_template = (
                "{system_prompt}\n"
                "\n"
                "## Dialogue History\n"
                "{dialogue_history}"
            )

        return prompt_template.format(
            system_prompt=sys_prompt,
            dialogue_history=dialogue_history,
        )
