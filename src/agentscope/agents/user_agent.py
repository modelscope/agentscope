# -*- coding: utf-8 -*-
"""User Agent class"""
import time
from typing import Union
from typing import Optional
from loguru import logger

from agentscope.agents import AgentBase
from agentscope.web.client import _studio_client
from agentscope.message import Msg
from agentscope.web.gradio.utils import user_input


class UserAgent(AgentBase):
    """User agent class"""

    def __init__(self, name: str = "User", require_url: bool = False) -> None:
        """Initialize a UserAgent object.

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
        timeout: Optional[int] = None,
    ) -> dict:
        """
        Processes the input provided by the user and stores it in memory,
        potentially formatting it with additional provided details.

        The method prompts the user for input, then optionally prompts for
        additional specifics based on the provided format keys. All
        information is encapsulated in a message object, which is then
        added to the object's memory.

        Arguments:
            x (`dict`, defaults to `None`):
                A dictionary containing initial data to be added to memory.
                Defaults to None.
            required_keys \
                (`Optional[Union[list[str], str]]`, defaults to `None`):
                Strings that requires user to input, which will be used as
                the key of the returned dict. Defaults to None.
            timeout (`Optional[int]`, defaults to `None`):
                Raise `TimeoutError` if user exceed input time, set to None
                for no limit.

        Returns:
            `dict`: A dictionary representing the message object that contains
            the user's input and any additional details. This is also
            stored in the object's memory.
        """
        if self.memory:
            self.memory.add(x)

        if _studio_client.active:
            logger.info(
                f"Waiting for input from:\n\n"
                f"    * {_studio_client.get_run_detail_page_url()}\n",
            )
            raw_input = _studio_client.get_user_input(
                agent_id=self.agent_id,
                name=self.name,
                require_url=self.require_url,
                required_keys=required_keys,
            )

            print("Obtain input:", raw_input)
            content = raw_input["content"]
            url = raw_input.get("url", None)
            kwargs = {}
        else:
            # TODO: To avoid order confusion, because `input` print much
            #  quicker than logger.chat
            time.sleep(0.5)
            content = user_input(timeout=timeout)
            kwargs = {}
            if required_keys is not None:
                if isinstance(required_keys, str):
                    required_keys = [required_keys]

                for key in required_keys:
                    kwargs[key] = input(f"{key}: ")

            # Input url of file, image, video, audio or website
            url = None
            if self.require_url:
                url = input("URL (or Enter to skip): ")
                if url == "":
                    url = None

        # Add additional keys
        msg = Msg(
            name=self.name,
            role="user",
            content=content,
            url=url,
            **kwargs,  # type: ignore[arg-type]
        )

        self.speak(msg)

        # Add to memory
        if self.memory:
            self.memory.add(msg)

        return msg

    def speak(
        self,
        content: Union[str, dict],
    ) -> None:
        """Speak the content to the audience."""
        logger.chat(content, disable_studio=True)
        if _studio_client.active:
            _studio_client.push_message(
                name=content.get("name", ""),
                role=content.get("role", "user"),
                content=content.get("content", ""),
                metadata=content.get("metadata", {}),
                url=content.get("url", None),
                timestamp=content.get("timestamp", None),
            )
