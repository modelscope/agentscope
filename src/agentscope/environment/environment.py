# -*- coding: utf-8 -*-
"""The enviromnent interface of AgentScope."""
from __future__ import annotations
from typing import List
from .attribute import Attribute


class Environment:
    """Environment class."""

    def __init__(self, name: str, attrs: List[Attribute]) -> None:
        self._name = name
        self._attrs = {attr.name: attr for attr in attrs}

    # def add_attribute(
    #     self, attribute: Attribute, path: List[str] = None
    # ) -> bool:
    #     """Add a attribute to environment."""
    #     if path is None or len(path) == 0:
    #         self._attrs[attribute.name] = attribute

    # def remove_attribute(self, path: str) -> bool:
    #     """Remove an attribute from environment."""
