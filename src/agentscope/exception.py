# -*- coding: utf-8 -*-
"""AgentScope exception classes."""

# - Model Response Parsing Exceptions


class ResponseParsingError(Exception):
    """The exception class for response parsing error with uncertain
    reasons."""

    raw_response: str
    """Record the raw response."""

    def __init__(self, message: str, raw_response: str = None) -> None:
        """Initialize the exception with the message."""
        self.message = message
        self.raw_response = raw_response

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class JsonParsingError(ResponseParsingError):
    """The exception class for JSON parsing error."""


class JsonDictValidationError(ResponseParsingError):
    """The exception class for JSON dict validation error."""


class JsonTypeError(ResponseParsingError):
    """The exception class for JSON type error."""


class RequiredFieldNotFoundError(ResponseParsingError):
    """The exception class for missing required field in model response, when
    the response is required to be a JSON dict object with required fields."""


class TagNotFoundError(ResponseParsingError):
    """The exception class for missing tagged content in model response."""

    missing_begin_tag: bool
    """If the response misses the begin tag."""

    missing_end_tag: bool
    """If the response misses the end tag."""

    def __init__(
        self,
        message: str,
        raw_response: str = None,
        missing_begin_tag: bool = True,
        missing_end_tag: bool = True,
    ):
        """Initialize the exception with the message.

        Args:
            raw_response (`str`):
                Record the raw response from the model.
            missing_begin_tag (`bool`, defaults to `True`):
                If the response misses the beginning tag, default to `True`.
            missing_end_tag (`bool`, defaults to `True`):
                If the response misses the end tag, default to `True`.
        """
        super().__init__(message, raw_response)

        self.missing_begin_tag = missing_begin_tag
        self.missing_end_tag = missing_end_tag


# - Function Calling Exceptions


class FunctionCallError(Exception):
    """The base class for exception raising during calling functions."""

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class FunctionCallFormatError(FunctionCallError):
    """The exception class for function calling format error."""


class FunctionNotFoundError(FunctionCallError):
    """The exception class for function not found error."""


class ArgumentNotFoundError(FunctionCallError):
    """The exception class for missing argument error."""


class ArgumentTypeError(FunctionCallError):
    """The exception class for argument type error."""


# - AgentScope Studio Exceptions


class StudioError(Exception):
    """The base class for exception raising during interaction with agentscope
    studio."""

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class StudioRegisterError(StudioError):
    """The exception class for error when registering to agentscope studio."""


# - Agent Server Exceptions


class AgentServerError(Exception):
    """The exception class for agent server related errors."""

    host: str
    """Hostname of the server."""
    port: int
    """Port of the server."""
    message: str
    """Error message"""

    def __init__(
        self,
        host: str,
        port: int,
        message: str = None,
    ) -> None:
        """Initialize the exception with the message."""
        self.host = host
        self.port = port
        self.message = message

    def __str__(self) -> str:
        err_msg = f"{self.__class__.__name__}[{self.host}:{self.port}]"
        if self.message is not None:
            err_msg += f": {self.message}"
        return err_msg


class AgentServerNotAliveError(AgentServerError):
    """The exception class for agent server not alive error."""


class AgentCreationError(AgentServerError):
    """The exception class for failing to create agent."""


class AgentCallError(AgentServerError):
    """The exception class for failing to call agent."""


# - Monitor related Exceptions


class QuotaExceededError(Exception):
    """An Exception used to indicate that a certain metric exceeds quota"""

    def __init__(
        self,
        name: str,
    ) -> None:
        """Init a QuotaExceedError instance.

        Args:
            name (`str`): name of the metric which exceeds quota.
        """
        self.message = f"Metric [{name}] exceeds quota."
        self.name = name
        super().__init__(self.message)
