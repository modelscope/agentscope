# -*- coding: utf-8 -*-
from typing import Optional, List, Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=(BaseModel | dict | list | bool | str | int | float))


class BaseQuery(BaseModel):
    name: Optional[str] = None
    current: Optional[int] = 1
    size: Optional[int] = 10
    status: Optional[int] = None


class PagingList(BaseModel, Generic[T]):
    current: Optional[int] = 1
    size: Optional[int] = 10
    total: Optional[int] = None
    records: Optional[List[T]] = None
