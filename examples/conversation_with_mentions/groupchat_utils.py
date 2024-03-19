# -*- coding: utf-8 -*-
""" Group chat utils."""
import re
from typing import Sequence


def select_next_one(agents: Sequence, rnd: int) -> Sequence:
    """
    Select next agent.
    """
    return agents[rnd % len(agents)]


def filter_agents(string: str, agents: Sequence) -> Sequence:
    """
    This function filters the input string for occurrences of the given names
    prefixed with '@' and returns a list of the found names.
    """
    if len(agents) == 0:
        return []

    # Create a pattern that matches @ followed by any of the candidate names
    pattern = (
        r"@(" + "|".join(re.escape(agent.name) for agent in agents) + r")\b"
    )

    # Find all occurrences of the pattern in the string
    matches = re.findall(pattern, string)

    # Create a dictionary mapping agent names to agent objects for quick lookup
    agent_dict = {agent.name: agent for agent in agents}

    # Return the list of matched agent objects preserving the order
    ordered_agents = [
        agent_dict[name] for name in matches if name in agent_dict
    ]
    return ordered_agents
