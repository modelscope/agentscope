# -*- coding: utf-8 -*-
"""User Proxy Agent class for distributed usage"""
from typing import Sequence, Union
from typing import Optional

from agentscope.agents import UserAgent
from agentscope.message import Msg


class UserProxyAgent(UserAgent):
    """User proxy agent class"""

    def reply(  # type: ignore[override]
        self,
        x: Optional[Union[Msg, Sequence[Msg]]] = None,
        required_keys: Optional[Union[list[str], str]] = None,
    ) -> Msg:
        """
        Reply with `self.speak(x)`
        """
        if x is not None:
            self.speak(x)
        return super().reply(x, required_keys)

    def observe(self, x: Union[Msg, Sequence[Msg]]) -> None:
        """
        Observe with `self.speak(x)`
        """
        if x is not None:
            self.speak(x)  # type: ignore[arg-type]
            self.memory.add(x)
