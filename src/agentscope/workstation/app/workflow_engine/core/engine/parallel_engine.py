# -*- coding: utf-8 -*-
"""
This module defines the ParallelExecutionEngine class, which serves as an
class for execution engines handling the parallel execution of nodes in a
directed acyclic graph (DAG).
"""
# mypy: disable-error-code=index

import traceback
import queue
import threading
import time
from typing import Generator, Any, List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from ..engine.sequential_engine import SequentialExecutionEngine
from ..status import Status
from ..event import (
    Event,
    StopEvent,
)


class ParallelExecutionEngine(SequentialExecutionEngine):
    """
    This class defines the ParallelExecutionEngine class, which serves as a
    class for execution engines handling the parallel execution of nodes in a
    directed acyclic graph (DAG).
    """

    def run(
        self,
        sorted_nodes: List[str],
        messages: List[Any],
        run_mode: str = "complete",
        inter_results: Optional[Dict] = None,
        usage_tracker: Optional[Any] = None,
        max_pool_workers: Optional[int] = None,
    ) -> Generator:
        """
        Method to run the execution engine parallely.
        """
        inter_results = self.restore_node_results(inter_results, messages)
        self.graph_cache = inter_results
        self.node_events = {node: threading.Event() for node in sorted_nodes}

        max_workers = len(sorted_nodes)
        if max_pool_workers:
            max_workers = min(max_workers, max_pool_workers)

        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for node_id in sorted_nodes:
                futures.append(
                    executor.submit(
                        self._thread_exec_node,
                        node_id,
                        usage_tracker,
                    ),
                )

            while True:
                try:
                    updated_node_id = self.update_queue.get_nowait()
                    yield (
                        updated_node_id,
                        self.graph.nodes[updated_node_id]["opt"].node_type,
                        self.graph_cache[updated_node_id],
                        self.stop_sign,
                    )
                except queue.Empty:
                    all_tasks_done = all(f.done() for f in futures)

                    # TODO: remove debug
                    for future in futures:
                        if future.done() and future.exception() is not None:
                            exception = future.exception()
                            print(f"Exception in thread: {exception}")
                            traceback_str = "".join(
                                traceback.format_exception(
                                    None,
                                    exception,
                                    exception.__traceback__,
                                ),
                            )
                            print(traceback_str)

                    if isinstance(self.stop_sign, StopEvent) or all_tasks_done:
                        for event in self.node_events.values():
                            event.set()
                        return
                    else:
                        time.sleep(0.01)

    def _thread_exec_node(
        self,
        node_id: str,
        usage_tracker: Optional[Any] = None,
        event: Optional[Event] = None,
    ) -> None:
        """
        Node thread execution function.
        """

        for predecessor in self.graph.predecessors(node_id):
            if predecessor in self.node_events.keys():
                while not self.node_events[predecessor].wait(timeout=1):
                    if isinstance(self.stop_sign, StopEvent):
                        self.node_events[node_id].set()
                        return

                    if self.check_if_remote_canceled():
                        self.handle_node_finished(
                            node_id,
                            status=Status.CANCELED.value,
                            message="Remote canceled",
                        )
                        self.update_queue.put(node_id)
                        self.node_events[node_id].set()
                        return

        generator = self._exec_node(node_id, usage_tracker, event)
        for _ in generator:
            self.update_queue.put(node_id)

        self.node_events[node_id].set()
