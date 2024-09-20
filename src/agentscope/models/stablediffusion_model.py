# -*- coding: utf-8 -*-
"""Model wrapper for stable diffusion models."""
from abc import ABC
import base64
import json
import time
from typing import Any, Optional, Union, Sequence

import requests
from loguru import logger

from . import ModelWrapperBase, ModelResponse
from ..constants import _DEFAULT_MAX_RETRIES
from ..constants import _DEFAULT_RETRY_INTERVAL
from ..message import Msg
from ..manager import FileManager
from ..utils.common import _convert_to_str


class StableDiffusionWrapperBase(ModelWrapperBase, ABC):
    """The base class for stable-diffusion model wrappers.

    To use SD-webui API, please
    1. First download stable-diffusion-webui from
    https://github.com/AUTOMATIC1111/stable-diffusion-webui and
    install it with 'webui-user.bat'
    2. Move your checkpoint to 'models/Stable-diffusion' folder
    3. Start launch.py with the '--api' parameter to start the server
    After that, you can use the SD-webui API and
    query the available parameters on the http://localhost:7862/docs page
    """

    model_type: str = "stable_diffusion"

    def __init__(
        self,
        config_name: str,
        host: str = "127.0.0.1:7862",
        base_url: Optional[Union[str, None]] = None,
        use_https: bool = False,
        generate_args: dict = None,
        headers: dict = None,
        options: dict = None,
        timeout: int = 30,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_interval: int = _DEFAULT_RETRY_INTERVAL,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the SD-webui API client.

        Args:
            config_name (`str`):
                The name of the model config.
            host (`str`, default `"127.0.0.1:7862"`):
                The host port of the stable-diffusion webui server.
            base_url (`str`, default `None`):
                Base URL for the stable-diffusion webui services.
                Generated from host and use_https if not provided.
            use_https (`bool`, default `False`):
                Whether to generate the base URL with HTTPS protocol or HTTP.
            generate_args (`dict`, default `None`):
                The extra keyword arguments used in SD api generation,
                e.g. `{"steps": 50}`.
            headers (`dict`, default `None`):
                HTTP request headers.
            options (`dict`, default `None`):
                The keyword arguments to change the webui settings
                such as model or CLIP skip, this changes will persist.
                e.g. `{"sd_model_checkpoint": "Anything-V3.0-pruned"}`.
        """
        # Construct base_url based on HTTPS usage if not provided
        if base_url is None:
            if use_https:
                base_url = f"https://{host}"
            else:
                base_url = f"http://{host}"

        self.base_url = base_url
        self.options_url = f"{base_url}/sdapi/v1/options"
        self.generate_args = generate_args or {}

        # Initialize the HTTP session and update the request headers
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

        # Set options if provided
        if options:
            self._set_options(options)

        # Get the default model name from the web-options
        model_name = (
            self._get_options()["sd_model_checkpoint"].split("[")[0].strip()
        )
        # Update the model name
        if self.generate_args.get("override_settings"):
            model_name = generate_args["override_settings"].get(
                "sd_model_checkpoint",
                model_name,
            )

        super().__init__(config_name=config_name, model_name=model_name)

        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_interval = retry_interval

    @property
    def url(self) -> str:
        """SD-webui API endpoint URL"""
        raise NotImplementedError()

    def _get_options(self) -> dict:
        response = self.session.get(url=self.options_url)
        if response.status_code != 200:
            logger.error(f"Failed to get options with {response.json()}")
            raise RuntimeError(f"Failed to get options with {response.json()}")
        return response.json()

    def _set_options(self, options: dict) -> None:
        response = self.session.post(url=self.options_url, json=options)
        if response.status_code != 200:
            logger.error(json.dumps(options, indent=4))
            raise RuntimeError(f"Failed to set options with {response.json()}")
        logger.info("Optionsset successfully")

    def _invoke_model(self, payload: dict) -> dict:
        """Invoke SD webui API and record the invocation if needed"""
        # step1: prepare post requests
        for i in range(1, self.max_retries + 1):
            response = self.session.post(url=self.url, json=payload)

            if response.status_code == requests.codes.ok:
                break

            if i < self.max_retries:
                logger.warning(
                    f"Failed to call the model with "
                    f"requests.codes == {response.status_code}, retry "
                    f"{i + 1}/{self.max_retries} times",
                )
                time.sleep(i * self.retry_interval)

        # step2: record model invocation
        # record the model api invocation, which will be skipped if
        # `FileManager.save_api_invocation` is `False`
        self._save_model_invocation(
            arguments=payload,
            response=response.json(),
        )

        # step3: return the response json
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            logger.error(
                json.dumps({"url": self.url, "json": payload}, indent=4),
            )
            raise RuntimeError(
                f"Failed to call the model with {response.json()}",
            )

    def _parse_response(self, response: dict) -> ModelResponse:
        """Parse the response json data into ModelResponse"""
        return ModelResponse(raw=response)


class StableDiffusionImageSynthesisWrapper(StableDiffusionWrapperBase):
    """Stable Diffusion Text-to-Image (txt2img) API Wrapper"""

    model_type: str = "sd_txt2img"

    @property
    def url(self) -> str:
        return f"{self.base_url}/sdapi/v1/txt2img"

    def _parse_response(self, response: dict) -> ModelResponse:
        session_parameters = response["parameters"]
        size = f"{session_parameters['width']}*{session_parameters['height']}"
        image_count = (
            session_parameters["batch_size"] * session_parameters["n_iter"]
        )

        self.monitor.update_image_tokens(
            model_name=self.model_name,
            image_count=image_count,
            resolution=size,
        )

        # Get image base64code as a list
        images = response["images"]
        b64_images = [base64.b64decode(image) for image in images]

        file_manager = FileManager.get_instance()
        # Return local url
        image_urls = [file_manager.save_image(_) for _ in b64_images]
        text = "Image saved to " + "\n".join(image_urls)
        return ModelResponse(text=text, image_urls=image_urls, raw=response)

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
                https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
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
        response = self._invoke_model(payload)

        # step3: parse the response
        return self._parse_response(response)

    def format(self, *args: Union[Msg, Sequence[Msg]]) -> str:
        # This is a temporary implementation to focus on the prompt
        # on single-turn image generation by preserving only the system prompt
        # and the last user message. This logic might change in the future
        # to support more complex conversational scenarios
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
        if sys_prompt:
            content_components.append(sys_prompt)
        # Add the last user message if the user messages is not empty
        if len(user_messages) > 0:
            content_components.append(user_messages[-1])

        prompt = ",".join(content_components)

        return prompt
