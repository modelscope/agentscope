# -*- coding: utf-8 -*-
from loguru import logger
from typing import Dict, Optional, Any, List

from sqlmodel import select

from app.dao.base_dao import BaseDAO
from app.models.app import AppVersionEntity
from app.utils.timestamp import get_current_time


class AppVersionDAO(BaseDAO[AppVersionEntity]):
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

            # Convert data objects
            for method in ["model_dump", "dict", "to_dict"]:
                if hasattr(obj_data, method):
                    obj_data = getattr(obj_data, method)()
                    break

            updated_objs = []
            for db_obj in results:
                # Update field values
                for field, value in obj_data.items():
                    if hasattr(db_obj, field):
                        # Handling nested objects
                        for method in ["model_dump", "dict", "to_dict"]:
                            if hasattr(value, method):
                                value = getattr(value, method)()
                                break
                        setattr(db_obj, field, value)
                    else:
                        raise ValueError(
                            f"Field {field} not found in "
                            f"{self.model.__name__}",
                        )

                # update modify time
                db_obj.gmt_modified = get_current_time()

                updated_objs.append(db_obj)

            self.session.commit()
            return updated_objs

        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error batch updating {self.model.__name__}: {str(e)}",
            )
            raise
