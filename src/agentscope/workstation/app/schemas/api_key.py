# -*- coding: utf-8 -*-
"""Api key schemas"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApiKey(BaseModel):
    """
    api key schema
    """

    id: Optional[int] = Field(default=None, alias="id")
    api_key: Optional[str] = Field(default=None, alias="api_key")
    description: Optional[str] = Field(default=None, alias="description")
    gmt_create: Optional[datetime] = Field(default=None, alias="gmt_create")
    gmt_modified: Optional[datetime] = Field(
        default=None,
        alias="gmt_modified",
    )
    creator: Optional[str] = Field(default=None, alias="creator")
    modifier: Optional[str] = Field(default=None, alias="modifier")
