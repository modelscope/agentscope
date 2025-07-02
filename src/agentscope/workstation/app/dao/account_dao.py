# -*- coding: utf-8 -*-
"""Account Dao"""
from typing import Optional
from app.dao.base_dao import BaseDAO
from app.models.account import Account
from app.utils.timestamp import get_current_time


class AccountDao(BaseDAO[Account]):
    """Dao for account."""

    _model_class = Account

    def update_last_login_info(
        self,
        id: int,
    ) -> Optional[Account]:
        """Update the last login info of the account."""
        account = self.get(id)
        account.gmt_last_login = get_current_time()
        self.session.commit()
        return account
