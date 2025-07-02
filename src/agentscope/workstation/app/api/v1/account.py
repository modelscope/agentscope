# -*- coding: utf-8 -*-
"""The account related API endpoints"""
import uuid
from typing import Optional

from fastapi import APIRouter
from app.schemas.response import create_response
from app.schemas.common import PaginationParams
from app.api.deps import (
    CurrentSuperAccount,
    CurrentAccount,
    SessionDep,
)
from app.schemas.account import (
    AddAccountRequest,
    AccountInfo,
    ChangePasswordRequest,
    PageAccountInfo,
    UpdateAccountRequest,
)
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("")
def add_account(
    current_account: CurrentSuperAccount,
    session: SessionDep,
    request: AddAccountRequest,
) -> dict:
    """Add a new account."""
    account_service = AccountService(session=session)
    account_id = str(uuid.uuid4())
    account_service.create_account(
        account_id=account_id,
        email=request.email,
        password=request.password,
        username=request.username,
        current_account=current_account,
    )
    return create_response(
        code="200",
        message="Add account successfully.",
        data=account_id,
    )


@router.get("")
def list_accounts(
    current_account: CurrentSuperAccount,  # pylint: disable=unused-argument
    session: SessionDep,
    name: str = "",
    current: Optional[int] = 1,
    size: Optional[int] = 10,
) -> dict:
    """List accounts."""
    pagination = PaginationParams.from_pretrained(
        page=current,
        page_size=size,
    )

    account_service = AccountService(session=session)
    total, accounts = account_service.list_accounts(
        name=name,
        pagination=pagination,
    )

    return create_response(
        code="200",
        message="List accounts successfully.",
        data=PageAccountInfo(
            total=total,
            current=current,
            size=size,
            records=accounts,
        ),
    )


@router.get("/profile")
def get_profile(current_account: CurrentAccount) -> dict:
    """Get current account profile."""
    return create_response(
        code="200",
        message="Get account successfully.",
        data=current_account,
    )


@router.put("/change-password")
def change_password(
    current_account: CurrentAccount,
    session: SessionDep,
    request: ChangePasswordRequest,
) -> dict:
    """Update own account information."""
    account_service = AccountService(session=session)
    account = account_service.update_account(
        account_id=current_account.account_id,
        password=request.password,
        new_password=request.new_password,
        current_account=current_account,
    )
    return create_response(
        code="200",
        message="Update account password successfully.",
        data=AccountInfo.model_validate(account),
    )


@router.get("/{account_id}")
def get_account(
    current_account: CurrentSuperAccount,  # pylint: disable=unused-argument
    session: SessionDep,
    account_id: str,
) -> dict:
    """Get specified account."""
    account_service = AccountService(session=session)
    account = account_service.get_account_by_account_id(account_id=account_id)
    return create_response(
        code="200",
        message="Get account successfully.",
        data=account,
    )


@router.put("/{account_id}")
def update_account(
    current_account: CurrentAccount,
    session: SessionDep,
    account_id: str,
    request: UpdateAccountRequest,
) -> dict:
    """Update specified account."""
    account_service = AccountService(session=session)
    account = account_service.update_account(
        account_id=account_id,
        username=request.username,
        email=request.email,
        new_password=request.password,
        current_account=current_account,
    )
    return create_response(
        code="200",
        message="Update account successfully.",
        data=account,
    )


@router.delete("/{account_id}")
def delete_account(
    current_account: CurrentAccount,  # pylint: disable=unused-argument
    session: SessionDep,
    account_id: uuid.UUID,
) -> dict:
    """Delete own account."""
    account_service = AccountService(session=session)
    account_service.delete_account(account_id=account_id)
    return create_response(
        code="200",
        message="Delete account successfully.",
        data=account_id,
    )
