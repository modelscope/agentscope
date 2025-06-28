# -*- coding: utf-8 -*-
from app.dao.base_dao import BaseDAO
from app.models.account import Account
from app.utils.timestamp import get_current_time
import uuid
from typing import Optional


class AccountDao(BaseDAO[Account]):
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
