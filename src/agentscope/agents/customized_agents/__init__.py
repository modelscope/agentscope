# -*- coding: utf-8 -*-
"""Import customized agents."""
import inspect

from .seeker_agent import SeekerAgent


class CustomizedAgents:
    """A registry for customized agents."""

    def __init__(self) -> None:
        self.agent_classes = {}
        self.agent_params = {}

    def register(self, agent_cls_name: str, agent_cls: type) -> None:
        """Register an customized agent class."""
        self.agent_classes[agent_cls_name] = agent_cls
        self.agent_params[agent_cls_name] = {}
        for param_name, param in inspect.signature(
            agent_cls.__init__,  # type: ignore[misc]
        ).parameters.items():
            # Skip 'self' parameter
            if param_name != "self":
                self.agent_params[agent_cls_name][param_name] = (
                    param.default if param.default is not param.empty else None
                )

    def get_all_agent_cls_names(self) -> list[str]:
        """Get all customized agent class names."""
        return list(self.agent_classes.keys())

    def get_agent_cls(self, agent_cls_name: str) -> type:
        """Get an customized agent class by the class name."""
        return self.agent_classes[agent_cls_name]

    def get_agent_params(self, agent_cls_name: str) -> dict:
        """Get an customized agent class parameters by the class name."""
        return self.agent_params[agent_cls_name]


customized_agents = CustomizedAgents()

__all__ = ["customized_agents", "SeekerAgent"]
