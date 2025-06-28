# -*- coding: utf-8 -*-
"""
This module defines the abstract base class WorkflowBaseNode for workflow
systems.
"""
# mypy: disable-error-code=arg-type
# pylint: disable=using-constant-test, unused-argument, using-constant-test
import traceback

from abc import ABC
from typing import Generator, Tuple, Any, Optional, Dict

from ..event import (
    Event,
    FailureEvent,
    NormalEvent,
    FallbackEvent,
    RetryEvent,
)
from ..utils.code import CodeBlock
from ..utils.logger_adapter import LoggerAdapter


class WorkflowBaseNode(ABC):
    """
    Abstract base class representing a generic node in a workflow.

    WorkflowBaseNode is designed to be subclassed with specific logic
    implemented in the subclass methods. It provides an interface for
    initialization and execution of operations when the node is called.
    """

    node_type = None
    mock_time = 0

    def __init__(
        self,
        node_id: str,
        node_kwargs: dict,
        logger: Any = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize nodes. Implement specific initialization logic in
        subclasses.
        """
        self.node_id = node_id
        self.node_name = node_kwargs.get("name", node_id)
        self.node_type = node_kwargs.get("type", "")
        self.request_id = kwargs.get("request_id", "")
        self.mock = kwargs.get("mock", False)
        self.logger = LoggerAdapter(logger=logger)

        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args: Any, **kwargs: Any) -> Generator:
        """
        Execute the node's operation.
        """
        event = kwargs.get("event")

        # Step 2: process input
        try:
            args, kwargs = self._preprocess_inputs(*args, **kwargs)
        except Exception as exc:
            yield self.error_handler(
                exception=exc,
                trace=traceback.format_exc(),
                event=event,
            )
            return

        # Step 3: determine exec mode
        if self.mock:
            # Mock mode, always exec `_mock_execute`
            execute_func = self._mock_execute
        elif isinstance(event, FallbackEvent):
            # Fallback mode
            execute_func = self._fallback_execute
        else:
            # Normal mode
            execute_func = self._execute

        # Step 4: exec node
        try:
            for msg in execute_func(*args, **kwargs):
                yield NormalEvent(context=msg)
        except Exception as exc:
            yield self.error_handler(
                exception=exc,
                trace=traceback.format_exc(),
                event=event,
            )

    def _execute(self, *args: Any, **kwargs: Any) -> Generator:
        """
        Performs the operations of the node. Implement specific logic in
        subclasses.
        """
        if False:
            yield

    def _fallback_execute(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Generator:
        """
        Performs the fallback execute.
        """
        if False:
            yield

        # Try to throw raw error
        event = kwargs.get("event")
        if isinstance(event, Event):
            error = event.context.get("error")
            if isinstance(error, type(Exception)):
                # TODO: add message to error
                self.logger.query_error(
                    request_id=self.request_id,
                    message=event.message,
                )
                raise error

        raise NotImplementedError(
            f"Fallback not implemented, last event: {kwargs.get('event')}",
        )

    def _mock_execute(self, *args: Any, **kwargs: Any) -> Generator:
        """
        Performs the mock operations of the node. Implement specific logic in
        subclasses.
        """
        if False:
            yield

    def error_handler(
        self,
        exception: Exception,
        trace: str = "",
        event: Optional[Event] = None,
        **kwargs: Any,
    ) -> Event:
        """
        Default to no error handler.
        """
        exception, should_retry = self.evaluate_exception(exception)
        event_kwargs = {
            "message": str(trace),
            "context": {
                "node_id": self.node_id,
                "node_name": self.node_name,
                "node_type": self.node_type,
                "error": exception,
            },
        }
        if isinstance(event, FallbackEvent):
            return FailureEvent(**event_kwargs)

        if should_retry:
            return RetryEvent(
                message=event_kwargs["message"],
                context=event_kwargs["context"],
            )

        return FallbackEvent(**event_kwargs)

    def evaluate_exception(
        self,
        exception: Exception,
    ) -> Tuple[Exception, bool]:
        """
        Evaluate the given exception to determine if it should be converted
        and if a retry is necessary.
        """
        return exception, False

    def _preprocess_inputs(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Tuple:
        """
        Default to no preprocess.
        """
        return args, kwargs

    def compile(self) -> Dict[str, Any]:
        """
        Compile the code string of this node into a CodeBlock. This method
        can be optionally overridden by subclasses to implement specific
        compile logic.

        Raises:
            NotImplementedError: If the subclass does not implement this
                method.
        """
        raise NotImplementedError(
            f"Compile method not implemented in {self.__class__.__name__} "
            f"with node_id={self.node_id} and node_type={self.node_type}. "
            "Subclasses should implement this method if they have specific "
            "compile logic.",
        )
