# -*- coding: utf-8 -*-
"""The provider related services"""
from typing import Optional, List
import json

from app.dao.provider_dao import ProviderDAO
from app.exceptions.service import (
    ProviderAlreadyExistsException,
    ProviderNotFoundException,
)
from app.models.provider import ProviderBase
from app.utils.crypto import encrypt_with_rsa
from .base_service import BaseService
from ..models.account import Account
from ..schemas.provider import ModelCredential


class ProviderService(BaseService[ProviderDAO]):
    """Service layer for providers."""

    _dao_cls = ProviderDAO

    def delete_provider(self, provider: str, workspace_id: str = None) -> None:
        """
        delete provider
        """
        provider_entity = self.get_provider_by_provider(provider, workspace_id)
        if not provider_entity:
            raise ProviderNotFoundException(extra_info={"provider": provider})
        self.delete(provider_entity.id)  # type: ignore

    def update_provider(
        self,
        provider: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        enable: Optional[bool] = None,
        credential: Optional[dict] = None,
        # supported_model_types: Optional[List[str]] = None,
        protocol: Optional[str] = None,
        workspace_id: str = None,
        current_account: Account = None,
    ) -> ProviderBase:
        """
        update provider infomation
        """
        provider_entity = self.get_provider_by_provider(provider, workspace_id)
        if not provider_entity:
            raise ProviderNotFoundException(extra_info={"provider": provider})

        if name:
            provider_entity.name = name
        if description:
            provider_entity.description = description
        if icon:
            provider_entity.icon = icon
        if enable is not None:
            provider_entity.enable = enable
        if credential:
            model_credential = ModelCredential(
                endpoint=credential["endpoint"],
                api_key=encrypt_with_rsa(credential["api_key"]),
            )
            provider_entity.credential = json.dumps(
                model_credential.__json__(),
            )
        # if supported_model_types:
        #     provider_entity.supported_model_types =
        #     supported_model_types.split(',')
        if protocol:
            provider_entity.protocol = protocol
        if current_account:
            provider_entity.modifier = current_account.account_id

        updated_provider = self.update(
            provider_entity.id,  # type: ignore
            provider_entity.model_dump(),
        )
        return updated_provider

    def create_provider(
        self,
        provider: str,
        name: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        enable: bool = True,
        credential: Optional[dict] = None,
        supported_model_types: Optional[List[str]] = None,
        protocol: str = "OpenAI",
        source: str = "custom",
        workspace_id: str = None,
        current_account: Account = None,
    ) -> ProviderBase:
        """create new provider"""
        provider_entity = self.get_provider_by_provider(provider, workspace_id)
        if provider_entity:
            raise ProviderAlreadyExistsException(
                extra_info={"provider": provider},
            )
        supported_model_types_str = None
        if supported_model_types:
            supported_model_types_str = ",".join(supported_model_types)
        model_credential = None
        if credential:
            model_credential = ModelCredential(
                endpoint=credential["endpoint"],
                api_key=encrypt_with_rsa(credential["api_key"]),
            )

        provider_entity = ProviderBase(
            provider=provider,
            name=name,
            description=description,
            icon=icon,
            enable=enable,
            credential=json.dumps(model_credential.__json__()),
            supported_model_types=supported_model_types_str,
            protocol=protocol,
            source=source,
            workspace_id=workspace_id,
            creator=current_account.account_id,
            modifier=current_account.account_id,
        )
        return self.create(provider_entity)

    def get_provider(
        self,
        provider: str,
        workspace_id: str = None,
    ) -> ProviderBase:
        """get provider information"""
        provider_entity = self.get_provider_by_provider(provider, workspace_id)
        if not provider_entity:
            raise ProviderNotFoundException(extra_info={"provider": provider})
        return provider_entity

    def list_providers(
        self,
        name: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> List[ProviderBase]:
        """list providers"""
        providers = self.dao.get_by_name(name, workspace_id)

        # Convert the supported_model_types string to a list.
        for provider in providers:
            if provider.supported_model_types:
                provider.supported_model_types = (
                    provider.supported_model_types.split(",")
                )
            else:
                provider.supported_model_types = []

        return providers

    def get_provider_by_provider(
        self,
        provider: str,
        workspace_id: str = None,
    ) -> ProviderBase:
        """get provider information according to provider"""
        return self.dao.get_by_provider(provider, workspace_id)

    def get_providers_by_workspace(
        self,
        workspace_id: str,
    ) -> List[ProviderBase]:
        """get all providers in the workspace"""
        return self.dao.get_by_workspace(workspace_id)
