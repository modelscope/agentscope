# -*- coding: utf-8 -*-
"""The placeholder message for RpcAgent."""
import json
from typing import Any, Optional, Union, Sequence

from .msg import Msg, MessageBase
from ..rpc.rpc_config import AsyncResult


class PlaceholderMessage(Msg):
    """A placeholder for the return message of RpcAgent."""

    PLACEHOLDER_ATTRS = {"_is_placeholder", "_async_result"}

    LOCAL_ATTRS = {
        "name",
        "timestamp",
        *PLACEHOLDER_ATTRS,
    }

    def __init__(
        self,
        name: str,
        timestamp: Optional[str] = None,
        async_result: AsyncResult = None,
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
            timestamp (`Optional[str]`, defaults to None):
                The timestamp of the message, if None, it will be set to
                current time.
            async_result (`AsyncResult`): The AsyncResult object returned by server.
        """  # noqa
        super().__init__(
            name=name,
            content=None,
            url=None,
            timestamp=timestamp,
            **kwargs,
        )
        # placeholder indicates whether the real message is still in rpc server
        self._is_placeholder = True
        self._async_result = async_result

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
            msg = self._async_result.get()
            if hasattr(msg, "url") and msg.url is not None:
                url = msg.url
                urls = [url] if isinstance(url, str) else url
                checked_urls = self._async_result.check_and_download_files(
                    urls,
                )
                msg.url = checked_urls[0] if isinstance(url, str) else urls
            self.update(msg)
            # the actual value has been updated, not a placeholder anymore
            self._is_placeholder = False
            self._async_result = None
        return self

    def __reduce__(self) -> tuple:
        if self._is_placeholder:
            return PlaceholderMessage, (
                self.name,
                self.timestamp,
                self._async_result,
            )
        else:
            return super().__reduce__()  # type: ignore[return-value]

    def serialize(self) -> str:
        self.update_value()
        return super().serialize()


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
