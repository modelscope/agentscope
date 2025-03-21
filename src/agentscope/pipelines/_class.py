# -*- coding: utf-8 -*-
"""Pipeline classes."""

from typing import Callable, Union
from typing import Optional

from ._functional import sequential_pipeline
from ..message import Msg


class SequentialPipeline:
    """A sequential pipeline class, which executes a sequence of operators
    sequentially. Compared with functional pipeline, this class can be
    re-used."""

    def __init__(
        self,
        operators: list[
            Callable[
                [Union[None, Msg, list[Msg]]],
                Union[None, Msg, list[Msg]],
            ]
        ],
    ) -> None:
        """Initialize a sequential pipeline class

        Args:
            operators (`list[Callable[[Union[None, Msg, list[Msg]]],
            Union[None, Msg, list[Msg]]]`):
                A list of operators, which can be agent, pipeline or any
                callable that takes `Msg` object(s) as input and returns
                `Msg` object or `None`
        """
        self.operators = operators
        self.participants = list(self.operators)

    def __call__(
        self,
        x: Optional[Union[Msg, list[Msg]]],
    ) -> Union[Msg, list[Msg], None]:
        """Execute the sequential pipeline

        Args:
            x (`Optional[Union[Msg, list[Msg]]]`, defaults to `None`):
                The initial input that will be passed to the first operator.
        """
        return sequential_pipeline(operators=self.operators, x=x)
