# -*- coding: utf-8 -*-
"""Import customized agents."""
import inspect
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel
from .seeker_agent import SeekerAgent


class Param(BaseModel):
    """The parameter of an customized agent."""

    name: str
    default: Optional[Any] = None
    type_hint: Optional[str] = None


class CustomizedAgents:
    """A registry for customized agents."""

    def __init__(self) -> None:
        self.agent_classes: Dict[str, type] = {}
        self.agent_params: Dict[str, Dict[str, Param]] = {}

    def register(self, agent_cls_name: str, agent_cls: type) -> None:
        """Register an customized agent class."""
        self.agent_classes[agent_cls_name] = agent_cls
        self.agent_params[agent_cls_name] = {}
        for param_name, param in inspect.signature(
            agent_cls.__init__,  # type: ignore[misc]
        ).parameters.items():
            # Skip 'self' parameter
            if param_name != "self":
                self.agent_params[agent_cls_name][param_name] = Param(
                    name=param_name,
                    default=param.default
                    if param.default is not param.empty
                    else None,
                    type_hint=(
                        param.annotation.__name__
                        if param.annotation is not param.empty
                        else None
                    ),
                )

    def get_all_agent_cls_names(self) -> list[str]:
        """Get all customized agent class names."""
        return list(self.agent_classes.keys())

    def get_agent_cls(self, agent_cls_name: str) -> type:
        """Get an customized agent class by the class name."""
        return self.agent_classes[agent_cls_name]

    def get_agent_params(self, agent_cls_name: str) -> Dict[str, Param]:
        """
        Get an customized agent's parameters and their defaults
        by the class name.
        """
        return self.agent_params[agent_cls_name]


customized_agents = CustomizedAgents()

__all__ = ["customized_agents", "SeekerAgent"]
