# -*- coding: utf-8 -*-
"""The placeholder message for RpcAgent."""
import json
from typing import Any, Optional, List, Union, Sequence

from .msg import Msg, MessageBase
from ..rpc import RpcAgentClient, ResponseStub, call_in_thread
from ..serialize import deserialize
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

    __serialized_attrs = {
        "host",
        "port",
        "task_id",
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
        x: Optional[Union[Msg, Sequence[Msg]]] = None,
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
            x (`Optional[Msg, Sequence[Msg]]`, defaults to `None`):
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
                task_id = deserialize(self._stub.get_response())
            except Exception as e:
                raise ValueError(
                    f"Failed to get task_id: {self._stub.get_response()}",
                ) from e
            self._task_id = task_id
            self._stub = None

    def serialize(self) -> str:
        if self._is_placeholder:
            self.__update_task_id()

            # Serialize the placeholder message
            serialized_dict = {
                "__module__": self.__class__.__module__,
                "__name__": self.__class__.__name__,
            }

            for attr_name in self.__serialized_attrs:
                serialized_dict[attr_name] = getattr(self, attr_name)

            return json.dumps(serialized_dict, ensure_ascii=False)

        else:
            # Serialize into a normal Msg object
            serialized_dict = {
                "__module__": Msg.__module__,
                "__name__": Msg.__name__,
            }

            # TODO: We will merge the placeholder and message classes in the
            #  future to avoid the hard coding of the serialized attributes
            #  here
            for attr_name in [
                "id",
                "name",
                "content",
                "role",
                "metadata",
                "url",
                "timestamp",
            ]:
                serialized_dict[attr_name] = getattr(self, attr_name)

            return json.dumps(serialized_dict, ensure_ascii=False)
