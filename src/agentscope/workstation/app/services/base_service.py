# -*- coding: utf-8 -*-
"""base service"""
import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from loguru import logger
from sqlmodel import Session, SQLModel

from app.dao.base_dao import BaseDAO
from app.schemas.common import PaginationParams

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)
DAOType = TypeVar("DAOType", bound=BaseDAO)


class BaseService(Generic[DAOType]):
    """Base service class"""

    _dao_cls: Type[DAOType]

    def __init__(self, session: Session):
        self.dao = self._dao_cls(session=session)
        self.session = session

    def get(self, id: Union[str, int, uuid.UUID]) -> Optional[ModelType]:
        """Get"""
        try:
            return self.dao.get(id)
        except Exception as e:
            logger.error(
                f"Service error getting entity with id {id}: {str(e)}",
            )
            raise

    def paginate(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> List[ModelType]:
        """Paginate"""
        try:
            return self.dao.paginate(filters=filters, pagination=pagination)
        except Exception as e:
            logger.error(f"Service error getting multiple entities: {str(e)}")
            raise

    def create(self, obj_in: Dict[str, Any]) -> ModelType:  # type: ignore
        """Create"""
        try:
            self._validate_create(obj_in)
            return self.dao.create(obj_in)
        except Exception as e:
            logger.error(f"Service error creating entity: {str(e)}")
            raise

    def update(
        self,
        id: Union[str, int, uuid.UUID],
        obj_in: Dict[str, Any],
        change_update_time: Optional[bool] = True,
    ) -> ModelType:  # type: ignore
        """Update"""
        try:
            self._validate_update(id, obj_in)
            model = self.dao.update(
                id,
                obj_in,
                change_update_time=change_update_time,
            )
            return model
        except Exception as e:
            logger.error(
                f"Service error updating entity with id {id}: {str(e)}",
            )
            raise

    def count_by_field(self, field_name: str, value: Any) -> int:
        """Count by field"""
        try:
            return self.dao.count_by_field(field_name, value)
        except Exception as e:
            logger.error(
                f"Service error counting entities by {field_name}: {str(e)}",
            )
            raise

    def count_by_fields(self, filters: Dict[str, Any]) -> int:
        """Count by fields"""
        try:
            return self.dao.count_by_fields(filters)
        except Exception as e:
            logger.error(
                f"Service error counting entities by {filters}: {str(e)}",
            )
            raise

    def get_first_by_fields(
        self,
        filters: Dict[str, Any],
    ) -> Optional[ModelType]:
        """Get first by fields"""
        try:
            return self.dao.get_first_by_fields(filters)
        except Exception as e:
            logger.error(
                f"Service error counting entities by {filters}: {str(e)}",
            )
            raise

    def get_last_by_fields(
        self,
        filters: Dict[str, Any],
    ) -> Optional[ModelType]:
        """Get last by fields"""
        try:
            items = self.dao.get_all_by_fields(filters)
            if len(items) > 0:
                return items[-1]
            return None
        except Exception as e:
            logger.error(
                f"Service error counting entities by {filters}: {str(e)}",
            )
            raise

    def get_all_by_fields(
        self,
        filters: Dict[str, Any],
    ) -> List[ModelType]:
        """Get all by fields"""
        try:
            return self.dao.get_all_by_fields(filters)
        except Exception as e:
            logger.error(
                f"Service error counting entities by {filters}: {str(e)}",
            )
            raise

    def get_first_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> Optional[ModelType]:
        """Get first by field"""
        try:
            return self.dao.get_first_by_field(field_name, value)
        except Exception as e:
            logger.error(
                f"Service error getting entity by {field_name}: {str(e)}",
            )
            raise

    def get_last_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> Optional[ModelType]:
        """Get last by field"""
        try:
            values = self.dao.get_all_by_field(field_name, value)
            if len(values) > 0:
                return values[-1]
            return None
        except Exception as e:
            logger.error(
                f"Service error getting entity by {field_name}: {str(e)}",
            )
            raise

    def get_all_by_field(self, field_name: str, value: Any) -> List[ModelType]:
        """Get all by field"""
        try:
            return self.dao.get_all_by_field(field_name, value)
        except Exception as e:
            logger.error(
                f"Service error getting entity by {field_name}: {str(e)}",
            )
            raise

    def delete(self, id: Union[str, int, uuid.UUID]) -> bool:
        """Delete"""
        try:
            self._validate_delete(id)
            return self.dao.delete(id)
        except Exception as e:
            logger.error(
                f"Service error deleting entity with id {id}: {str(e)}",
            )
            raise

    def delete_all_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> List[ModelType]:
        """Delete all by field"""
        try:
            return self.dao.delete_all_by_field(field_name, value)
        except Exception as e:
            logger.error(
                f"Service error deleting entity by {field_name}: {str(e)}",
            )
            raise

    def _validate_create(self, obj_data: Dict[str, Any]) -> None:
        """Validate create"""
        # pass

    def _validate_update(
        self,
        id: Union[str, int, uuid.UUID],
        update_data: Dict[str, Any],
    ) -> None:
        """Validate update"""
        # pass

    def _validate_delete(self, id: Union[str, int, uuid.UUID]) -> None:
        """Validate delete"""
        # pass

    def _validate_exists(self, id: Union[str, int, uuid.UUID]) -> None:
        """Validate exists"""
        # pass
