# -*- coding: utf-8 -*-
from sqlalchemy import TypeDecorator, Integer
from typing import Any


class IntEnum(TypeDecorator):
    impl = Integer

    def __init__(self, enum_type: Any) -> None:
        super().__init__()
        self.enum_type = enum_type

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if isinstance(value, self.enum_type):
            return value.value
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        return self.enum_type(value)
