# -*- coding: utf-8 -*-
"""The placeholder message for RpcAgent."""
import json
from typing import Any, Optional, List, Union, Sequence

from loguru import logger

from .msg import Msg, MessageBase
from ..rpc import RpcAgentClient, ResponseStub, call_in_thread
from ..utils.tools import is_web_accessible


class PlaceholderMessage(Msg):
    """A placeholder for the return message of RpcAgent."""

    PLACEHOLDER_ATTRS = {
        "_host",
        "_port",
        "_client",
        "_task_id",
        "_stub",
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
        url: Optional[Union[List[str], str]] = None,
        timestamp: Optional[str] = None,
        host: str = None,
        port: int = None,
        task_id: int = None,
        client: Optional[RpcAgentClient] = None,
        x: dict = None,
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
            role (`Literal["system", "user", "assistant"]`, defaults to "assistant"):
                The role of the message, which can be one of the `"system"`,
                `"user"`, or `"assistant"`.
            url (`Optional[Union[List[str], str]]`, defaults to None):
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
            client (`RpcAgentClient`, defaults to `None`):
                An RpcAgentClient instance used to connect to the generator of
                this placeholder.
            x (`dict`, defaults to `None`):
                Input parameters used to call rpc methods on the client.
        """  # noqa
        super().__init__(
            name=name,
            content=content,
            url=url,
            timestamp=timestamp,
            **kwargs,
        )
        # placeholder indicates whether the real message is still in rpc server
        self._is_placeholder = True
        if client is None:
            self._stub: ResponseStub = None
            self._host: str = host
            self._port: int = port
            self._task_id: int = task_id
        else:
            self._stub = call_in_thread(
                client,
                x.serialize() if x is not None else "",
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

    def update_value(self) -> MessageBase:
        """Get attribute values from rpc agent server immediately"""
        if self._is_placeholder:
            # retrieve real message from rpc agent server
            self.__update_task_id()
            client = RpcAgentClient(self._host, self._port)
            result = client.update_placeholder(task_id=self._task_id)
            msg = deserialize(result)
            self.__update_url(msg)  # type: ignore[arg-type]
            self.update(msg)
            # the actual value has been updated, not a placeholder anymore
            self._is_placeholder = False
        return self

    def __update_url(self, msg: MessageBase) -> None:
        """Update the url field of the message."""
        if hasattr(msg, "url") and msg.url is None:
            return
        url = msg.url
        if isinstance(url, str):
            urls = [url]
        else:
            urls = url
        checked_urls = []
        for url in urls:
            if not is_web_accessible(url):
                client = RpcAgentClient(self._host, self._port)
                checked_urls.append(client.download_file(path=url))
            else:
                checked_urls.append(url)
        msg.url = checked_urls[0] if isinstance(url, str) else checked_urls

    def __update_task_id(self) -> None:
        if self._stub is not None:
            try:
                resp = deserialize(self._stub.get_response())
            except Exception as e:
                logger.error(
                    f"Failed to get task_id: {self._stub.get_response()}",
                )
                raise ValueError(
                    f"Failed to get task_id: {self._stub.get_response()}",
                ) from e
            self._task_id = resp["task_id"]  # type: ignore[call-overload]
            self._stub = None

    def serialize(self) -> str:
        if self._is_placeholder:
            self.__update_task_id()
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
    "PlaceholderMessage": PlaceholderMessage,
}


def deserialize(s: Union[str, bytes]) -> Union[Msg, Sequence]:
    """Deserialize json string into MessageBase"""
    js_msg = json.loads(s)
    msg_type = js_msg.pop("__type")
    if msg_type == "List":
        return [deserialize(s) for s in js_msg["__value"]]
    elif msg_type not in _MSGS:
        raise NotImplementedError(
            f"Deserialization of {msg_type} is not supported.",
        )
    return _MSGS[msg_type](**js_msg)


def serialize(messages: Union[Sequence[MessageBase], MessageBase]) -> str:
    """Serialize multiple MessageBase instance"""
    if isinstance(messages, MessageBase):
        return messages.serialize()
    seq = [msg.serialize() for msg in messages]
    return json.dumps({"__type": "List", "__value": seq})
