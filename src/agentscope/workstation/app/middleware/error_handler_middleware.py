# -*- coding: utf-8 -*-
from fastapi.responses import JSONResponse
from fastapi import Request
from app.exceptions.base import BaseException


async def base_exception_handler(
    request: Request,
    exc: BaseException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )
