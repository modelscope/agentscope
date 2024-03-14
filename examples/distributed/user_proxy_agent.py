# -*- coding: utf-8 -*-
"""User Proxy Agent class for distributed usage"""
import time
from typing import Sequence, Union
from typing import Optional

from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.web.studio.utils import user_input


class UserProxyAgent(AgentBase):
    """User proxy agent class"""

    def __init__(self, name: str = "User", require_url: bool = False) -> None:
        """Initialize a UserProxyAgent object.

        Arguments:
            name (`str`, defaults to `"User"`):
                The name of the agent. Defaults to "User".
            require_url (`bool`, defaults to `False`):
                Whether the agent requires user to input a URL. Defaults to
                False. The URL can lead to a website, a file,
                or a directory. It will be added into the generated message
                in field `url`.
        """
        super().__init__(name=name)

        self.name = name
        self.require_url = require_url

    def reply(
        self,
        x: dict = None,
        required_keys: Optional[Union[list[str], str]] = None,
    ) -> dict:
        if x is not None:
            self.speak(x)
            self.memory.add(x)

        time.sleep(0.5)
        content = user_input()

        kwargs = {}
        if required_keys is not None:
            if isinstance(required_keys, str):
                required_keys = [required_keys]

            for key in required_keys:
                kwargs[key] = user_input(f"{key}: ")

        # Input url of file, image, video, audio or website
        url = None
        if self.require_url:
            url = user_input("URL: ")

        # Add additional keys
        msg = Msg(
            self.name,
            content=content,
            url=url,
            **kwargs,  # type: ignore[arg-type]
        )

        # Add to memory
        self.memory.add(msg)

        return msg

    def observe(self, x: Union[dict, Sequence[dict]]) -> None:
        if x is not None:
            self.speak(x)  # type: ignore[arg-type]
            self.memory.add(x)
