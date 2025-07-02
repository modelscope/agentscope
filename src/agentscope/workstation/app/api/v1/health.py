# -*- coding: utf-8 -*-
"""Health"""
from fastapi import APIRouter

from app.schemas.response import create_response

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Health check."""
    return create_response(
        code="200",
        message="Health check successfully.",
    )
