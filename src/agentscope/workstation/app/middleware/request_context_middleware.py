# -*- coding: utf-8 -*-
import time
from typing import Callable, Any
from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.request_context import RequestContext, request_context_var


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        if request.method in ["OPTIONS"]:
            return await call_next(request)

        request_context = RequestContext.from_request(request)
        request_context_var.set(request_context)

        start_time = time.time()
        context = {
            "method": request.method,
            "path": request.url.path,
        }

        logger.info("Request started.", context=context)

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(
                f"Request finished in {process_time:.3f}s",
                context=context,
            )
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}", exc_info=True)
            raise
