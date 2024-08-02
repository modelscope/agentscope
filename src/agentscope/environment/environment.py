# -*- coding: utf-8 -*-
"""The enviromnent interface of AgentScope."""
from __future__ import annotations
from typing import List, Any, Union


from .attribute import Attribute
from ..exception import (
    EnvAttributeUnsupportedFunctionError,
)


class Environment:
    """Base Environment class."""

    def __init__(
        self,
        name: str,
        attrs: Union[Attribute, List[Attribute]],
    ) -> None:
        self._name = name
        if isinstance(attrs, Attribute):
            attrs = [attrs]
        self._attrs = {attr.name: attr for attr in attrs}

    def add_attr(self, attr: Attribute) -> bool:
        """Add an attribute to the environment."""
        if attr.name in self._attrs:
            return False
        self._attrs[attr.name] = attr
        return True

    def remove_attr(self, attr_name: str) -> bool:
        """Remove an attribute from the environment."""
        if attr_name not in self._attrs:
            return False
        del self._attrs[attr_name]
        return True

    def _get_attribute(self, path: Union[str, List[str]]) -> Attribute:
        """get the attribute with the path."""
        if isinstance(path, list):
            if len(path) == 0:
                raise ValueError("path cannot be empty")
            attribute = self._attrs[path[0]]
            for i in range(1, len(path)):
                attribute = attribute[path[i]]
            return attribute
        else:
            return self._attrs[path]

    def get(self, name: Union[str, List[str]]) -> Any:
        """Get the value of an attribute."""
        attr = self._get_attribute(name)
        if not hasattr(attr, "get"):
            raise EnvAttributeUnsupportedFunctionError(attr.name, "get")
        return attr.get()

    def set(self, name: Union[str, List[str]], value: Any) -> bool:
        """Set the value of an attribute."""
        attr = self._get_attribute(name)
        if not hasattr(attr, "set"):
            raise EnvAttributeUnsupportedFunctionError(attr.name, "set")
        return attr.set(value)
