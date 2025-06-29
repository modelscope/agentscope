# -*- coding: utf-8 -*-

from pydantic import BaseModel


class ModelCredential(BaseModel):
    endpoint: str
    api_key: str

    def __json__(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "api_key": self.api_key,
        }
