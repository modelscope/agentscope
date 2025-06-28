# -*- coding: utf-8 -*-
"""The API response base model."""

from app.utils.request_context import request_context_var
from typing import Any, Optional


def create_response(
    data: Any = None,
    code: str = "200",
    message: str = "success",
) -> dict:
    return {
        "code": code,
        "message": message,
        "data": data,
        "request_id": request_context_var.get().request_id,
    }


def create_success_response(
    data: Any = None,
    code: str = "200",
    message: str = "success",
) -> dict:
    return {
        "success": True,
        "code": code,
        "message": message,
        "data": data,
        "request_id": request_context_var.get().request_id,
    }


def mcp_response(
    data: Any = None,
    code: str = "200",
    message: str = "success",
    request_id: Optional[str] = None,
    success: bool = True,
) -> dict:
    request_id = (
        request_id
        if request_id is not None
        else request_context_var.get().request_id
    )
    return {
        "success": success,
        "code": code,
        "message": message,
        "request_id": request_id,
        "data": data,
    }
