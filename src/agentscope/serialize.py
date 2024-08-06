# -*- coding: utf-8 -*-
"""The serialization module for the package."""
import importlib
import json
from typing import Any

from .message import Msg


class _AgentScopeEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        """Serialize the object to a JSON string."""
        # TODO: The serialization of ResponseStub should be avoided
        # if isinstance(o, ResponseStub):
        #     return None

        if isinstance(o, Msg):
            return o.serialize()

        return super().default(o)


def _deserialize_hook(data: dict) -> Any:
    """Deserialize the JSON string to an object, including Msg object in
    AgentScope."""
    module_name = data.get("__module__", None)
    class_name = data.get("__name__", None)

    if module_name is not None and class_name is not None:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        if hasattr(cls, "from_dict"):
            return cls.from_dict(data)
    return data


def serialize(obj: Any) -> str:
    """Serialize the object to a JSON string.

    For AgentScope, this function supports to serialize `Msg` object for now.
    """
    # TODO: We leave the serialization of agents in next PR
    return json.dumps(obj, ensure_ascii=False, cls=_AgentScopeEncoder)


def deserialize(s: str) -> Any:
    """Deserialize the JSON string to an object

    For AgentScope, this function supports to serialize `Msg` object for now.
    """
    # TODO: We leave the serialization of agents in next PR
    return json.loads(s, object_hook=_deserialize_hook)
