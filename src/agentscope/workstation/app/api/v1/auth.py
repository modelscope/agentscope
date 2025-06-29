# -*- coding: utf-8 -*-

import uuid
from typing import Dict

from fastapi import APIRouter

from app.api.deps import SessionDep, CurrentAccount
from app.schemas.auth import (
    LoginRequest,
)
from app.schemas.response import create_response
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
)
async def login(
    session: SessionDep,
    request: LoginRequest,
) -> dict:
    """Login a user with username and password."""
    auth_service = AuthService(session=session)
    account = auth_service.authenticate(
        username=request.username,
        password=request.password,
    )
    token = auth_service.get_jwt_token(
        account_id=account.account_id,
    )

    return create_response(
        code="200",
        message="Login successfully",
        data=token,
    )


@router.post(
    "/refresh-token",
)
async def refresh_access_token(
    session: SessionDep,
    refresh_token_dict: Dict[str, str],
) -> dict:
    """Refresh the token."""
    auth_service = AuthService(session=session)
    token = auth_service.refresh_token(
        refresh_token=refresh_token_dict["refresh_token"],
    )
    return create_response(
        code="200",
        message="Refresh token successfully",
        data=token,
    )


# @router.post("/register")
# def register(session: SessionDep, request: RegisterAccountRequest) -> dict:
#     """Register a new user."""
#     auth_service = AuthService(session=session)
#     account = auth_service.create_account(
#         email=request.email,
#         password=request.password,
#         username=request.username,
#     )
#     return create_response(
#         code = "200",
#         message="Register account successfully.",
#         data = AccountInfo.model_validate(account)
#     )


@router.put(
    "/logout",
)
async def logout(
    current_account: CurrentAccount,
    session: SessionDep,
) -> dict:
    """Logout"""

    return create_response(
        code="200",
        message="Logout successfully",
    )
