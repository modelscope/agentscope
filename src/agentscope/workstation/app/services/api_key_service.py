# -*- coding: utf-8 -*-
"""Module for API key related functions."""
import uuid
from typing import Optional

from sqlmodel import desc

from app.dao.api_key_dao import ApiKeyDAO
from app.exceptions.service import ApiKeyNotFoundException
from app.models.account import Account
from app.models.api_key import ApiKeyEntity, ApiKeyStatus
from app.schemas.api_key import ApiKey
from app.schemas.app import BaseQuery
from app.schemas.base import PagingList
from app.schemas.common import PaginationParams
from app.services.base_service import BaseService
from app.utils.crypto import encrypt_with_rsa, decrypt_with_rsa, mask_string


class ApiKeyService(BaseService[ApiKeyDAO]):
    """
    API key related services
    """

    _dao_cls = ApiKeyDAO

    def create_api_key(self, current_account: Account, api_key: ApiKey) -> int:
        """
        create a new api key
        """

        ak = f"sk-{str(uuid.uuid4()).replace('-', '')}"
        ak = encrypt_with_rsa(ak)

        account_id = str(current_account.id)
        entity = ApiKeyEntity(
            api_key=ak,
            account_id=account_id,
            description=api_key.description,
            creator=account_id,
            modifier=account_id,
        )

        created_api_key = self.dao.create(entity)
        return created_api_key.id  # type: ignore

    def update_api_key(
        self,
        current_account: Account,
        api_key: ApiKey,
    ) -> None:
        """
        update an existing api key
        """
        if not api_key.id:
            raise ApiKeyNotFoundException
        entity = self._get_entity_by_id(
            account_id=current_account.account_id,
            api_key_id=api_key.id,
        )

        if not entity:
            raise ApiKeyNotFoundException

        entity.description = api_key.description
        entity.modifier = str(current_account.id)
        self.dao.update(api_key.id, entity)

    def get_api_key(
        self,
        current_account: Account,
        api_key_id: int,
    ) -> Optional[ApiKey]:
        """
        get an existing api key
        """

        entity = self._get_entity_by_id(
            account_id=current_account.account_id,
            api_key_id=api_key_id,
        )

        if not entity:
            return None

        return self._to_api_key(entity=entity, mask=False)

    def delete_api_key(
        self,
        current_account: Account,
        api_key_id: int,
    ) -> None:
        """
        delete an existing api key
        """

        entity = self._get_entity_by_id(
            account_id=current_account.account_id,
            api_key_id=api_key_id,
        )
        if not entity:
            raise ApiKeyNotFoundException

        entity.status = ApiKeyStatus.DELETED
        entity.modifier = current_account.account_id

        self.dao.update(api_key_id, entity)

    def list_api_keys(
        self,
        current_account: Account,
        query: BaseQuery,
    ) -> PagingList[ApiKey]:
        """
        list api keys
        """
        conditions = [
            ApiKeyEntity.account_id == str(current_account.id),
            ApiKeyEntity.status != ApiKeyStatus.DELETED,
        ]

        # query total and api keys
        total = self.dao.count_by_where_conditions(*conditions)

        order_by = [desc(ApiKeyEntity.gmt_modified)]
        pagination = PaginationParams(page=query.current, page_size=query.size)
        entities = self.dao.paginate_by_conditions(
            *conditions,
            order_by=order_by,
            pagination=pagination,
        )

        # convert entity
        api_keys = (
            [self._to_api_key(entity) for entity in entities]
            if entities
            else []
        )

        return PagingList(
            current=query.current,
            size=query.size,
            total=total,
            records=api_keys,
        )

    def _get_entity_by_id(
        self,
        account_id: str,
        api_key_id: int,
    ) -> Optional[ApiKeyEntity]:
        conditions = [
            ApiKeyEntity.id == api_key_id,
            ApiKeyEntity.account_id == account_id,
            ApiKeyEntity.status != ApiKeyStatus.DELETED,
        ]

        return self.dao.get_first_by_where_conditions(*conditions)

    @staticmethod
    def _to_api_key(
        entity: ApiKeyEntity,
        mask: bool = True,
    ) -> Optional[ApiKey]:
        if not entity:
            return None

        api_key = ApiKey(**entity.model_dump())

        if api_key.api_key is None:
            return None
        api_key.api_key = decrypt_with_rsa(api_key.api_key)
        if mask:
            api_key.api_key = mask_string(api_key.api_key)

        return api_key
