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
        config: Optional[dict] = None,
        sys_prompt: Optional[str] = None,
        model_id: str = None,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
    ) -> None:
        """Initialize the text to image agent.

        Arguments:
            name (`str`):
                The name of the agent.
            config (`Optional[dict]`):
                The configuration of the agent, if provided, the agent will
                be initialized from the config rather than the other
                parameters.
            sys_prompt (`Optional[str]`):
                The system prompt of the agent, which can be passed by args
                or hard-coded in the agent.
            model_id (`str`, defaults to None):
                The model id, which is used to load model from configuration.
            use_memory (`bool`, defaults to `True`):
                Whether the agent has memory.
            memory_config (`Optional[dict]`):
                The config of memory.
        """
        super().__init__(
            name=name,
            config=config,
            sys_prompt=sys_prompt,
            model_id=model_id,
            use_memory=use_memory,
            memory_config=memory_config,
        )

    def reply(self, x: dict = None) -> dict:
        if x is not None:
            self.memory.add(x)
        image_urls = self.model(x.content).image_urls
        # TODO: optimize the construction of content
        msg = Msg(
            self.name,
            content="This is the generated image ",
            url=image_urls,
        )
        logger.chat(msg)
        self.memory.add(msg)
        return msg
