# -*- coding: utf-8 -*-
"""The rpc version of env."""
import uuid
from typing import List, Type

from .env import EventListener, Env
from ..rpc.rpc_object import RpcObject


class RpcEnv(Env, RpcObject):
    """The rpc version of env."""

    def __init__(
        self,
        name: str,
        env_cls: Type[Env],
        host: str = "localhost",
        port: int = None,
        env_id: str = None,
        connect_existing: bool = False,
        max_pool_size: int = 8192,
        max_timeout_seconds: int = 7200,
        local_mode: bool = True,
        env_configs: dict = None,
    ) -> None:
        """Initialize an RpcEnv instance.

        Args:
            name (`str`): the name of the env.
            cls (type): The Env sub-class.
            host (`str`, defaults to `localhost`):
                Hostname of the rpc agent server.
            port (`int`, defaults to `None`):
                Port of the rpc agent server.
            env_id (`str`, defaults to `None`):
                The id of the env.
            connect_existing (`bool`, defaults to `False`):
                Set to `True`, if the env is already running on the server.
            max_pool_size (`int`, defaults to `8192`):
                Max number of task results that the server can accommodate.
            max_timeout_seconds (`int`, defaults to `7200`):
                Timeout for task results.
            local_mode (`bool`, defaults to `True`):
                Whether the started gRPC server only listens to local
                requests.
        """
        self._name = name
        RpcObject.__init__(
            self,
            cls=env_cls,
            oid=uuid.uuid4().hex if env_id is None else env_id,
            host=host,
            port=port,
            max_pool_size=max_pool_size,
            max_timeout_seconds=max_timeout_seconds,
            local_mode=local_mode,
            connect_existing=connect_existing,
            configs=env_configs,
        )

    @property
    def name(self) -> str:
        return self._name

    def get_parent(self) -> Env:
        return self._call_rpc_func("get_parent", {})

    def set_parent(self, parent: Env) -> None:
        return self._call_rpc_func(
            "get_parent",
            {
                "kwargs": {
                    "parent": parent,
                },
            },
        )

    def get_children(self) -> dict[str, Env]:
        return self._call_rpc_func("get_children", {})

    def add_child(self, child: Env) -> bool:
        return self._call_rpc_func(
            "add_child",
            {
                "kwargs": {
                    "child": child,
                },
            },
        )

    def remove_child(self, children_name: str) -> bool:
        return self._call_rpc_func(
            "remove_child",
            {
                "kwargs": {
                    "children_name": children_name,
                },
            },
        )

    def add_listener(self, target_event: str, listener: EventListener) -> bool:
        # raise
        return self._call_rpc_func(
            "add_listener",
            {
                "kwargs": {
                    "target_event": target_event,
                    "listener": listener,
                },
            },
        )

    def remove_listener(self, target_event: str, listener_name: str) -> bool:
        return self._call_rpc_func(
            "remove_listener",
            {
                "kwargs": {
                    "target_event": target_event,
                    "listener_name": listener_name,
                },
            },
        )

    def get_listeners(self, target_event: str) -> List[EventListener]:
        raise NotImplementedError("Currently, RpcEnv not supports listener")

    def describe(self) -> str:
        return self._call_rpc_func(
            "describe",
            {},
        )

    def __getitem__(self, env_name: str) -> Env:
        return self._call_rpc_func(
            "__getitem__",
            {"kwargs": {"env_name": env_name}},
        )

    def __setitem__(self, env_name: str, env: Env) -> None:
        self._call_rpc_func(
            "__setitem__",
            {"kwargs": {"env_name": env_name}},
        )
