# -*- coding: utf-8 -*-
from fastapi import APIRouter

from app.api.deps import CurrentAccount, SessionDep, BaseQueryDeps
from app.exceptions.base import IncorrectParameterException
from app.schemas.api_key import ApiKey
from app.schemas.response import create_success_response
from app.services.api_key_service import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("")
async def create_api_key(
    current_account: CurrentAccount,
    session: SessionDep,
    api_key: ApiKey,
) -> dict:
    if not api_key.description or api_key.description.strip() == "":
        raise IncorrectParameterException(
            extra_info="Missing required parameter: description",
        )

    api_key_service = ApiKeyService(session=session)
    aid = api_key_service.create_api_key(
        current_account=current_account,
        api_key=api_key,
    )

    return create_success_response(data=aid)


@router.put("/{api_key_id}")
async def update_api_key(
    api_key_id: int,
    current_account: CurrentAccount,
    session: SessionDep,
    api_key: ApiKey,
) -> dict:
    if not api_key_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: api_key_id",
        )

    if not api_key.description or api_key.description.strip() == "":
        raise IncorrectParameterException(
            extra_info="Missing required parameter: description",
        )

    api_key_service = ApiKeyService(session=session)
    api_key.id = api_key_id
    api_key_service.update_api_key(
        current_account=current_account,
        api_key=api_key,
    )

    return create_success_response(data=None)


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_account: CurrentAccount,
    session: SessionDep,
) -> dict:
    if not api_key_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: api_key_id",
        )

    api_key_service = ApiKeyService(session=session)
    api_key_service.delete_api_key(
        current_account=current_account,
        api_key_id=api_key_id,
    )

    return create_success_response(data=None)


@router.get("/{api_key_id}")
async def get_api_key(
    api_key_id: int,
    current_account: CurrentAccount,
    session: SessionDep,
) -> dict:
    if not api_key_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: api_key_id",
        )

    api_key_service = ApiKeyService(session=session)
    api_key = api_key_service.get_api_key(
        current_account=current_account,
        api_key_id=api_key_id,
    )

    return create_success_response(data=api_key)


@router.get("")
async def list_api_keys(
    query: BaseQueryDeps,
    current_account: CurrentAccount,
    session: SessionDep,
) -> dict:
    api_key_service = ApiKeyService(session=session)
    api_keys = api_key_service.list_api_keys(
        current_account=current_account,
        query=query,
    )

    return create_success_response(data=api_keys)
