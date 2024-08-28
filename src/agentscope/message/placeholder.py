# -*- coding: utf-8 -*-
# mypy: disable-error-code="misc"
"""The placeholder message for RpcAgent."""
from typing import Any, Optional, Union, List, Literal

from .msg import Msg
from ..rpc.rpc_config import AsyncResult


class PlaceholderMessage(Msg):
    """A placeholder for the return message of RpcAgent."""

    PLACEHOLDER_ATTRS = {"_is_placeholder", "_async_result"}

    __serialized_attrs = {
        "_async_result",
    }

    _is_placeholder: bool
    """Indicates whether the real message is still in the rpc server."""

    def __init__(
        self,
        async_result: AsyncResult = None,
        **kwargs: Any,
    ) -> None:
        """A placeholder message, records the address of the real message.

        Args:
            async_result (`AsyncResult`): The AsyncResult object returned by server.
        """  # noqa
        super().__init__(
            name="",
            role="assistant",
            content=None,
            url=None,
            **kwargs,
        )
        # placeholder indicates whether the real message is still in rpc server
        self._is_placeholder = True
        self._async_result = async_result

    @property
    def id(self) -> str:
        """The identity of the message."""
        if self._is_placeholder:
            self.update_value()
        return self._id

    @property
    def name(self) -> str:
        """The name of the message sender."""
        if self._is_placeholder:
            self.update_value()
        return self._name

    @property
    def content(self) -> Any:
        """The content of the message."""
        if self._is_placeholder:
            self.update_value()
        return self._content

    @property
    def role(self) -> Literal["system", "user", "assistant"]:
        """The role of the message sender, chosen from 'system', 'user',
        'assistant'."""
        if self._is_placeholder:
            self.update_value()
        return self._role

    @property
    def url(self) -> Optional[Union[str, List[str]]]:
        """A URL string or a list of URL strings."""
        if self._is_placeholder:
            self.update_value()
        return self._url

    @property
    def metadata(self) -> Optional[Union[dict, str]]:
        """The metadata of the message, which can store some additional
        information."""
        if self._is_placeholder:
            self.update_value()
        return self._metadata

    @property
    def timestamp(self) -> str:
        """The timestamp when the message is created."""
        if self._is_placeholder:
            self.update_value()
        return self._timestamp

    @id.setter  # type: ignore[no-redef]
    def id(self, value: str) -> None:
        """Set the identity of the message."""
        self._id = value

    @name.setter  # type: ignore[no-redef]
    def name(self, value: str) -> None:
        """Set the name of the message sender."""
        self._name = value

    @content.setter  # type: ignore[no-redef]
    def content(self, value: Any) -> None:
        """Set the content of the message."""
        self._content = value

    @role.setter  # type: ignore[no-redef]
    def role(self, value: Literal["system", "user", "assistant"]) -> None:
        """Set the role of the message sender. The role must be one of
        'system', 'user', 'assistant'."""
        if value not in ["system", "user", "assistant"]:
            raise ValueError(
                f"Invalid role {value}. The role must be one of "
                f"['system', 'user', 'assistant']",
            )
        self._role = value

    @url.setter  # type: ignore[no-redef]
    def url(self, value: Union[str, List[str], None]) -> None:
        """Set the url of the message. The url can be a URL string or a list of
        URL strings."""
        self._url = value

    @metadata.setter  # type: ignore[no-redef]
    def metadata(self, value: Union[dict, str, None]) -> None:
        """Set the metadata of the message to store some additional
        information."""
        self._metadata = value

    @timestamp.setter  # type: ignore[no-redef]
    def timestamp(self, value: str) -> None:
        """Set the timestamp of the message."""
        self._timestamp = value

    def update_value(self) -> None:
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
            # the actual value has been updated, not a placeholder anymore
            self._is_placeholder = False
            self._async_result = None
            self.id = msg.id
            self.name = msg.name
            self.role = msg.role
            self.content = msg.content
            self.metadata = msg.metadata
            self.timestamp = msg.timestamp
            self.url = msg.url
        return self

    def __reduce__(self) -> tuple:
        if self._is_placeholder:
            return PlaceholderMessage, (self._async_result,)
        else:
            return super().__reduce__()  # type: ignore[return-value]

    def to_dict(self) -> dict:
        """Serialize the placeholder message."""
        if self._is_placeholder:
            self.update_value()
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
            "url",
            "metadata",
            "timestamp",
        ]:
            serialized_dict[attr_name] = getattr(self, attr_name)
        return serialized_dict

    @classmethod
    def from_dict(cls, serialized_dict: dict) -> "PlaceholderMessage":
        """Create a PlaceholderMessage from a dictionary."""
        return cls(
            host=serialized_dict["_host"],
            port=serialized_dict["_port"],
            task_id=serialized_dict["_task_id"],
        )
