# -*- coding: utf-8 -*-
"""Model wrapper for stable diffusion models."""
from abc import ABC
import base64
from typing import Any, Optional, Union, List, Sequence

from . import ModelWrapperBase, ModelResponse
from ..message import Msg
from ..manager import FileManager
import requests
from ..utils.common import _convert_to_str


class StableDiffusionWrapperBase(ModelWrapperBase, ABC):
    """The base class for stable-diffusion model wrappers.

    To use SD API, please
    1. First download stable-diffusion-webui from https://github.com/AUTOMATIC1111/stable-diffusion-webui and
    install it with 'webui-user.bat'
    2. Move your checkpoint to 'models/Stable-diffusion' folder
    3. Start launch.py with the '--api' parameter to start the server
    After that, you can use the SD-webui API and
    query the available parameters on the http://localhost:7860/docs page
    """

    model_type: str
    """The type of the model wrapper, which is to identify the model wrapper
    class in model configuration."""

    options: dict
    """A dict contains the options for stable-diffusion option API.
    Modifications made through this parameter are persistent, meaning they will 
    remain in effect for subsequent generation requests until explicitly changed or reset.
    e.g. {"sd_model_checkpoint": "Anything-V3.0-pruned", "CLIP_stop_at_last_layers": 2}"""

    def __init__(
        self,
        config_name: str,
        options: dict = None,
        generate_args: dict = None,
        url: Optional[Union[str, None]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the model wrapper for SD-webui API.

        Args:
            options (`dict`, default `None`):
                The keyword arguments to change the webui settings
                such as model or CLIP skip, this changes will persist across sessions.
                e.g. `{"sd_model_checkpoint": "Anything-V3.0-pruned", "CLIP_stop_at_last_layers": 2}`.
            generate_args (`dict`, default `None`):
                The extra keyword arguments used in SD-webui api generation,
                e.g. `steps`, `seed`.
            url (`str`, default `None`):
                The url of the SD-webui server.
                Defaults to `None`, which is http://127.0.0.1:7860.
        """
        if url is None:
            url = "http://127.0.0.1:7860"

        self.url = url
        self.generate_args = generate_args or {}

        options_url = f"{self.url}/sdapi/v1/options"
        # Get the current default model
        default_model_name = (
            requests.get(options_url)
            .json()["sd_model_checkpoint"]
            .split("[")[0]
            .strip()
        )

        if options is not None:
            # Update webui options if needed
            requests.post(options_url, json=options)
            model_name = options.get("sd_model_checkpoint", default_model_name)
        else:
            model_name = default_model_name

        super().__init__(config_name=config_name, model_name=model_name)

    def format(
        self,
        *args: Union[Msg, Sequence[Msg]],
    ) -> Union[List[dict], str]:
        raise RuntimeError(
            f"Model Wrapper [{type(self).__name__}] doesn't "
            f"need to format the input. Please try to use the "
            f"model wrapper directly.",
        )


class StableDiffusionTxt2imgWrapper(StableDiffusionWrapperBase):

    model_type: str = "sd_txt2img"

    def __call__(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Args:
            prompt (`str`):
                The prompt string to generate images from.
            **kwargs (`Any`):
                The keyword arguments to SD-webui txt2img API, e.g.
                `n_iter`, `steps`, `seed`, `width`, etc. Please refer to
                https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API#api-guide-by-kilvoctu
                or http://localhost:7860/docs
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                A list of image local urls in image_urls field and the
                raw response in raw field.
        """

        # step1: prepare keyword arguments
        payload = {
            "prompt": prompt,
            **kwargs,
            **self.generate_args,
        }

        # step2: forward to generate response
        txt2img_url = f"{self.url}/sdapi/v1/txt2img"
        response = requests.post(url=txt2img_url, json=payload)

        if response.status_code != requests.codes.ok:
            error_msg = f" Status code: {response.status_code},"
            raise RuntimeError(error_msg)

        # step3: record the model api invocation if needed
        output = response.json()
        self._save_model_invocation(
            arguments={
                "model": self.model_name,
                **payload,
            },
            response=output,
        )

        # step4: update monitor accordingly
        session_parameters = output["parameters"]
        size = f"{session_parameters['width']}*{session_parameters['height']}"
        image_count = session_parameters["batch_size"] * session_parameters["n_iter"]

        self.monitor.update_image_tokens(
            model_name=self.model_name,
            image_count=image_count,
            resolution=size,
        )

        # step5: return response
        # Get image base64code as a list
        images = output["images"]
        b64_images = [base64.b64decode(image) for image in images]

        file_manager = FileManager.get_instance()
        # Return local url
        urls = [file_manager.save_image(_) for _ in b64_images]
        text = "Image saved to " + "\n".join(urls)
        return ModelResponse(text=text, image_urls=urls, raw=response)

    def format(self, *args: Msg | Sequence[Msg]) -> List[dict] | str:
        # This is a temporary implementation to focus on the prompt 
        # on single-turn image generation by preserving only the system prompt and 
        # the last user message. This logic might change in the future to support 
        # more complex conversational scenarios
        if len(args) == 0:
            raise ValueError(
                "At least one message should be provided. An empty message "
                "list is not allowed.",
            )

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

        # record user message history as a list of strings
        user_messages = []
        sys_prompt = None
        for i, unit in enumerate(input_msgs):
            if i == 0 and unit.role == "system":
                # if system prompt is available, place it at the beginning
                sys_prompt = _convert_to_str(unit.content)
            elif unit.role == "user":
                # Merge user messages into a conversation history prompt
                user_messages.append(_convert_to_str(unit.content))
            else:
                continue

        content_components = []
        # Add system prompt at the beginning if provided
        if sys_prompt is not None:
            content_components.append(sys_prompt)
        # Add the last user message if the user messages is not empty
        if len(user_messages) > 0:
            content_components.append(user_messages[-1])

        prompt = ",".join(content_components)

        return prompt
