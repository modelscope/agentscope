# -*- coding: utf-8 -*-
from starlette.exceptions import HTTPException

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles  # New: Introduction of StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse
from starlette.types import Scope

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.exceptions.base import BaseException
from app.middleware.error_handler_middleware import base_exception_handler
from app.middleware.request_context_middleware import RequestContextMiddleware
from app.utils.json_utils import json_dumps
from typing import Any


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


class CustomJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json_dumps(content).encode("utf-8")


class SpaStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Any:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


def create_app() -> FastAPI:
    application = FastAPI(
        generate_unique_id_function=custom_generate_unique_id,
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        default_response_class=CustomJSONResponse,
    )
    if settings.all_cors_origins:
        application.add_middleware(
            CORSMiddleware,
            #             allow_origins=settings.all_cors_origins,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
    )
    application.add_exception_handler(BaseException, base_exception_handler)
    application.include_router(api_router)

    @application.on_event("startup")
    async def on_startup() -> None:
        init_db()
        # try:
        #     redis = await init_fast_api_limiter_redis()
        #     await FastAPILimiter.init(redis)
        # except Exception as e:
        #     print(f"redis init error: {str(e)}")

    return application


if __name__ == "__main__":
    import uvicorn

    app_instance = create_app()
    uvicorn.run(app_instance, host="0.0.0.0", port=8000)
