# -*- coding: utf-8 -*-
"""A proxy object which represent a object located in a rpc server."""
from typing import Any, Callable
from abc import ABC
from inspect import getmembers, isfunction
from types import FunctionType

from ..rpc import RpcAgentClient
from ..exception import AgentServerUnsupportedMethodError


def get_public_methods(cls: type) -> list[str]:
    """Get all public methods of the given class."""
    return [
        name
        for name, member in getmembers(cls, predicate=isfunction)
        if isinstance(member, FunctionType) and not name.startswith("_")
    ]


class RpcObject(ABC):
    """A proxy object which represent a object located in a rpc server."""

    def __init__(self, host: str, port: int, oid: str, cls: type) -> None:
        """Initialize the rpc object.

        Args:
            host (`str`): The host of the rpc server.
            port (`int`): The port of the rpc server.
            oid (`str`): The id of the object in the rpc server.
            cls (`type`): The class of the object in the rpc server.
        """
        # TODO: avoid re-init `host`, `port`, `_agent_id`, `client`
        self.host = host
        self.port = port
        self._agent_id = oid
        self._supported_attributes = get_public_methods(cls)
        self.client = RpcAgentClient(host, port)

    def _call_rpc_func(self, func_name: str, args: tuple, kwargs: dict) -> Any:
        """Call a function in rpc server."""
        return self.client.call_agent_func(
            agent_id=self._agent_id,
            func_name=func_name,
            *args,
            **kwargs,
        )

    def __getattr__(self, name: str) -> Callable:
        if name not in self._supported_attributes:
            raise AgentServerUnsupportedMethodError(
                host=self.host,
                port=self.port,
                oid=self._agent_id,
                func_name=name,
            )

        def wrapper(*args, **kwargs) -> Any:  # type: ignore[no-untyped-def]
            return self._call_rpc_func(
                func_name=name,
                args=args,
                kwargs=kwargs,
            )

        return wrapper

    def __getstate__(self) -> dict:
        """For serialization."""
        return self.__dict__.copy()

    def __setstate__(self, state: dict) -> None:
        """For deserialization."""
        self.__dict__.update(state)
