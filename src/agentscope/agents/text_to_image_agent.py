# -*- coding: utf-8 -*-
"""An agent that convert text to image."""

from typing import Optional, Union, Sequence

from loguru import logger

from .agent import AgentBase
from ..message import Msg


class TextToImageAgent(AgentBase):
    """
    A agent used to perform text to image tasks.

    TODO: change the agent into a service.
    """

    def __init__(
        self,
        name: str,
        model_config_name: str,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
    ) -> None:
        """Initialize the text to image agent.

        Arguments:
            name (`str`):
                The name of the agent.
            model_config_name (`str`, defaults to None):
                The name of the model config, which is used to load model from
                configuration.
            use_memory (`bool`, defaults to `True`):
                Whether the agent has memory.
            memory_config (`Optional[dict]`):
                The config of memory.
        """
        super().__init__(
            name=name,
            sys_prompt="",
            model_config_name=model_config_name,
            use_memory=use_memory,
            memory_config=memory_config,
        )

        logger.warning(
            "The `TextToImageAgent` will be deprecated in v0.0.6, "
            "please use `text_to_image` service and `ReActAgent` instead.",
        )

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        if self.memory:
            self.memory.add(x)
        if x is None:
            # get the last message from memory
            if self.memory and self.memory.size() > 0:
                x = self.memory.get_memory()[-1]
            else:
                return Msg(
                    self.name,
                    content="Please provide a text prompt to generate image.",
                    role="assistant",
                )
        image_urls = self.model(x.content).image_urls
        # TODO: optimize the construction of content
        msg = Msg(
            self.name,
            content="This is the generated image",
            role="assistant",
            url=image_urls,
        )

        self.speak(msg)

        if self.memory:
            self.memory.add(msg)

        return msg
