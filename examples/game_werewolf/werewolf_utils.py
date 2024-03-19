# -*- coding: utf-8 -*-
"""utils."""
import re
from typing import Union, Any, Sequence

import numpy as np
from loguru import logger

from prompt import Prompts
from agentscope.agents import AgentBase
from agentscope.message import Msg


def check_winning(alive_agents: list, wolf_agents: list, host: str) -> bool:
    """check which group wins"""
    if len(wolf_agents) * 2 >= len(alive_agents):
        msg = Msg(host, Prompts.to_all_wolf_win)
        logger.chat(f"{host}: {msg.content}")
        return True
    if alive_agents and not wolf_agents:
        msg = Msg(host, Prompts.to_all_village_win)
        logger.chat(f"{host}: {msg.content}")
        return True
    return False


def update_alive_players(
    survivors: Sequence[AgentBase],
    wolves: Sequence[AgentBase],
    dead_names: Union[str, list[str]],
) -> tuple[list, list]:
    """update the list of alive agents"""
    if not isinstance(dead_names, list):
        dead_names = [dead_names]
    return [_ for _ in survivors if _.name not in dead_names], [
        _ for _ in wolves if _.name not in dead_names
    ]


def majority_vote(votes: list) -> Any:
    """majority_vote function"""
    unit, counts = np.unique(votes, return_counts=True)
    return unit[np.argmax(counts)]


def extract_name_and_id(name: str) -> tuple[str, int]:
    """extract player name and id from a string"""
    name = re.search(r"\bPlayer\d+\b", name).group(0)
    idx = int(re.search(r"Player(\d+)", name).group(1)) - 1
    return name, idx


def n2s(agents: Sequence[Union[AgentBase, str]]) -> str:
    """combine agent names into a string, and use "and" to connect the last
    two names."""

    def _get_name(agent_: Union[AgentBase, str]) -> str:
        return agent_.name if isinstance(agent_, AgentBase) else agent_

    if len(agents) == 1:
        return _get_name(agents[0])

    return (
        ", ".join([_get_name(_) for _ in agents[:-1]])
        + " and "
        + _get_name(agents[-1])
    )
