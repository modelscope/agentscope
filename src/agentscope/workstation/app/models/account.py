# -*- coding: utf-8 -*-
"""account model"""
from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Column, Integer
from sqlmodel import Field, SQLModel

from .field import email_field, username_field


# Shared properties
class AccountBase(SQLModel):
    """The base model used to represent a account."""

    account_id: str = Field(max_length=64, unique=True, index=True)
    username: str = username_field()
    email: Optional[EmailStr] = email_field()
    icon: Optional[str] = Field(default=None, max_length=255)
    type: str = Field(max_length=64)  # basic, admin
    status: int = Field(default=1)  # 0- deleted, 1- normal
    gmt_create: datetime = Field(default_factory=datetime.now)
    gmt_modified: datetime = Field(default_factory=datetime.now)
    gmt_last_login: Optional[datetime] = Field(default=None)
    creator: str = Field(max_length=64)
    modifier: str = Field(max_length=64)


# Database model, database table inferred from class name
class Account(AccountBase, table=True):  # type: ignore
    """The account model."""

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    password: str = Field(max_length=255)

    @property
    def has_password(self) -> bool:
        """Check if the account has a password set."""
        return self.password is not None
