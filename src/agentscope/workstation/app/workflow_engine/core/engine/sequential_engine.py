# -*- coding: utf-8 -*-
"""Sequential Execution Engine"""
# pylint: disable=too-many-branches, too-many-statements
import random
import time
import traceback
from typing import Generator, Any, List, Dict, Optional

from .base_engine import BaseExecutionEngine
from ..status import Status
from ..event import (
    Event,
    SuccessEvent,
    StopEvent,
    RetryEvent,
    NormalEvent,
    FallbackEvent,
    FailureEvent,
)


class SequentialExecutionEngine(BaseExecutionEngine):
    """Sequential Execution Engine"""

    def run(
        self,
        sorted_nodes: List[str],
        messages: List[Any],
        run_mode: str = "complete",
        inter_results: Optional[Dict] = None,
        usage_tracker: Optional[Any] = None,
    ) -> Generator:
        """
        Method to run the execution engine sequentially.
        """
        inter_results = self.restore_node_results(inter_results, messages)
        self.graph_cache = inter_results

        for node_id in sorted_nodes:
            for _ in self._exec_node(node_id, usage_tracker):
                yield (
                    node_id,
                    self.graph.nodes[node_id]["opt"].node_type,
                    self.graph_cache.get(node_id, {}),
                    sorted_nodes,
                    self.stop_sign,
                )
                if isinstance(self.stop_sign, StopEvent):
                    break

    def _exec_node(
        self,
        node_id: str,
        usage_tracker: Optional[Any] = None,
        event: Optional[Event] = None,
    ) -> Generator:
        """
        Node execution function.
        """
        opt = self.graph.nodes[node_id]["opt"]
        inputs = self.get_input_from_cache(node_id)

        # Clear node status
        self.clear_node_value(node_id)

        # Handle Skip Signal
        if inputs == Status.SKIP.value:
            self.handle_node_finished(
                node_id,
                status=Status.SKIP.value,
                message="Skip",
            )
            yield
            return

        gen = opt(
            inputs=inputs,
            global_cache=self.graph_cache,
            usage_tracker=usage_tracker,
            event=event,
            graph=self.graph,
        )

        try:
            while True:
                if isinstance(self.stop_sign, StopEvent):
                    break

                if self.check_if_remote_canceled():
                    self.handle_node_finished(
                        node_id,
                        status=Status.CANCELED.value,
                        message="Remote canceled",
                    )
                    break

                event = next(gen)

                # Handle event
                if isinstance(event, RetryEvent):
                    self.retry_counts[node_id] = (
                        self.retry_counts.get(
                            node_id,
                            0,
                        )
                        + 1
                    )
                    if self.retry_counts[node_id] < self.default_node_retry:
                        time.sleep(
                            self.default_retry_interval + random.uniform(0, 1),
                        )
                    else:
                        event = FallbackEvent(
                            message=event.message,
                            context=event.context,
                        )
                    yield from self._exec_node(
                        node_id,
                        usage_tracker,
                        event,
                    )
                    return
                elif isinstance(event, FallbackEvent):
                    yield from self._exec_node(
                        node_id,
                        usage_tracker,
                        event,
                    )
                    return
                elif isinstance(event, NormalEvent):
                    self.save_node_results(
                        result=event.context,
                        node_id=node_id,
                        status=Status.RUNNING.value,
                    )
                elif isinstance(event, SuccessEvent):
                    self.handle_node_finished(
                        node_id,
                        status=Status.SUCCEEDED.value,
                    )
                    # Set event to global
                    self.stop_sign = event
                elif isinstance(event, Event):
                    # For Unknown event and FailureEvent
                    self.handle_node_finished(
                        node_id,
                        status=Status.FAILED.value,
                        message=event.message,
                    )
                    # Set event to global
                    self.stop_sign = event
                else:
                    err_message = f"Unknown Output from {node_id}: {event}"
                    self.handle_node_finished(
                        node_id,
                        status=Status.FAILED.value,
                        message=err_message,
                    )
                    self.stop_sign = FailureEvent(message=err_message)
                yield

        except StopIteration:
            self.handle_node_finished(node_id, Status.SUCCEEDED.value)
            yield
        except Exception as e:
            err_message = (
                f"Unknown error from {node_id}: "
                f"{e}\n{traceback.format_exc()}"
            )
            self.handle_node_finished(
                node_id,
                status=Status.FAILED.value,
                message=err_message,
            )
            self.stop_sign = FailureEvent(message=err_message)
            yield
