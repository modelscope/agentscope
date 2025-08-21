# -*- coding: utf-8 -*-
"""utils."""
import re
from typing import Union, Any, Sequence, Type

import numpy as np
from pydantic import BaseModel, Field
from prompt import Prompts

from agentscope._logging import logger
from agentscope.agent import AgentBase, ReActAgent
from agentscope.message import Msg
from agentscope.pipeline._functional import fanout_pipeline


def check_winning(
    alive_agents: list,
    wolf_agents: list,
    host: str,
) -> tuple[bool, Msg | None]:
    """check which group wins"""
    if len(wolf_agents) * 2 >= len(alive_agents):
        msg = Msg(host, Prompts.to_all_wolf_win, role="assistant")
        return True, msg
    if alive_agents and not wolf_agents:
        msg = Msg(host, Prompts.to_all_village_win, role="assistant")
        return True, msg
    return False, None


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
    votes_valid = [item for item in votes if item != "Abstain"]
    # Count the votes excluding abstentions.
    unit, counts = np.unique(votes_valid, return_counts=True)
    return unit[np.argmax(counts)]


def extract_name_and_id(name: str) -> tuple[str, int]:
    """extract player name and id from a string"""
    try:
        name = re.search(r"\b[Pp]layer\d+\b", name).group(0)
        idx = int(re.search(r"[Pp]layer(\d+)", name).group(1)) - 1
    except AttributeError:
        # In case Player remains silent or speaks to abstain.
        logger.warning("vote: invalid name %s, set to Abstain", name)
        name = "Abstain"
        idx = -1
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


def turn_off_stream(agents: Sequence[ReActAgent]) -> None:
    """turn off stream for all agents"""
    for agent in agents:
        agent.model.stream = False


def turn_on_stream(agents: list[ReActAgent]) -> None:
    """turn on stream for all agents"""
    for agent in agents:
        agent.model.stream = True


async def collect_votes(
    voters: list[ReActAgent],
    hint: Msg,
    structured_model: Type[BaseModel],
) -> list[str]:
    """collect votes from voters"""
    turn_off_stream(voters)

    wolves_vote_results = await fanout_pipeline(
        voters,
        hint,
        structured_model=structured_model,
    )
    turn_on_stream(voters)
    votes = [
        extract_name_and_id(result.metadata["name"])[0]
        for result in wolves_vote_results
    ]
    return votes


class WolfDiscussionModel(BaseModel):
    """wolf discussion model"""

    thought: str = Field(description="What you thought")
    speak: str = Field(description="What you said")
    finish_discussion: bool = Field(
        description="Whether you have finished discussing",
    )


class VoteModel(BaseModel):
    """wolf vote model"""

    name: str = Field(description="The name you vote for")


class SeerModel(BaseModel):
    """seer model"""

    name: str = Field(description="The name you want to know the role of")


class WitchResurrectModel(BaseModel):
    """witch resurrect model"""

    name: str = Field(description="The name you want to resurrect")
    resurrect: bool = Field(
        description="Whether you want to resurrect the player",
    )


class WitchPoisonModel(BaseModel):
    """witch poison model"""

    name: str = Field(description="The name you want to poison")
    poison: bool = Field(description="Whether you want to poison the player")
