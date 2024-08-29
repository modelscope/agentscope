# -*- coding: utf-8 -*-
""" Meta class for all classes that can run on rpc server."""

from abc import ABCMeta
from typing import Any
import uuid
from loguru import logger

from .rpc_object import RpcObject


def generate_oid() -> str:
    """Generate a unique id"""
    return uuid.uuid4().hex


class RpcMeta(ABCMeta):
    """The metaclass for all classes that can run on rpc server."""

    _REGISTRY = {}

    def __init__(cls, name: Any, bases: Any, attrs: Any) -> None:
        if name in RpcMeta._REGISTRY:
            logger.warning(f"Class with name [{name}] already exists.")
        else:
            RpcMeta._REGISTRY[name] = cls
        super().__init__(name, bases, attrs)

    def __new__(mcs: type, name: Any, bases: Any, attrs: Any) -> Any:
        attrs["to_dist"] = RpcMeta.to_dist
        return super().__new__(mcs, name, bases, attrs)  # type: ignore[misc]

    def __call__(cls, *args: tuple, **kwargs: dict) -> Any:
        to_dist = kwargs.pop("to_dist", False)
        if to_dist is True:
            to_dist = {}
        if to_dist is not False and to_dist is not None:
            if cls is not RpcObject:
                return RpcObject(
                    cls=cls,
                    oid=generate_oid(),
                    host=to_dist.pop(  # type: ignore[arg-type]
                        "host",
                        "localhost",
                    ),
                    port=to_dist.pop("port", None),  # type: ignore[arg-type]
                    max_pool_size=kwargs.pop(  # type: ignore[arg-type]
                        "max_pool_size",
                        8192,
                    ),
                    max_timeout_seconds=to_dist.pop(  # type: ignore[arg-type]
                        "max_timeout_seconds",
                        7200,
                    ),
                    local_mode=to_dist.pop(  # type: ignore[arg-type]
                        "local_mode",
                        True,
                    ),
                    connect_existing=False,
                    configs={
                        "args": args,
                        "kwargs": kwargs,
                        "class_name": cls.__name__,
                    },
                )
        instance = super().__call__(*args, **kwargs)
        instance._init_settings = {
            "args": args,
            "kwargs": kwargs,
            "class_name": cls.__name__,
        }
        instance._oid = generate_oid()
        return instance

    @staticmethod
    def get_class(cls_name: str) -> Any:
        """Get the class based on the specific class name.

        Args:
            cls_name (`str`): the name of the class.

        Raises:
            ValueError: class name not exits.

        Returns:
            Any: the class
        """
        if cls_name not in RpcMeta._REGISTRY:
            raise ValueError(f"Class <{cls_name}> not found.")
        return RpcMeta._REGISTRY[cls_name]  # type: ignore[return-value]

    @staticmethod
    def register_class(cls: type) -> bool:  # pylint: disable=W0211
        """Register the class into the registry.

        Args:
            cls (`Type`): the class to be registered.

        Returns:

            `bool`: whether the registration is successful.
        """
        cls_name = cls.__name__
        if cls_name in RpcMeta._REGISTRY:
            logger.info(
                f"Class with name [{cls_name}] already exists.",
            )
            return False
        else:
            RpcMeta._REGISTRY[cls_name] = cls
            return True

    @staticmethod
    def to_dist(  # pylint: disable=W0211
        self: Any,
        host: str = "localhost",
        port: int = None,
        max_pool_size: int = 8192,
        max_timeout_seconds: int = 7200,
        local_mode: bool = True,
    ) -> Any:
        """Convert current object into its distributed version.

        Args:
            host (`str`, defaults to `"localhost"`):
                Hostname of the rpc agent server.
            port (`int`, defaults to `None`):
                Port of the rpc agent server.
            max_pool_size (`int`, defaults to `8192`):
                Only takes effect when `host` and `port` are not filled in.
                The max number of agent reply messages that the started agent
                server can accommodate. Note that the oldest message will be
                deleted after exceeding the pool size.
            max_timeout_seconds (`int`, defaults to `7200`):
                Only takes effect when `host` and `port` are not filled in.
                Maximum time for reply messages to be cached in the launched
                agent server. Note that expired messages will be deleted.
            local_mode (`bool`, defaults to `True`):
                Only takes effect when `host` and `port` are not filled in.
                Whether the started agent server only listens to local
                requests.

        Returns:
            `RpcObject`: the wrapped agent instance with distributed
            functionality
        """

        if isinstance(self, RpcObject):
            return self
        return RpcObject(
            cls=self.__class__,
            host=host,
            port=port,
            configs=self._init_settings,
            oid=self._oid,
            max_pool_size=max_pool_size,
            max_timeout_seconds=max_timeout_seconds,
            local_mode=local_mode,
        )
