# -*- coding: utf-8 -*-
from sqlmodel import Field
from datetime import datetime, timezone


def email_field() -> Field:
    """The email field"""
    return Field(unique=True, index=True, max_length=255)


def username_field() -> Field:
    """The username field"""
    return Field(min_length=1, max_length=255)


def password_field() -> Field:
    """The password field"""
    return Field(min_length=6, max_length=40)


def utc_datetime_field() -> Field:
    """The utc datetime field"""
    return Field(default_factory=lambda: datetime.now(timezone.utc))


def formatted_datetime_field() -> Field:
    """The formatted datetime field""" ""
    return Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def verification_code_field() -> Field:
    """The verification code field"""
    return Field(min_length=6, max_length=6)
