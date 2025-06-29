# -*- coding: utf-8 -*-
from fastapi import APIRouter
from fastapi import Response

from app.schemas.response import create_response

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Health check."""
    return create_response(
        code="200",
        message="Health check successfully.",
    )
