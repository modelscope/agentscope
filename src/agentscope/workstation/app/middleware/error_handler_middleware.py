# -*- coding: utf-8 -*-
"""exception handler"""
from fastapi.responses import JSONResponse
from app.exceptions.base import BaseException  # pylint: disable=W0622


async def base_exception_handler(
    # request: Request,
    exc: BaseException,
) -> JSONResponse:
    """Base exception handler"""
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )
