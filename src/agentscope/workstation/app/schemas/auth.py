# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import EmailStr
from sqlmodel import SQLModel, Field

from ..models.field import username_field, password_field


class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    expire_in: int


class LoginRequest(SQLModel):
    username: str = username_field()
    password: str = password_field()


class RegisterAccountRequest(SQLModel):
    """The request model used to register a new account."""

    password: str = password_field()
    username: str = username_field()
    email: Optional[EmailStr] = Field(default=None, nullable=True)
    nickname: Optional[str] = Field(default=None, nullable=True)
