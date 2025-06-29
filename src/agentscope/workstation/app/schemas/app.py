# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel

from app.models.app import AppType, AppStatus, AppVersionEntity
from app.schemas.base import BaseQuery


# Define Application Pydantic Model
class App(BaseModel):
    id: Optional[int] = None
    workspace_id: Optional[str] = None
    app_id: Optional[str] = None
    name: str
    config: Dict[str, Any] = None
    description: Optional[str] = None
    type: Optional[AppType] = None
    status: Optional[AppStatus] = None
    pub_config: Optional[Dict[str, Any]] = None
    source: str = "console"
    gmt_create: Optional[datetime] = None
    gmt_modified: Optional[datetime] = None
    creator: Optional[str] = None
    modifier: Optional[str] = None
    # latest version
    latestVersion: Optional[AppVersionEntity] = None
    # released version
    publishedVersion: Optional[AppVersionEntity] = None

    class Config:
        use_enum_values = (
            True  # Use enumeration values instead of names when serializing
        )
        validate_by_name = True  # Support filling data by field name or alias


class AppQuery(BaseQuery):
    app_id: Optional[str] = None
    type: Optional[AppType] = None
