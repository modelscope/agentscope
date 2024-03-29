# -*- coding: utf-8 -*-
"""User Proxy Agent class for distributed usage"""
from typing import Sequence, Union
from typing import Optional

from agentscope.agents import UserAgent


class UserProxyAgent(UserAgent):
    """User proxy agent class"""

    def reply(  # type: ignore [override]
        self,
        x: dict = None,
        required_keys: Optional[Union[list[str], str]] = None,
    ) -> dict:
        """
        Reply with `self.speak(x)`
        """
        if x is not None:
            self.speak(x)
        return super().reply(x, required_keys)

    def observe(self, x: Union[dict, Sequence[dict]]) -> None:
        """
        Observe with `self.speak(x)`
        """
        if x is not None:
            self.speak(x)  # type: ignore[arg-type]
            self.memory.add(x)
