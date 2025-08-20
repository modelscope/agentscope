# -*- coding: utf-8 -*-
"""
This module provides a LoggerAdapter class for enhanced logging capabilities.
"""
import logging
import inspect

from typing import Any, Optional


class LoggerAdapter:
    """
    This module provides a LoggerAdapter class for enhanced logging
    capabilities.
    """

    def __init__(self, logger: Optional[Any] = None):
        self.logger = logger or logging.getLogger(__name__)

    def _format_additional_kwargs(
        self,
        exclude_keys: set,
        **kwargs: Any,
    ) -> str:
        """
        Log additional kwargs.
        """
        # Exclude known keys and format the remaining ones
        additional_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key not in exclude_keys
        }
        return ", ".join(
            f"{key}={value}" for key, value in additional_kwargs.items()
        )

    def _log_with_inspection(self, log_func_name: str, **kwargs: Any) -> None:
        """
        Use inspection to log.
        """
        log_func = getattr(self.logger, log_func_name, None)
        if not log_func:
            raise AttributeError(
                f"{self.logger} does not have a method named {log_func_name}",
            )

        # Use inspect to find the parameters in the logger function
        sig = inspect.signature(log_func)
        func_params = sig.parameters

        # Extract known keys based on the logger function's parameters
        known_keys = set(func_params.keys())
        provided_kwargs = {
            key: kwargs[key] for key in known_keys if key in kwargs
        }

        # Format additional kwargs
        additional_message = self._format_additional_kwargs(
            known_keys,
            **kwargs,
        )
        if additional_message:
            msg = (
                f"{provided_kwargs.get('message', '')} | {additional_message}"
            )
            log_func(msg, **provided_kwargs)
        else:
            log_func(**provided_kwargs)

    def query_info(self, **kwargs: Any) -> None:
        """
        Logs an informational message using inspection to match method
        parameters.
        """
        if hasattr(self.logger, "query_info"):
            self._log_with_inspection("query_info", **kwargs)
        else:
            self._log_with_inspection("info", **kwargs)

    def query_error(self, **kwargs: Any) -> None:
        """
        Logs an error message using inspection to match method parameters.
        """
        if hasattr(self.logger, "query_error"):
            self._log_with_inspection("query_error", **kwargs)
        else:
            self._log_with_inspection("error", **kwargs)
