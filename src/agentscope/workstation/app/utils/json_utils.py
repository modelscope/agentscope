# -*- coding: utf-8 -*-
from datetime import datetime
from fastapi.encoders import jsonable_encoder
import json
from typing import Any


def datetime_to_timestamp(obj: Any) -> int:
    """Convert datetime object to timestamp

    Args:
        obj: datetime object

    Returns:
        int: timestamp in milliseconds
    """
    if isinstance(obj, datetime):
        return int(obj.timestamp() * 1000)
    return obj


def json_dumps(obj: Any, **kwargs: Any) -> str:
    """Customized JSON serialization

    Args:
        obj: object to serialize
        **kwargs: kwargs to json.dumps

    Returns:
        str: JSON string
    """
    encoded = jsonable_encoder(obj)
    if isinstance(encoded, dict):
        for key, value in encoded.items():
            encoded[key] = datetime_to_timestamp(value)
    elif isinstance(encoded, list):
        encoded = [datetime_to_timestamp(item) for item in encoded]
    return json.dumps(encoded, **kwargs)
