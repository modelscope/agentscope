# -*- coding: utf-8 -*-
"""The serializable class"""
import json
from typing import Any, Dict, Optional, Callable, TypeVar

T = TypeVar("T")


class SerializeField:
    """The serialize field class."""

    def __init__(
        self,
        value: T,
        serialize_fn: Optional[Callable[[T], dict]] = None,
        deserialize_fn: Optional[Callable[[T, Any], T]] = None,
    ) -> None:
        """Initialize the serialize field."""
        self.value = value

        if (serialize_fn is None and deserialize_fn is not None) or (
            serialize_fn is not None and deserialize_fn is None
        ):
            raise ValueError(
                "The serialize_fn and deserialize_fn must be both given "
                "or both not given.",
            )

        if serialize_fn is None and deserialize_fn is None:
            try:
                json.dumps(value)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"The value {value} is not JSON serializable, please"
                    f"provide the serialize_fn and deserialize_fn.",
                ) from e

        self.serialize_fn = serialize_fn
        self.deserialize_fn = deserialize_fn


class Serializable:
    """The base class for serializable objects, which supports
    automatic serialization and registration of fields."""

    def __init__(self) -> None:
        self.__fields__: set[str] = set()
        self.__serialize_configs__: Dict[str, Dict[str, Callable]] = {}

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "__fields__":
            super().__setattr__(name, value)
            return

        if isinstance(value, SerializeField):
            # Register field
            self.__fields__.add(name)
            # Register serialize/deserialize functions
            if (
                value.serialize_fn is not None
                and value.deserialize_fn is not None
            ):
                self.__serialize_configs__[name] = {
                    "serialize_fn": value.serialize_fn,
                    "deserialize_fn": value.deserialize_fn,
                }
            # Set the original value
            super().__setattr__(name, value.value)

        elif isinstance(value, Serializable):
            self.__fields__.add(name)
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        """Delete the attribute."""
        self.__fields__.remove(name)
        self.__serialize_configs__.pop(name)
        super().__delattr__(name)

    def to_dict(self) -> dict:
        """Serialize the object to a dictionary."""
        serialized_dict = {}
        for field in self.__fields__:
            value = getattr(self, field)

            if isinstance(value, Serializable):
                serialized_dict[field] = value.to_dict()
                continue

            serialize_fn = self.__serialize_configs__.get(
                field,
                {},
            ).get("serialize_fn")
            if field in self.__serialize_configs__ and serialize_fn:
                serialized_dict[field] = serialize_fn(value)
            else:
                serialized_dict[field] = value

        return serialized_dict

    def from_dict(self, serialized_dict: dict) -> None:
        """Deserialize the object from a dictionary."""
        for field in self.__fields__:
            if field in serialized_dict:
                serialized_value = serialized_dict[field]
                obj = getattr(self, field)

                # If it's a serializable object, recursively deserialize
                if isinstance(obj, Serializable):
                    obj.from_dict(serialized_value)
                    continue

                deserialize_fn = self.__serialize_configs__.get(
                    field,
                    {},
                ).get("deserialize_fn")
                if field in self.__serialize_configs__ and deserialize_fn:
                    deserialized_value = deserialize_fn(
                        obj,
                        serialized_value,
                    )
                    setattr(
                        self,
                        field,
                        deserialized_value,
                    )
                else:
                    setattr(self, field, serialized_value)
