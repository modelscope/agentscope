# -*- coding: utf-8 -*-
"""The model related services"""
from pydantic import BaseModel


class ModelCredential(BaseModel):
    """The model credential"""

    endpoint: str
    api_key: str

    def __json__(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "api_key": self.api_key,
        }
