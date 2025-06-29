# -*- coding: utf-8 -*-
"""The base exceptions"""

from typing import Optional, Union


class BaseException(Exception):
    """The base exception"""

    code: Optional[int] = None
    message: Optional[str] = None

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[int] = None,
        extra_info: Optional[Union[str, dict, list]] = None,
    ) -> None:
        """Initialize the base exception"""
        self.message = message or self.message
        if extra_info:
            self.message = f"{self.message}: {extra_info}"
        self.code = self.code if code is None else code
        super().__init__(message)

    def __str__(self) -> str:
        return self.message or self.__class__.__name__


class InternalServerError(BaseException):
    """The internal server error"""

    code = 500
    message = "Internal server error"


class NotFoundException(BaseException):
    """The not found exception"""

    code = 404
    message = "Not found"


class AlreadyExistsException(BaseException):
    """The already exists exception"""

    code = 409
    message = "Already exists"


class AccessDeniedException(BaseException):
    """The access denied exception"""

    code = 403
    message = "Access denied"


class PermissionDeniedException(BaseException):
    """The permission denied exception"""

    code = 403
    message = "Permission denied"


class IncorrectParameterException(BaseException):
    """The incorrect parameter exception"""

    code = 400
    message = "Incorrect parameter"


class InvalidException(BaseException):
    """The invalid exception"""

    code = 400
    message = "Invalid"


class ValidationError(BaseException):
    """The validation error"""

    code = 400
    message = "Validation error"


class NotSetException(BaseException):
    """The not set exception"""

    code = 400
    message = "Not set"
