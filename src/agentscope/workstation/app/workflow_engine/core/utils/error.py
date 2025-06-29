# -*- coding: utf-8 -*-
"""
This module defines custom error classes used in the workflow system.
"""

SUCCESS_CODE = 200
UNKNOWN_ERROR_CODE = 500
PARSE_ERROR_CODE = 400
API_ERROR_CODE = 502
THROTTLE_ERROR_CODE = 429
MODEL_CALL_ERROR_CODE = 503
WORKFLOW_GRAPH_ERROR_CODE = 409
LOOP_BREAK_ERROR_CODE = 410
LOOP_CONTINUE_ERROR_CODE = 411
CANCEL_OPERATION_CODE = 499


class ApiError(Exception):
    """
    Represents a general API error.
    """

    def __init__(self, message: str = None, code: int = None) -> None:
        self.name = "ApiError"
        self.code = code if code is not None else API_ERROR_CODE
        self.message = message if message is not None else "Api error."
        super().__init__(self.message)


class ThrottleError(ApiError):
    """
    Represents an error due to throttling.
    """

    def __init__(self, message: str = None, code: int = None) -> None:
        super().__init__(
            message or "Throttle error.",
            code or THROTTLE_ERROR_CODE,
        )
        self.name = "ThrottleError"


class ModelCallError(ApiError):
    """
    Represents an error when calling a model.
    """

    def __init__(self, message: str = None, code: int = None) -> None:
        super().__init__(
            message or "Model call error.",
            code or MODEL_CALL_ERROR_CODE,
        )
        self.name = "ModelCallError"


class ParseError(Exception):
    """
    Represents an error during parsing operations.
    """

    def __init__(self, message: str = None, code: int = None) -> None:
        self.name = "ParseError"
        self.code = code if code is not None else PARSE_ERROR_CODE
        self.message = message if message is not None else "Parse error."
        super().__init__(self.message)


class UnknownError(Exception):
    """
    Represents an unidentified or unknown error.
    """

    def __init__(self, message: str = None, code: int = None) -> None:
        self.name = "UnknownError"
        self.code = code if code is not None else UNKNOWN_ERROR_CODE
        self.message = message if message is not None else "Unknown error."
        super().__init__(self.message)


class LoopBreakError(Exception):
    """
    Represents an error used to signal the break of a process or loop.
    """

    def __init__(self, message: str = None, code: int = None) -> None:
        self.name = "LoopBreakError"
        self.code = code if code is not None else LOOP_BREAK_ERROR_CODE
        self.message = (
            message if message is not None else "Loop break signal received."
        )
        super().__init__(self.message)


class LoopContinueError(Exception):
    """
    Represents an error used to signal to continue of a process or loop.
    """

    def __init__(self, message: str = None, code: int = None) -> None:
        self.name = "LoopContinueError"
        self.code = code if code is not None else LOOP_CONTINUE_ERROR_CODE
        self.message = (
            message
            if message is not None
            else "Loop continue signal " "received."
        )
        super().__init__(self.message)


class WorkflowGraphError(Exception):
    """
    Represents an error related to the workflow graph structure.
    """

    def __init__(self, message: str = None, code: int = None) -> None:
        self.name = "WorkflowGraphError"
        self.code = code if code is not None else WORKFLOW_GRAPH_ERROR_CODE
        self.message = (
            message
            if message is not None
            else "Workflow graph structure error."
        )
        super().__init__(self.message)


def is_workflow_error(exception: Exception) -> bool:
    """
    Checks if the provided exception is an instance of one of the custom
    error classes.
    """
    workflow_errors = (
        ApiError,
        ThrottleError,
        ModelCallError,
        ParseError,
        UnknownError,
        LoopBreakError,
        LoopContinueError,
        WorkflowGraphError,
    )
    return isinstance(exception, workflow_errors)
