# -*- coding: utf-8 -*-
"""A agent that convert text to image."""

from typing import Optional
from loguru import logger

from .agent import AgentBase
from ..message import Msg


class TextToImageAgent(AgentBase):
    """A agent used to perform text to image tasks."""

    def __init__(
        self,
        name: str,
        sys_prompt: str,
        model_config_name: str,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
    ) -> None:
        """Initialize the text to image agent.

        Arguments:
            name (`str`):
                The name of the agent.
            sys_prompt (`Optional[str]`):
                The system prompt of the agent, which can be passed by args
                or hard-coded in the agent.
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
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            use_memory=use_memory,
            memory_config=memory_config,
        )

    def reply(self, x: dict = None) -> dict:
        if self.memory:
            self.memory.add(x)

        image_urls = self.model(x.content).image_urls
        # TODO: optimize the construction of content
        msg = Msg(
            self.name,
            content="This is the generated image ",
            url=image_urls,
        )
        logger.chat(msg)

        if self.memory:
            self.memory.add(msg)

        return msg
