# -*- coding: utf-8 -*-
"""
This module defines an abstract base class for message handling in a
workflow system.
"""
import json
from collections import defaultdict
from typing import Any, Optional, Dict, List, Union
from abc import ABC, abstractmethod


class NodeCache(defaultdict):
    """
    NodeCache is a specialized dictionary subclass that stores information
    related to nodes. It supports key attributes like 'results', 'node_id',
    'status', and 'message'.

    Attributes:
        results (Any): The results associated with the node.
        node_id (Optional[str]): The unique identifier for the node.
        status (Optional[str]): The status of the node.
        message (Optional[str]): A message related to the node.
    """

    _VALID_KEYS = ["results", "node_id", "status", "message"]

    def __init__(
        self,
        results: Any = None,
        node_id: Optional[str] = None,
        status: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        super().__init__(lambda: None)
        initial_values = {
            "results": results,
            "node_id": node_id,
            "status": status,
            "message": message,
        }

        self.update(**initial_values)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._VALID_KEYS:
            self[name] = value
        else:
            raise AttributeError(
                f"{name} is not a valid attribute of NodeCache",
            )

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(
                f"'NodeCache' object has no attribute '{name}'",
            ) from exc

    def __repr__(self) -> str:
        return json.dumps(self, ensure_ascii=False)


class NodeCacheHandler(ABC):
    """
    An abstract base class that defines the interface for handling messages
    in a workflow system.
    """

    @abstractmethod
    def create_node_cache(
        self,
        status: str,
        message_str: Optional[str] = None,
    ) -> NodeCache:
        """
        Create a node_cache with the given status and optional message string.
        """

    @abstractmethod
    def update_status(self, node_cache: NodeCache, status: str) -> None:
        """
        Update the status of a given node_cache.
        """

    @abstractmethod
    def update_message(
        self,
        node_cache: NodeCache,
        message_str: str,
    ) -> None:
        """
        Update the message string of a given node_cache.
        """

    @abstractmethod
    def convert_node_result_to_cache(
        self,
        result: Dict,
        node_id: str,
        status: str,
        graph: Any,
    ) -> Dict:
        """
        Format the output results for nodes.
        """

    @abstractmethod
    def restore_node_results(
        self,
        results: Dict,
        messages: Optional[List] = None,
    ) -> Dict:
        """
        Restore and return the node results from given results dictionary.
        """

    @staticmethod
    @abstractmethod
    def retrieve_node_input(
        node_id: str,
        global_cache: Dict,
        graph: Any,
    ) -> Optional[Union[str, Dict]]:
        """
        Retrieve the input for a specific node from the global cache.
        """
