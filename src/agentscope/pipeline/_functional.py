# -*- coding: utf-8 -*-
"""Functional counterpart for Pipeline"""
import inspect
from typing import Type

from pydantic import BaseModel

from ..agent import AgentBase
from ..message import Msg


async def sequential_pipeline(
    agents: list[AgentBase],
    msg: Msg | list[Msg] | None = None,
    structured_model: Type[BaseModel] | None = None,
) -> Msg | list[Msg] | None:
    """An async syntactic sugar pipeline that executes a sequence of agents
    sequentially. The output of the previous agent will be passed as the
    input to the next agent. The final output will be the output of the
    last agent.

    Example:
        .. code-block:: python

            agent1 = ReActAgent(...)
            agent2 = ReActAgent(...)
            agent3 = ReActAgent(...)

            msg_input = Msg("user", "Hello", "user")

            msg_output = await sequential_pipeline(
                [agent1, agent2, agent3],
                msg_input
            )

            # Pipeline with structured output
            from pydantic import BaseModel

            class TaskResult(BaseModel):
                status: str
                result: str
                confidence: float

            structured_output = await sequential_pipeline(
                [agent1, agent2, agent3],
                msg_input,
                structured_model=TaskResult
            )

    Args:
        agents (`list[AgentBase]`):
            A list of agents.
        msg (`Msg | list[Msg] | None`, defaults to `None`):
            The initial input that will be passed to the first agent.
        structured_model (`Type[BaseModel] | None`, defaults to `None`):
            A Pydantic BaseModel class that defines the expected structure
            for the agents' output. When provided, each agent in the pipeline
            will be instructed to return data that conforms to this schema.
            This enables structured output generation throughout the entire
            pipeline execution.

            .. note:: The structured_model will be applied to each agent
                in the sequence.

    Returns:
        `Msg | list[Msg] | None`:
            The output of the last agent in the sequence.
    """
    for agent in agents:
        if structured_model is not None:
            reply_signature = inspect.signature(agent.reply)
            if "structured_model" in reply_signature.parameters:
                msg = await agent(msg, structured_model=structured_model)
            else:
                msg = await agent(msg)
        else:
            msg = await agent(msg)
    return msg
