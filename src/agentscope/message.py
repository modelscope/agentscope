# -*- coding: utf-8 -*-
"""The base class for message unit"""

from typing import Any, Optional, Union, Sequence, Literal
from uuid import uuid4
import json

from loguru import logger

from .rpc import RpcAgentClient, ResponseStub, call_in_thread
from .utils.tools import _get_timestamp

MSG_TYPE_REAL = "REAL"
MSG_TYPE_PLACEHOLDER = "PLACEHOLDER"


class Msg:
    """The message class."""

    __type__: str = MSG_TYPE_REAL

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

    url: Optional[Union[Sequence[str], str]]
    """A url to file, image, video, audio or website."""

    timestamp: str
    """The timestamp of the message."""

    host: Optional[str] = None
    """The hostname where to obtain the message."""

    port: Optional[int] = None
    """The port where to obtain the message."""

    _serialize_attrs = {
        "__type__",
        "id",
        "name",
        "content",
        "role",
        "metadata",
        "url",
        "timestamp",
        "host",
        "port",
    }
    """The attributes to be serialized."""

    def __init__(
        self,
        name: str,
        content: Any,
        role: Literal["system", "user", "assistant"],
        url: Optional[Union[Sequence[str], str]] = None,
        metadata: Optional[Union[dict, str]] = None,
        timestamp: Optional[str] = None,
        echo: bool = False,
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
            url (`Optional[Union[list[str], str]]`, defaults to `None`):
                A url to file, image, video, audio or website.
            timestamp (`Optional[str]`, defaults to `None`):
                The timestamp of the message, if None, it will be set to
                current time.
            metadata (`Optional[Union[dict, str]]`, defaults to `None`):
                Save the information for application's control flow, or other
                purposes.
            echo (`bool`, defaults to `False`):
                Whether to print the message to the console.
        """
        # id and timestamp will be added to the object as its attributes
        # rather than items in dict
        self.id = uuid4().hex
        self.timestamp = timestamp or _get_timestamp()

        self.name = name
        self.content = content
        self.role = role
        self.url = url
        self.metadata = metadata

        if echo:
            logger.chat(self)

    def serialize(self) -> str:
        """Return the serialized message."""
        json_dict = {getattr(self, _) for _ in self._serialize_attrs}

        return json.dumps(json_dict, ensure_ascii=False)

    @classmethod
    def deserialize(cls, json_dict_or_str: dict) -> "Msg":
        """Deserialize the json string into a message object."""

        if isinstance(json_dict_or_str, str):
            json_dict = json.loads(json_dict_or_str)
        else:
            json_dict = json_dict_or_str

        for attr in cls._serialize_attrs:
            assert attr in json_dict, f"Missing attribute {attr} for Msg."

        msg_obj = cls(name="", content="", role="assistant")
        for k, v in json_dict.items():
            setattr(msg_obj, k, v)
        return msg_obj


class PlaceholderMessage(Msg):
    """A placeholder for the return message of RpcAgent."""

    __type__: str = MSG_TYPE_PLACEHOLDER

    LOCAL_ATTRS = {
        "_host",
        "_port",
        "_client",
        "_task_id",
        "_stub",
        "_is_placeholder",
    }

    _serialize_attrs = {
        "__type__",
        "_host",
        "_port",
        "_task_id",
    }

    def __init__(
        self,
        client: Optional[RpcAgentClient] = None,
        x: Union[Msg, Sequence[Msg]] = None,
    ) -> None:
        """A placeholder message, records the address of the real message.

        Args:
            client (`RpcAgentClient`, defaults to `None`):
                An RpcAgentClient instance used to connect to the generator of
                this placeholder.
            x (`Union[Msg, Sequence[Msg]]`, defaults to `None`):
                Input parameters used to call rpc methods on the client.
        """

        # Placeholder indicates whether the real message is still in rpc server
        self._is_placeholder = True

        self._stub = call_in_thread(
            client,
            msg_serialize(x),
            "_reply",
        )
        self._host = client.host
        self._port = client.port
        self._task_id = None

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
        return Msg.__getattr__(self, __name)

    def update_value(self) -> Msg:
        """Get attribute values from rpc agent server immediately."""
        if self._is_placeholder:
            # retrieve real message from rpc agent server
            self.__update_task_id()
            client = RpcAgentClient(self._host, self._port)
            result = client.call_func(
                func_name="_get",
                value=json.dumps({"task_id": self._task_id}),
            )
            msg = msg_deserialize(result)
            status = msg.pop("__status", "OK")
            if status == "ERROR":
                raise RuntimeError(msg.content)

            self.update(msg)
            # the actual value has been updated, not a placeholder anymore
            self._is_placeholder = False
        return self

    def __update_task_id(self) -> None:
        if self._stub is not None:
            try:
                self._task_id: str = self._stub.get_response()
            except Exception as e:
                raise ValueError(
                    f"Failed to get task_id: {self._stub.get_response()}",
                ) from e
            self._stub = None

    def serialize(self) -> str:
        if self._is_placeholder:
            self.__update_task_id()
            return json.dumps(
                {
                    "__type__": self.__type__,
                    "host": self._host,
                    "port": self._port,
                    "task_id": self._task_id,
                },
            )
        else:
            return super().serialize()

    @classmethod
    def deserialize(cls, json_dict_or_str: dict) -> "PlaceholderMessage":
        """Deserialize the json string into an object."""

        if isinstance(json_dict_or_str, str):
            json_dict = json.loads(json_dict_or_str)
        else:
            json_dict = json_dict_or_str


        placeholder_obj = cls()





def _dict_to_msg(dct: dict) -> Union[Msg, dict]:
    if dct.get("__type__", None) == MSG_TYPE_REAL:
        return Msg.deserialize(dct)
    elif dct.get("__type__", None) == MSG_TYPE_PLACEHOLDER:
        return PlaceholderMessage.deserialize(dct)

    return dct


def msg_deserialize(s: Union[str, bytes]) -> Union[Msg, Sequence]:
    """Deserialize json string into MessageBase.

    Args:
        s (`Union[str, bytes]`):
            The json string to be deserialized.
    """
    return json.loads(s, object_hook=_dict_to_msg)


def _msg_serialize(obj: Any) -> str:
    """Serialize Msg object into a json string."""
    if isinstance(obj, Msg):
        return obj.serialize()
    raise TypeError(f"Type {type(obj)} is not serializable.")


def msg_serialize(messages: Union[Sequence[Msg], Msg]) -> str:
    """Serialize Msg object(s) into a json string."""
    return json.dumps(messages, default=_msg_serialize)
