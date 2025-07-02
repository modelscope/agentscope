# -*- coding: utf-8 -*-
"""The auth related services"""
import uuid
from typing import Optional, Union
from datetime import datetime, timedelta, timezone
from sqlmodel import Session
from app.core.config import settings
from app.exceptions.service import (
    IncorrectPasswordException,
    UserNotFoundException,
)
from app.models.account import Account
from app.schemas.auth import TokenResponse
from app.services.jwt_service import JwtService
from app.services.account_service import AccountService
from app.utils.security import (
    verify_password,
)


class AuthService:
    """Service layer for login."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        """Initialize the service layer for login."""
        self.account_service = AccountService(
            session=session,
        )

    def authenticate(self, username: str, password: str) -> Optional[Account]:
        """Authenticate the account by username and password."""
        account = self.account_service.get_account_by_username(
            username=username,
        )
        if not account:
            raise UserNotFoundException(extra_info={"username": username})
        if not verify_password(password, account.password):
            raise IncorrectPasswordException()
        account = self.account_service.update_last_login_info(
            id=account.id,
        )
        return account

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh the jwt token by refresh token."""
        account = self.get_account_by_token(refresh_token)
        return self.get_jwt_token(account_id=account.account_id)

    def get_jwt_token(
        self,
        account_id: Union[str, uuid.UUID],
    ) -> TokenResponse:
        """Get the jwt token by account id."""
        expire_time = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        access_payload = {
            "exp": expire_time,
            "account_id": str(account_id),
        }
        access_token = JwtService().encode(access_payload)

        refresh_payload = {
            "account_id": str(account_id),
            "timestamp": str(datetime.now(timezone.utc)),
            "exp": expire_time,
        }
        refresh_token = JwtService().encode(refresh_payload)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expire_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def get_account_by_token(self, token: str) -> Account:
        """Get the account info by token."""
        payload = JwtService().decode(token)
        account_id: str = payload.get("account_id")
        account = self.account_service.get_account_by_account_id(account_id)
        if not account:
            raise UserNotFoundException(extra_info={"account_id": account_id})
        return account
