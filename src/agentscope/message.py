# -*- coding: utf-8 -*-
"""The base class for message unit"""

from typing import Any, Optional, Union, Sequence
from uuid import uuid4
import json

from loguru import logger

from .rpc import RpcAgentClient
from .utils.tools import _get_timestamp


class MessageBase(dict):
    """Base Message class, which is used to maintain information for dialog,
    memory and used to construct prompt.
    """

    def __init__(
        self,
        name: str,
        content: Any,
        url: Optional[Union[Sequence[str], str]] = None,
        timestamp: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the message object

        Args:
            name (`str`):
                The name of who send the message. It's often used in
                role-playing scenario to tell the name of the sender.
                However, you can also only use `role` when calling openai api.
                The usage of `name` refers to
                https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            content (`Any`):
                The content of the message.
            url (`Optional[Union[list[str], str]]`, defaults to None):
                A url to file, image, video, audio or website.
            timestamp (`Optional[str]`, defaults to None):
                The timestamp of the message, if None, it will be set to
                current time.
            **kwargs (`Any`):
                Other attributes of the message. For OpenAI API, you should
                add "role" from `["system", "user", "assistant", "function"]`.
                When calling OpenAI API, `"role": "assistant"` will be added
                to the messages that don't have "role" attribute.

        """
        # id and timestamp will be added to the object as its attributes
        # rather than items in dict
        self.id = uuid4().hex
        if timestamp is None:
            self.timestamp = _get_timestamp()
        else:
            self.timestamp = timestamp

        self.name = name
        self.content = content

        if url:
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

    def to_str(self) -> str:
        """Return the string representation of the message"""
        raise NotImplementedError

    def serialize(self) -> str:
        """Return the serialized message."""
        raise NotImplementedError


class Msg(MessageBase):
    """The Message class."""

    def __init__(
        self,
        name: str,
        content: Any,
        url: Optional[Union[Sequence[str], str]] = None,
        timestamp: Optional[str] = None,
        echo: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name,
            content=content,
            url=url,
            timestamp=timestamp,
            **kwargs,
        )
        if echo:
            logger.chat(self)

    def to_str(self) -> str:
        """Return the string representation of the message"""
        return f"{self.name}: {self.content}"

    def serialize(self) -> str:
        return json.dumps({"__type": "Msg", **self})


class Tht(MessageBase):
    """The Thought message is used to record the thought of the agent to
    help them make decisions and responses. Generally, it shouldn't be
    passed to or seen by the other agents.

    In our framework, we formulate the thought in prompt as follows:
    - For OpenAI API calling:

    .. code-block:: python

        [
            ...
            {
                "role": "assistant",
                "name": "thought",
                "content": "I should ..."
            },
            ...
        ]

    - For open-source models that accepts string as input:

    .. code-block:: python

        ...
        {self.name} thought: I should ...
        ...

    We admit that there maybe better ways to formulate the thought. Users
    are encouraged to create their own thought formulation methods by
    inheriting `MessageBase` class and rewrite the `__init__` and `to_str`
    function.

    .. code-block:: python

        class MyThought(MessageBase):
            def to_str(self) -> str:
                # implement your own thought formulation method
                pass
    """

    def __init__(
        self,
        content: Any,
        timestamp: Optional[str] = None,
    ) -> None:
        super().__init__(
            name="thought",
            content=content,
            timestamp=timestamp,
        )

    def to_str(self) -> str:
        """Return the string representation of the message"""
        return f"{self.name} thought: {self.content}"

    def serialize(self) -> str:
        return json.dumps({"__type": "Tht", **self})


class PlaceholderMessage(MessageBase):
    """A placeholder for the return message of RpcAgent."""

    PLACEHOLDER_ATTRS = {
        "_host",
        "_port",
        "_client",
        "_task_id",
        "_is_placeholder",
    }

    LOCAL_ATTRS = {
        "name",
        "timestamp",
        *PLACEHOLDER_ATTRS,
    }

    def __init__(
        self,
        name: str,
        content: Any,
        url: Optional[Union[Sequence[str], str]] = None,
        timestamp: Optional[str] = None,
        host: str = None,
        port: int = None,
        task_id: int = None,
        **kwargs: Any,
    ) -> None:
        """A placeholder message, records the address of the real message.

        Args:
            name (`str`):
                The name of who send the message. It's often used in
                role-playing scenario to tell the name of the sender.
                However, you can also only use `role` when calling openai api.
                The usage of `name` refers to
                https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            content (`Any`):
                The content of the message.
            url (`Optional[Union[list[str], str]]`, defaults to None):
                A url to file, image, video, audio or website.
            timestamp (`Optional[str]`, defaults to None):
                The timestamp of the message, if None, it will be set to
                current time.
            host (`str`, defaults to `None`):
                The hostname of the rpc server where the real message is
                located.
            port (`int`, defaults to `None`):
                The port of the rpc server where the real message is located.
            task_id (`int`, defaults to `None`):
                The task id of the real message in the rpc server.
        """
        super().__init__(
            name=name,
            content=content,
            url=url,
            timestamp=timestamp,
            **kwargs,
        )
        # placeholder indicates whether the real message is still in rpc server
        self._is_placeholder = True
        self._host = host
        self._port = port
        self._task_id = task_id

    def __is_local(self, key: Any) -> bool:
        return (
            key in PlaceholderMessage.LOCAL_ATTRS or not self._is_placeholder
        )

    def __getattr__(self, __name: str) -> Any:
        """Get attribute value from PlaceholderMessage. Get value from rpc
        agent server if necessary.

        Args:
            __name (`str`):
                Attribute name.
        """
        if not self.__is_local(__name):
            self.update_value()
        return MessageBase.__getattr__(self, __name)

    def __getitem__(self, __key: Any) -> Any:
        """Get item value from PlaceholderMessage. Get value from rpc
        agent server if necessary.

        Args:
            __key (`Any`):
                Item name.
        """
        if not self.__is_local(__key):
            self.update_value()
        return MessageBase.__getitem__(self, __key)

    def to_str(self) -> str:
        return f"{self.name}: {self.content}"

    def update_value(self) -> MessageBase:
        """Get attribute values from rpc agent server immediately"""
        if self._is_placeholder:
            # retrieve real message from rpc agent server
            client = RpcAgentClient(self._host, self._port)
            result = client.call_func(
                func_name="_get",
                value=json.dumps({"task_id": self._task_id}),
            )
            self.update(deserialize(result))
            # the actual value has been updated, not a placeholder any more
            self._is_placeholder = False
        return self

    def serialize(self) -> str:
        if self._is_placeholder:
            return json.dumps(
                {
                    "__type": "PlaceholderMessage",
                    "name": self.name,
                    "content": None,
                    "timestamp": self.timestamp,
                    "host": self._host,
                    "port": self._port,
                    "task_id": self._task_id,
                },
            )
        else:
            states = {
                k: v
                for k, v in self.items()
                if k not in PlaceholderMessage.PLACEHOLDER_ATTRS
            }
            states["__type"] = "Msg"
            return json.dumps(states)


_MSGS = {
    "Msg": Msg,
    "Tht": Tht,
    "PlaceholderMessage": PlaceholderMessage,
}


def deserialize(s: str) -> Union[MessageBase, Sequence]:
    """Deserialize json string into MessageBase"""
    js_msg = json.loads(s)
    msg_type = js_msg.pop("__type")
    if msg_type == "List":
        return [deserialize(s) for s in js_msg["__value"]]
    elif msg_type not in _MSGS:
        raise NotImplementedError(
            "Deserialization of {msg_type} is not supported.",
        )
    return _MSGS[msg_type](**js_msg)


def serialize(messages: Union[Sequence[MessageBase], MessageBase]) -> str:
    """Serialize multiple MessageBase instance"""
    if isinstance(messages, MessageBase):
        return messages.serialize()
    seq = [msg.serialize() for msg in messages]
    return json.dumps({"__type": "List", "__value": seq})
