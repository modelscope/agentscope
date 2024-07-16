from abc import ABC
from openai import OpenAI
from .model import ModelWrapperBase, ModelResponse
from typing import Union, Sequence, Any, Dict, List
import logging
from ..message import Msg
logger = logging.getLogger(__name__)

_DEFAULT_API_BUDGET = float("inf")

try:
    import openai
except ImportError:
    openai = None

class YiWrapperBase(ModelWrapperBase, ABC):
    """The model wrapper for Yi API."""

    def __init__(
            self,
            config_name: str,
            model_name: str = None,
            api_key: str = None,
            region: str = "domestic",  # "domestic" or "overseas"
            client_args: dict = None,
            generate_args: dict = None,
            budget: float = _DEFAULT_API_BUDGET,
            **kwargs: Any,
    ) -> None:
        """Initialize the Yi client.

        Args:
            config_name (`str`):
                The name of the model config.
            model_name (`str`, default `None`):
                The name of the model to use in Yi API.
            api_key (`str`, default `None`):
                The API key for Yi API.
            region (`str`, default "domestic"):
                The region for API base URL. Either "domestic" or "overseas".
            client_args (`dict`, default `None`):
                The extra keyword arguments to initialize the Yi client.
            generate_args (`dict`, default `None`):
                The extra keyword arguments used in Yi api generation,
                e.g. `temperature`, `max_tokens`.
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

        base_url = "https://api.lingyiwanwu.com/v1" if region == "domestic" else "https://api.01.ai/v1"
        if base_url:
            self.base_url = base_url
        elif region == "overseas":
            self.base_url = "https://api.01.ai/v1"
        else:
            self.base_url = "https://api.lingyiwanwu.com/v1"

        if region == "overseas" and model_name not in ["yi-large"]:
            logger.warning(
                f"Model {model_name} may not be available for overseas region. Only yi-large is confirmed to work.More information can be found here https://platform.01.ai/docs#models-and-pricing")
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            **(client_args or {}),
        )

        # Set the max length of Yi model (this might need to be adjusted)
        self.max_length = 4096  # Placeholder value, adjust as needed

        # Set monitor accordingly
        self._register_budget(model_name, budget)
        self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        # Set monitor accordingly
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
            *args: Union[Msg, Sequence[Msg]],
    ) -> Union[List[dict], str]:
        raise NotImplementedError(
            f"Model Wrapper [{type(self).__name__}] doesn't "
            f"implement the format method. Please implement it "
            f"in the subclass."
        )


class YiChatWrapper(YiWrapperBase):
    """The model wrapper for Yi's chat API."""

    model_type: str = "yi_chat"

    def __call__(
            self,
            messages: list,
            **kwargs: Any,
    ) -> ModelResponse:
        """Processes a list of messages to construct a payload for the Yi
        API call. It then makes a request to the Yi API and returns the
        response. This method also updates monitoring metrics based on the
        API response.

        Args:
            messages (`list`):
                A list of messages to process.
            **kwargs (`Any`):
                The keyword arguments to Yi chat completions API,
                e.g. `temperature`, `max_tokens`, etc.

        Returns:
            `ModelResponse`:
                The response text in text field, and the raw response in
                raw field.
        """
        # Prepare keyword arguments
        kwargs = {**self.generate_args, **kwargs}

        # Checking messages
        if not isinstance(messages, list):
            raise ValueError(
                "Yi `messages` field expected type `list`, "
                f"got `{type(messages)}` instead.",
            )
        if not all("role" in msg and "content" in msg for msg in messages):
            raise ValueError(
                "Each message in the 'messages' list must contain a 'role' "
                "and 'content' key for Yi API.",
            )

        # Forward to generate response
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs,
        )

        # Record the api invocation if needed
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                "messages": messages,
                **kwargs,
            },
            response=response.model_dump(),
        )

        # Update monitor accordingly
        self.update_monitor(call_counter=1, **response.usage.model_dump())

        # Return response
        return ModelResponse(
            text=response.choices[0].message.content,
            raw=response.model_dump(),
        )

    def format(
            self,
            *args: Union[Msg, Sequence[Msg]],
    ) -> List[dict]:
        """Format the input string and dictionary into the format that
        Yi Chat API required.

        Args:
            args (`Union[Msg, Sequence[Msg]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.

        Returns:
            `List[dict]`:
                The formatted messages in the format that Yi Chat API
                required.
        """
        messages = []
        for arg in args:
            if arg is None:
                continue
            if isinstance(arg, Msg):
                messages.append(
                    {
                        "role": arg.role,
                        "content": str(arg.content),
                    }
                )
            elif isinstance(arg, list):
                messages.extend(self.format(*arg))
            else:
                raise TypeError(
                    f"The input should be a Msg object or a list "
                    f"of Msg objects, got {type(arg)}.",
                )

        return messages