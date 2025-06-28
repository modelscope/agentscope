# -*- coding: utf-8 -*-
from sqlmodel import select, and_, or_
from typing import Optional
from app.dao.base_dao import BaseDAO
from app.models.provider import ProviderBase


class ProviderDAO(BaseDAO[ProviderBase]):
    _model_class = ProviderBase

    def get_by_provider(
        self,
        provider: str,
        workspace_id: str = None,
    ) -> ProviderBase:
        """get provider information according to provider"""
        conditions = [self._model_class.provider == provider]
        if workspace_id:
            conditions.append(self._model_class.workspace_id == workspace_id)

        query = select(self._model_class).where(and_(*conditions))
        return self.session.exec(query).first()

    def get_by_name(
        self,
        name: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> list[ProviderBase]:
        """List of providers based on fuzzy name search"""
        conditions = []
        if name:
            conditions.append(self._model_class.name.like(f"%{name}%"))
        if workspace_id:
            conditions.append(self._model_class.workspace_id == workspace_id)

        query = select(self._model_class)
        if conditions:
            query = query.where(and_(*conditions))
        return self.session.exec(query).all()

    def get_by_workspace(self, workspace_id: str) -> list[ProviderBase]:
        """Get all providers under the workspace"""
        query = select(self._model_class).where(
            self._model_class.workspace_id == workspace_id,
        )
        return self.session.exec(query).all()
