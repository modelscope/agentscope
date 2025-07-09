# -*- coding: utf-8 -*-
"""The account related services"""
import uuid
from typing import Optional, List, Tuple, Union

from app.dao.account_dao import AccountDao
from app.exceptions.service import (
    AccountAlreadyExistsException,
    IncorrectPasswordException,
    AccountNotFoundException,
)
from app.models.account import Account
from app.schemas.common import PaginationParams
from app.utils.security import (
    get_password_hash,
    verify_password,
)
from .base_service import BaseService


class AccountService(BaseService[AccountDao]):
    """Service layer for accounts."""

    _dao_cls = AccountDao

    def delete_account(self, account_id: Union[str, uuid.UUID]) -> None:
        """
        Delete current account.
        """
        account = self.get(account_id)
        if not account:
            raise AccountNotFoundException(
                extra_info={"account_id": account_id},
            )
        self.delete_all_by_field("account_id", account_id)

    def update_account(
        self,
        account_id: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        email: Optional[str] = None,
        new_password: Optional[str] = None,
        current_account: Account = None,
    ) -> Account:
        """
        Update current account.
        """
        account = self.get_account_by_account_id(account_id)
        if not account:
            raise AccountNotFoundException(
                extra_info={"account_id": account_id},
            )

        if password and not verify_password(password, account.password):
            raise IncorrectPasswordException()

        if username:
            account.username = username
        if new_password:
            account.password = get_password_hash(new_password)
        if email:
            account.email = email
        account.creator = (current_account.username,)
        account.modifier = (current_account.username,)
        if not account.id:
            raise AccountNotFoundException(
                extra_info={"account_id": account_id},
            )
        updated_account = self.update(
            account.id,
            account.model_dump(),
        )
        return updated_account

    def create_account(
        self,
        account_id: str,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        current_account: Account = None,
    ) -> Account:
        """Create a new account."""
        account = self.get_account_by_username(username)
        if account:
            raise AccountAlreadyExistsException(
                extra_info={"username": username},
            )
        if password:
            password = get_password_hash(password)

        account = Account(
            account_id=account_id,
            email=email,
            type="user",
            password=password,
            username=username,
            creator=current_account.username,
            modifier=current_account.username,
        )
        account = self.create(account)
        return account

    def get_account(self, account_id: str) -> Account:
        """Get an account by account_id."""
        account = self.get_first_by_field("account_id", account_id)
        if not account:
            raise AccountNotFoundException(
                extra_info={"account_id": account_id},
            )
        return account

    def list_accounts(
        self,
        name: str,
        pagination: PaginationParams,
    ) -> Tuple[int, List[Account]]:
        """List accounts."""
        filters = {"status": 1, "type": "user"}
        if name:
            filters["username"] = {"like": f"%{name}%"}

        total = self.count_by_fields(filters)
        accounts = self.paginate(
            filters=filters,
            pagination=pagination,
        )
        return total, accounts

    def get_account_by_username(self, username: str) -> Optional[Account]:
        """Get an account by username."""
        account = self.get_first_by_field("username", username)
        return account

    def get_account_by_account_id(self, account_id: str) -> Optional[Account]:
        """Get an account by account_id."""
        account = self.get_first_by_field("account_id", account_id)
        return account

    def update_last_login_info(
        self,
        id_: int,
    ) -> Optional[Account]:
        """Update last login info."""
        return self.dao.update_last_login_info(id_=id_)
