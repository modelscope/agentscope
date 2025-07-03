# -*- coding: utf-8 -*-
"""Account schema"""
from typing import Optional, List

from pydantic import EmailStr
from sqlmodel import SQLModel, Field

from app.models.field import password_field, username_field
from app.models.account import AccountBase


class AddAccountRequest(SQLModel):
    """The request model used to register a new account."""

    password: str = Field(default=None, nullable=True)
    username: str = username_field()
    email: Optional[EmailStr] = Field(default=None, nullable=True)


class UpdateAccountRequest(SQLModel):
    """The request model used to update a account."""

    email: Optional[EmailStr] = Field(default=None, nullable=True)
    username: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        nullable=True,
    )
    password: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=40,
        nullable=True,
    )


# Properties to receive via API on update, all are optional
class ChangePasswordRequest(SQLModel):
    """The request model used to update a account."""

    password: Optional[str] = password_field()
    new_password: Optional[str] = password_field()


class AccountInfo(AccountBase):
    """The response model used to return account information."""

    id: int
    has_password: bool = False


class PageAccountInfo(SQLModel):
    """The response model used to return account information."""

    current: int
    size: int
    total: int
    records: List[AccountInfo]
