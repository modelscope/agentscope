# -*- coding: utf-8 -*-
"""Router"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.account import router as account_router
from app.api.v1.health import router as health_router
from app.api.v1.file import router as file_router
from app.api.v1.workflow import router as workflow_router
from app.api.v1.knowledge_base import router as knowledge_base_router
from app.api.v1.app import router as app_router
from app.api.v1.provider import router as provider_router
from app.api.v1.mcp import router as mcp_router
from app.api.v1.api_key import router as api_key_router
from app.api.v1.chat import router as agent_router
from app.api.v1.model import router as model_router
from app.api.v1.system import router as system_router
from app.core.config import settings


api_router = APIRouter(prefix=settings.API_V1_STR)

api_router.include_router(auth_router)
api_router.include_router(account_router)
api_router.include_router(health_router)
api_router.include_router(file_router)
api_router.include_router(workflow_router)
api_router.include_router(knowledge_base_router)
api_router.include_router(app_router)
api_router.include_router(knowledge_base_router)
api_router.include_router(provider_router)
api_router.include_router(mcp_router)
api_router.include_router(api_key_router)
api_router.include_router(agent_router)
api_router.include_router(model_router)
api_router.include_router(system_router)
