# -*- coding: utf-8 -*-
"""Graph builder."""
from typing import Any, Dict, Optional

import networkx as nx
from ..utils.error import WorkflowGraphError

from ..utils.logger_adapter import LoggerAdapter


class BaseGraphBuilder:
    """Graph builder."""

    def __init__(
        self,
        config: Dict,
        logger: Any = None,
        request_id: Optional[str] = None,
        mock: bool = False,
    ):
        """
        Initialize the BaseGraphBuilder with a configuration, request ID,
        and mock flag.

        Args:
            config (Dict): The configuration to build the graph from.
            request_id (str): The request ID for logging.
            mock (bool): Flag indicating if this is a mock execution.
        """
        self.config = config
        self.request_id = request_id
        self.mock = mock
        self.graph = nx.MultiDiGraph()  # Allow redundant edges
        self.logger = LoggerAdapter(logger=logger)
        self._build()

    def _build(self) -> nx.DiGraph:
        """Build and return the graph."""
        self._add_nodes()
        self._add_edges()
        self._verify_graph()
        self._log_graph_info()
        return self.graph

    def _add_nodes(self) -> None:
        """Add nodes to the graph based on the configuration."""
        raise NotImplementedError("Subclasses should implement this method")

    def _add_edges(self) -> None:
        """Add edges between nodes as specified in the config."""
        raise NotImplementedError("Subclasses should implement this method")

    def _verify_graph(self) -> None:
        """Verify the constructed graph for validity."""
        if not nx.is_directed_acyclic_graph(self.graph):
            message = "The provided configuration does not form a DAG."
            self._log_error(message)
            raise WorkflowGraphError(message=message)

    def _log_error(self, message: str) -> None:
        """Log an error message with configuration context."""
        self.logger.query_error(
            request_id=self.request_id,
            message=message,
            context={"config": self.config},
        )

    def _log_graph_info(self) -> None:
        """Log information about the constructed graph."""
        self.logger.query_info(
            request_id=self.request_id,
            context={
                "graph info": f"\nNodes: {self.graph.nodes}\nEdges:"
                f" {self.graph.edges}",
            },
        )

    def get_graph(self) -> nx.DiGraph:
        """Return the internal graph object."""
        return self.graph
