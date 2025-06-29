# -*- coding: utf-8 -*-
import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from loguru import logger
from sqlmodel import Session, SQLModel, asc, desc, func, select

from app.models.app import AppEntity, AppVersionEntity
from app.schemas.common import PaginationParams
from app.utils.timestamp import get_current_time

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseDAO(Generic[ModelType]):
    _model_class: Type[ModelType]
    """
    Base Data Access Object class, provides basic CRUD operations for
    database models

    Responsibilities:
    - Execute database operations
    - Return database model instances
    - Does not handle business logic or validation
    """

    def __init__(self, session: Session):
        self.session = session
        self.model = self._model_class

    def get(self, id: Union[str, int, uuid.UUID]) -> Optional[ModelType]:
        try:
            statement = select(self.model).where(self.model.id == id)
            return self.session.exec(statement).first()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} with id {id}: {str(e)}",
            )
            raise

    def count_by_field(self, field_name: str, value: Any) -> int:
        try:
            query = (
                select(
                    func.count(),
                )
                .select_from(self.model)
                .where(getattr(self.model, field_name) == value)
            )
            return self.session.exec(query).one()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} count: {str(e)}",
            )
            raise

    def count_by_fields(self, filters: Dict[str, Any]) -> int:
        try:
            query = select(func.count()).select_from(self.model)
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    query = query.where(
                        getattr(self.model, field_name) == value,
                    )

            count = self.session.exec(query).one()  # Get count
            return count

        except Exception as e:
            logger.error(
                f"Error counting {self.model.__name__} with fields "
                f"{filters}: {str(e)}",
            )
            raise

    def get_first_by_fields(
        self,
        filters: Dict[str, Any],
    ) -> Optional[ModelType]:
        try:
            query = select(self.model)
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    query = query.where(
                        getattr(self.model, field_name) == value,
                    )
            return self.session.exec(query).first()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by fields {filters}: {str(e)}",  # noqa 501
            )
            raise

    def get_all_by_fields(self, filters: Dict[str, Any]) -> List[ModelType]:
        try:
            query = select(self.model)
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    query = query.where(
                        getattr(self.model, field_name) == value,
                    )
            return self.session.exec(query).all()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by fields {filters}: {str(e)}",  # noqa 501
            )
            raise

    def get_first_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> Optional[ModelType]:
        try:
            query = select(self.model).where(
                getattr(self.model, field_name) == value,
            )
            return self.session.exec(query).first()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by {field_name}: {str(e)}",  # noqa 501
            )
            raise

    def get_all_by_field(self, field_name: str, value: Any) -> List[ModelType]:
        try:
            query = select(self.model).where(
                getattr(self.model, field_name) == value,
            )
            return self.session.exec(query).all()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by {field_name}: {str(e)}",  # noqa 501
            )
            raise

    def delete_all_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> List[ModelType]:
        try:
            query = select(self.model).where(
                getattr(self.model, field_name) == value,
            )
            results = self.session.exec(query).all()
            for item in results:
                self.session.delete(item)
            self.session.commit()
            return results
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by {field_name}: {str(e)}",  # noqa 501
            )
            raise

    def paginate(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> List[ModelType]:
        try:
            query = select(self.model)
            if filters:
                for attr, value in filters.items():
                    if hasattr(self.model, attr):
                        query = query.where(getattr(self.model, attr) == value)

            if (
                pagination
                and pagination.search
                and hasattr(
                    self.model,
                    "name",
                )
            ):
                query = query.where(
                    self.model.name.contains(
                        pagination.search,
                    ),
                )

            if pagination is None:
                return self.session.exec(query).all()

            order_by = pagination.order_by
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                if pagination.order_direction == "desc":
                    query = query.order_by(desc(order_column))
                elif pagination.order_direction == "asc":
                    query = query.order_by(asc(order_column))

                query = query.order_by(getattr(self.model, order_by))

            statement = query.offset(pagination.skip).limit(pagination.limit)
            return self.session.exec(statement).all()

        except Exception as e:
            logger.error(
                f"Error getting multiple {self.model.__name__}: {str(e)}",
            )
            raise

    def create(
        self,
        obj_data: Union[AppEntity, AppVersionEntity, Dict[str, Any]],
    ) -> ModelType:
        try:
            for method in ["model_dump", "dict", "to_dict"]:
                if hasattr(obj_data, method):
                    obj_data = getattr(obj_data, method)()
                    break
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)
            self.session.commit()
            self.session.refresh(db_obj)
            return db_obj
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise

    def update(
        self,
        id: Union[str, int, uuid.UUID],
        obj_data: Dict[str, Any],
        change_update_time: Optional[bool] = True,
    ) -> ModelType:
        try:
            db_obj = self.get(id)
            if not db_obj:
                raise ValueError(
                    f"{self.model.__name__} with id {id} not found",
                )

            for method in ["model_dump", "dict", "to_dict"]:
                if hasattr(obj_data, method):
                    obj_data = getattr(obj_data, method)()
                    break
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    for method in ["model_dump", "dict", "to_dict"]:
                        if hasattr(value, method):
                            value = getattr(value, method)()
                            break
                    setattr(db_obj, field, value)
                else:
                    raise ValueError(
                        f"Field {field} not found in {self.model.__name__}",
                    )
            if change_update_time:
                db_obj.gmt_modified = get_current_time()
            self.session.commit()
            return db_obj
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error updating {self.model.__name__} with id {id}: {str(e)}",
            )
            raise

    def delete(self, id: Union[str, int, uuid.UUID]) -> bool:
        try:
            db_obj = self.get(id)
            if not db_obj:
                return False
            self.session.delete(db_obj)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error deleting {self.model.__name__} with id {id}: {str(e)}",
            )
            raise

    def exists(self, id: Union[str, int, uuid.UUID]) -> bool:
        try:
            statement = select(self.model).where(self.model.id == id)
            result = self.session.exec(statement).first()
            return result is not None
        except Exception as e:
            logger.error(
                f"Error checking existence of {self.model.__name__} with id {id}: {str(e)}",  # noqa 301
            )
            raise

    def get_first_by_where_conditions(
        self,
        *where_conditions: Any,
        order_by: Optional[list] = None,
    ) -> Optional[ModelType]:
        try:
            query = select(self.model)
            if where_conditions:
                query = query.where(*where_conditions)
            if order_by:
                query = query.order_by(*order_by)

            return self.session.exec(query).first()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by fields {where_conditions}: {str(e)}",  # noqa 501
            )
            raise

    def get_all_by_where_conditions_and_order_by(
        self,
        *where_conditions: Any,
        order_by: Optional[list] = None,
    ) -> List[ModelType]:
        try:
            query = select(self.model)
            if where_conditions:
                query = query.where(*where_conditions)
            if order_by:
                query = query.order_by(*order_by)

            return self.session.exec(query).all()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by fields "
                f"{where_conditions}: {str(e)}",
            )
            raise

    def count_by_where_conditions(self, *where_conditions: Any) -> int:
        try:
            query = select(func.count()).select_from(self.model)
            if where_conditions:
                query = query.where(
                    *where_conditions,
                )  # Apply all incoming conditions

            count = self.session.exec(query).one()  # Get count
            return count
        except Exception as e:
            logger.error(
                f"Error counting {self.model.__name__} with where conditions "
                f"{where_conditions}: {str(e)}",
            )
            raise

    def paginate_by_conditions(
        self,
        *where_conditions: Any,
        order_by: Optional[list] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> List[ModelType]:
        try:
            query = select(self.model)
            if where_conditions:
                query = query.where(*where_conditions)
            if order_by:
                query = query.order_by(*order_by)

            if pagination is None:
                return self.session.exec(query).all()

            statement = query.offset(pagination.skip).limit(pagination.limit)
            return self.session.exec(statement).all()

        except Exception as e:
            logger.error(
                f"Error getting multiple {self.model.__name__}: {str(e)}",
            )
            raise
