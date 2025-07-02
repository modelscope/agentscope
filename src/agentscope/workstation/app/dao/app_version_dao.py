# -*- coding: utf-8 -*-
"""Module for app version related functions."""
from typing import Dict, Any, List
from loguru import logger
from sqlmodel import select

from app.dao.base_dao import BaseDAO
from app.models.app import AppVersionEntity
from app.utils.timestamp import get_current_time


class AppVersionDAO(BaseDAO[AppVersionEntity]):
    """App Version DAO class."""

    _model_class = AppVersionEntity

    def update_by_where_conditions(
        self,
        *where_conditions: Any,
        obj_data: Dict[str, Any],
    ) -> List[AppVersionEntity]:
        """
        Batch update records based on WHERE conditions

        :param where_conditions: SQLAlchemy WHERE condition expression tuple
        :param obj_data: Field data dictionary to be updated
        :param change_update_time: Automatically update modification time
        :return: Updated model instance list
        """
        try:
            # Query records that meet the criteria
            query = select(self.model).where(*where_conditions)
            results = self.session.exec(query).all()

            data_dict = self._convert_to_dict(obj_data)

            updated_objs = []
            for db_obj in results:
                self._update_object_fields(db_obj, data_dict)
                updated_objs.append(db_obj)

            self.session.commit()
            return updated_objs

        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error batch updating {self.model.__name__}: {str(e)}",
            )
            raise

    def _convert_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert an object to dictionary if possible."""
        for method in ["model_dump", "dict", "to_dict"]:
            if hasattr(obj, method):
                return getattr(obj, method)()
        return obj

    def _update_object_fields(
        self,
        db_obj: AppVersionEntity,
        data_dict: Dict[str, Any],
    ) -> None:
        """Update object fields from a dictionary."""
        for field, value in data_dict.items():
            if not hasattr(db_obj, field):
                raise ValueError(
                    f"Field {field} not found in {self.model.__name__}",
                )
            processed_value = self._convert_to_dict(value)
            setattr(db_obj, field, processed_value)
        db_obj.gmt_modified = get_current_time()
