# -*- coding: utf-8 -*-
# mypy: disable-error-code="misc"
"""The placeholder message for RpcAgent."""
import os
from typing import Any, Optional, List, Union, Sequence, Literal

from loguru import logger

from .msg import Msg
from ..rpc import RpcAgentClient, ResponseStub, call_in_thread
from ..serialize import deserialize, is_serializable, serialize
from ..utils.common import _is_web_url


class PlaceholderMessage(Msg):
    """A placeholder for the return message of RpcAgent."""

    __placeholder_attrs = {
        "_host",
        "_port",
        "_client",
        "_task_id",
        "_stub",
        "_is_placeholder",
    }

    __serialized_attrs = {
        "_host",
        "_port",
        "_task_id",
    }

    _is_placeholder: bool
    """Indicates whether the real message is still in the rpc server."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        task_id: int = None,
        client: Optional[RpcAgentClient] = None,
        x: Optional[Union[Msg, Sequence[Msg]]] = None,
    ) -> None:
        """A placeholder message, records the address of the real message.

        Args:
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
        """
        super().__init__(
            name="",
            content="",
            role="assistant",
            url=None,
            metadata=None,
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
                serialize(x),
                "_reply",
            )
            self._host = client.host
            self._port = client.port
            self._task_id = None

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
        if not is_serializable(value):
            logger.warning(
                f"The content of {type(value)} is not serializable, which "
                f"may cause problems.",
            )
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
            self.__update_task_id()
            client = RpcAgentClient(self._host, self._port)
            result = client.update_placeholder(task_id=self._task_id)

            # Update the values according to the result obtained from the
            # distributed agent
            data = deserialize(result)

            self.id = data.id
            self.name = data.name
            self.role = data.role
            self.content = data.content
            self.metadata = data.metadata

            self.timestamp = data.timestamp

            # For url field, download the file if it's a local file of the
            # distributed agent, and turn it into a local url
            self.url = self.__update_url(data.url)

            self._is_placeholder = False

    def __update_url(
        self,
        url: Union[list[str], str, None],
    ) -> Union[list, str, None]:
        """If the url links to
            - a file that the main process can access, return the url directly
            - a web resource, return the url directly
            - a local file of the distributed agent (maybe in the deployed
            machine of the distributed agent), we download the file and update
            the url to the local url.
            - others (maybe a meaningless url, e.g "xxx.com"), return the url.

        Args:
            url (`Union[List[str], str, None]`):
                The url to be updated.
        """

        if url is None:
            return None

        if isinstance(url, str):
            if os.path.exists(url) or _is_web_url(url):
                return url

            # Try to get the file from the distributed agent
            client = RpcAgentClient(self.host, self.port)
            # TODO: what if failed here?
            local_url = client.download_file(path=url)

            return local_url

        if isinstance(url, list):
            return [self.__update_url(u) for u in url]

        raise TypeError(
            f"Invalid URL type, expect str, list[str] or None, "
            f"got {type(url)}.",
        )

    def __update_task_id(self) -> None:
        """Get the task_id from the rpc server."""
        if self._stub is not None:
            try:
                task_id = deserialize(self._stub.get_response())
            except Exception as e:
                raise ValueError(
                    f"Failed to get task_id: {self._stub.get_response()}",
                ) from e
            self._task_id = task_id
            self._stub = None

    def to_dict(self) -> dict:
        """Serialize the placeholder message."""
        if self._is_placeholder:
            self.__update_task_id()

            # Serialize the placeholder message
            serialized_dict = {
                "__module__": self.__class__.__module__,
                "__name__": self.__class__.__name__,
            }

            for attr_name in self.__serialized_attrs:
                serialized_dict[attr_name] = getattr(self, attr_name)

            return serialized_dict

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
