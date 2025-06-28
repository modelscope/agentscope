# -*- coding: utf-8 -*-
"""The account related API endpoints"""

from fastapi import APIRouter

from app.schemas.response import create_response
from app.core.config import settings

router = APIRouter(prefix="/system", tags=["accounts"])


@router.get("/global-config")
def global_config() -> dict:
    """Return global config"""
    result = {
        "login_method": settings.LOGIN_METHOD,
        "upload_method": settings.UPLOAD_METHOD,
    }

    return create_response(
        code="200",
        message="Get global config successfully.",
        data=result,
    )
