# -*- coding: utf-8 -*-
"""The base class for message unit"""

from typing import Any, Optional, Union, Literal, List
from uuid import uuid4
import json

from loguru import logger

from ..utils.tools import _get_timestamp, _map_string_to_color_mark


class MessageBase(dict):
    """Base Message class, which is used to maintain information for dialog,
    memory and used to construct prompt.
    """

    def __init__(
        self,
        name: str,
        content: Any,
        role: Literal["user", "system", "assistant"] = "assistant",
        url: Optional[Union[List[str], str]] = None,
        timestamp: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the message object

        Args:
            name (`str`):
                The name of who send the message. It's often used in
                role-playing scenario to tell the name of the sender.
            content (`Any`):
                The content of the message.
            role (`Literal["system", "user", "assistant"]`, defaults to "assistant"):
                The role of who send the message. It can be one of the
                `"system"`, `"user"`, or `"assistant"`. Default to
                `"assistant"`.
            url (`Optional[Union[List[str], str]]`, defaults to None):
                A url to file, image, video, audio or website.
            timestamp (`Optional[str]`, defaults to None):
                The timestamp of the message, if None, it will be set to
                current time.
            **kwargs (`Any`):
                Other attributes of the message.
        """  # noqa
        # id and timestamp will be added to the object as its attributes
        # rather than items in dict
        self.id = uuid4().hex
        if timestamp is None:
            self.timestamp = _get_timestamp()
        else:
            self.timestamp = timestamp

        self.name = name
        self.content = content
        self.role = role

        self.url = url

        self.update(kwargs)

    def __getattr__(self, key: Any) -> Any:
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(f"no attribute '{key}'") from e

    def __setattr__(self, key: Any, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: Any) -> None:
        try:
            del self[key]
        except KeyError as e:
            raise AttributeError(f"no attribute '{key}'") from e

    def serialize(self) -> str:
        """Return the serialized message."""
        raise NotImplementedError


class Msg(MessageBase):
    """The Message class."""

    id: str
    """The id of the message."""

    name: str
    """The name of who send the message."""

    content: Any
    """The content of the message."""

    role: Literal["system", "user", "assistant"]
    """The role of the message sender."""

    metadata: Optional[dict]
    """Save the information for application's control flow, or other
    purposes."""

    url: Optional[Union[List[str], str]]
    """A url to file, image, video, audio or website."""

    timestamp: str
    """The timestamp of the message."""

    def __init__(
        self,
        name: str,
        content: Any,
        role: Literal["system", "user", "assistant"] = None,
        url: Optional[Union[List[str], str]] = None,
        timestamp: Optional[str] = None,
        echo: bool = False,
        metadata: Optional[Union[dict, str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the message object

        Args:
            name (`str`):
                The name of who send the message.
            content (`Any`):
                The content of the message.
            role (`Literal["system", "user", "assistant"]`):
                Used to identify the source of the message, e.g. the system
                information, the user input, or the model response. This
                argument is used to accommodate most Chat API formats.
            url (`Optional[Union[List[str], str]]`, defaults to `None`):
                A url to file, image, video, audio or website.
            timestamp (`Optional[str]`, defaults to `None`):
                The timestamp of the message, if None, it will be set to
                current time.
            echo (`bool`, defaults to `False`):
                Whether to print the message to the console.
            metadata (`Optional[Union[dict, str]]`, defaults to `None`):
                Save the information for application's control flow, or other
                purposes.
            **kwargs (`Any`):
                Other attributes of the message.
        """

        if role is None:
            logger.warning(
                "A new field `role` is newly added to the message. "
                "Please specify the role of the message. Currently we use "
                'a default "assistant" value.',
            )

        super().__init__(
            name=name,
            content=content,
            role=role or "assistant",
            url=url,
            timestamp=timestamp,
            metadata=metadata,
            **kwargs,
        )

        m1, m2 = _map_string_to_color_mark(self.name)
        self._colored_name = f"{m1}{self.name}{m2}"

        if echo:
            logger.chat(self)

    def formatted_str(self, colored: bool = False) -> str:
        """Return the formatted string of the message. If the message has an
        url, the url will be appended to the content.

        Args:
            colored (`bool`, defaults to `False`):
                Whether to color the name of the message
        """
        if colored:
            name = self._colored_name
        else:
            name = self.name

        colored_strs = [f"{name}: {self.content}"]
        if self.url is not None:
            if isinstance(self.url, list):
                for url in self.url:
                    colored_strs.append(f"{name}: {url}")
            else:
                colored_strs.append(f"{name}: {self.url}")
        return "\n".join(colored_strs)

    def serialize(self) -> str:
        return json.dumps({"__type": "Msg", **self})
