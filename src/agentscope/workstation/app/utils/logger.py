# -*- coding: utf-8 -*-
"""Logger module"""
from typing import Any
import sys
import os
from loguru import logger
from app.core.config import settings
from .request_context import request_context_var


def ensure_log_directory(log_file: str) -> None:
    """Ensure that the log directory exists."""
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def setup_logger() -> None:
    """Configure the logger with specified parameters."""
    log_file = settings.LOG_FILE
    ensure_log_directory(log_file)

    log_format = settings.LOG_FORMAT or (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level> | "
        "<magenta>{extra}</magenta>"
    )

    # Function to handle adding request_id to log records
    def request_context_filter(record: Any) -> bool:
        # Initialize 'context' dictionaries if they don't exist
        record_extra = record.setdefault("extra", {})
        context = record.setdefault("context", {})

        # Assign request_context
        request_context = request_context_var.get()
        request_context_dict = request_context.to_dict()
        record_extra.update(request_context_dict)

        # Move non-context and non-payload items to payload
        for key, value in list(record_extra.items()):
            if key not in ["context"] and key not in request_context_dict:
                context[key] = value
                del record_extra[key]

        return True

    # Remove all existing handlers
    logger.remove()

    try:
        # Add console output
        logger.add(
            sys.stdout,
            format=log_format,
            filter=request_context_filter,
            level=settings.LOG_LEVEL,
            enqueue=True,
        )

        log_retention = settings.LOG_RETENTION
        if isinstance(log_retention, str) and log_retention.isdigit():
            log_retention = int(log_retention)

        # Add file output if log file path is provided
        logger.add(
            log_file,
            format=log_format,
            filter=request_context_filter,
            level=settings.LOG_LEVEL,
            rotation=settings.LOG_ROTATION,
            retention=log_retention,
            enqueue=True,
        )
    except Exception as e:
        logger.error(f"Logger setup failed: {e}", exc_info=True)


# Configure logger when the module is imported
setup_logger()
