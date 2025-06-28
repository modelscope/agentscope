# -*- coding: utf-8 -*-
from enum import Enum
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


class OrderDirection(str, Enum):
    """Sorting direction"""

    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """Pagination parameters"""

    page: int = Field(default=1, ge=1, description="page number")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number per page",
    )
    order_by: Optional[str] = Field(default=None, description="Sorting field")
    order_direction: OrderDirection = Field(
        default=OrderDirection.DESC,
        description="Sorting direction",
    )
    search: Optional[str] = Field(default=None, description="search keyword")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size

    @classmethod
    def create(
        cls,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Optional["PaginationParams"]:
        if all(
            param is None
            for param in [
                page,
                page_size,
                order_by,
                order_direction,
                search,
            ]
        ):
            return None

        return cls(
            page=page if page is not None else cls.page,
            page_size=page_size if page_size is not None else cls.page_size,
            order_by=order_by,
            order_direction=(
                order_direction
                if order_direction is not None
                else cls.order_direction
            ),
            search=search if search is not None else cls.search,
        )

    @classmethod
    def from_pretrained(
        cls,
        page: Optional[int] = 1,
        page_size: Optional[int] = 10,
        search: Optional[str] = None,
    ) -> "PaginationParams":
        return cls(
            page=page,
            page_size=page_size,
            search=search,
        )
