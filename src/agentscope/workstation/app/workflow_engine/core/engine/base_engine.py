# -*- coding: utf-8 -*-
"""
This module defines the BaseExecutionEngine class, which serves as an
abstract base class for execution engines handling the execution of nodes in a
directed acyclic graph (DAG).
"""
import queue

from typing import Generator, Any, List, Dict, Optional, Union
from abc import ABC, abstractmethod

import networkx as nx

from ..node_caches.node_cache_handler import NodeCacheHandler
from ..event import NormalEvent
from ..utils.logger_adapter import LoggerAdapter
from ..constant import DEFAULT_NODE_RETRY, DEFAULT_RETRY_INTERVAL


class BaseExecutionEngine(ABC):
    """
    Abstract base class for execution engines.
    """

    default_node_retry = DEFAULT_NODE_RETRY
    default_retry_interval = DEFAULT_RETRY_INTERVAL

    def __init__(
        self,
        graph: nx.DiGraph,
        node_cache_handler: NodeCacheHandler,
        logger: Any = None,
        request_id: str = None,
    ):
        """
        Initialize the ExecutionEngine with a graph, message handler,
        and optional request ID.
        """
        self.graph = graph
        self.node_cache_handler = node_cache_handler
        self.logger = LoggerAdapter(logger=logger)
        self.request_id = request_id
        self.update_queue = queue.Queue()
        self.stopped_nodes = set()
        self.node_events = {}
        self.stop_sign = NormalEvent()
        # TODO: handle sys.query ....
        self.input_messages = []
        self.retry_counts = {}
        self.graph_cache = {}

    @abstractmethod
    def run(
        self,
        sorted_nodes: List[str],
        messages: List[Any],
        run_mode: str = "complete",
        inter_results: Optional[Dict] = None,
        usage_tracker: Optional[Any] = None,
    ) -> Generator:
        """
        Abstract method to run the execution engine. Subclasses must
        implement this method to define the specific execution logic.
        """

    def handle_node_finished(
        self,
        node_id: str,
        status: str,
        message: Optional[str] = None,
    ) -> None:
        """
        Handle the completion of a node by updating its status and message.
        """
        if node_id not in self.graph_cache:
            self.graph_cache[
                node_id
            ] = self.node_cache_handler.create_node_cache(
                status,
                message,
            )
        else:
            self.node_cache_handler.update_status(
                self.graph_cache[node_id],
                status,
            )

        if message:
            self.node_cache_handler.update_message(
                self.graph_cache[node_id],
                message,
            )

    def clear_node_value(self, node_id: str) -> None:
        """
        Clear any state associated with a node before retrying execution.
        """
        self.graph_cache.pop(node_id, None)

    def check_if_remote_canceled(self) -> bool:
        """
        Check if the execution has been remotely canceled.
        """
        try:
            r = {}  # TODO: Placeholder for redis
            remote_status = r.get(self.request_id)
            if remote_status == b"cancel":
                return True
        except Exception:
            pass
        return False

    def get_input_from_cache(self, node_id: str) -> Optional[Union[str, Dict]]:
        """
        Retrieve input data for a node from the cache.
        """
        return self.node_cache_handler.retrieve_node_input(
            node_id=node_id,
            global_cache=self.graph_cache,
            graph=self.graph,
        )

    def save_node_results(
        self,
        result: Dict,
        node_id: str,
        status: str = None,
    ) -> None:
        """
        Format the output results for a node and save to cache.
        """
        self.graph_cache[
            node_id
        ] = self.node_cache_handler.convert_node_result_to_cache(
            result,
            node_id,
            status,
            self.graph,
        )

    def restore_node_results(
        self,
        results: Optional[Dict] = None,
        messages: Optional[List] = None,
    ) -> Dict:
        """
        Restore results for nodes from a given results dictionary.
        """
        if results is None:
            results = {}
        return self.node_cache_handler.restore_node_results(results, messages)
