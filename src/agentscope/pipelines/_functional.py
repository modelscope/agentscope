# -*- coding: utf-8 -*-
"""Functional counterpart for Pipeline"""
from typing import (
    Callable,
    Optional,
    Union,
)

from ..message import Msg


def sequential_pipeline(
    operators: list[
        Callable[
            [Union[None, Msg, list[Msg]]],
            Union[None, Msg, list[Msg]],
        ]
    ],
    x: Optional[Union[Msg, list[Msg]]] = None,
) -> Union[None, Msg, list[Msg]]:
    """A syntactic sugar pipeline that executes a sequence of operators
    sequentially. The output of the previous operator will be passed as the
    input to the next operator. The final output will be the output of the
    last operator.

    Example:
        .. code-block:: python

            agent1 = DialogAgent(...)
            agent2 = DialogAgent(...)
            agent3 = DialogAgent(...)

            msg_input = Msg("user", "Hello", "user")

            msg_output = sequential_pipeline(
                [agent1, agent2, agent3],
                msg_input
            )

    Args:
        operators (`list[Callable[[Union[None, Msg, list[Msg]]],
        Union[None, Msg, list[Msg]]]`):
            A list of operators, which can be agent, pipeline or any callable
            that takes `Msg` object(s) as input and returns `Msg` object or
            `None`
        x (`Optional[Union[Msg, list[Msg]]]`, defaults to `None`):
            The initial input that will be passed to the first operator.

    Returns:
        `Union[None, Msg, list[Msg]]`:
            The output of the last operator in the sequence.
    """
    if len(operators) == 0:
        raise ValueError("No operators provided.")

    msg = operators[0](x)
    for operator in operators[1:]:
        msg = operator(msg)
    return msg
