# -*- coding: utf-8 -*-
""" Base class for Pipeline """

from typing import Callable, Sequence
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from abc import abstractmethod

from .functional import (
    Operators,
    placeholder,
    sequentialpipeline,
    ifelsepipeline,
    switchpipeline,
    forlooppipeline,
    whilelooppipeline,
)
from ..agents.operator import Operator


class PipelineBase(Operator):
    r"""Base interface of all pipelines.

    The pipeline is a special kind of operator that includes
    multiple operators and the interaction logic among them.
    """

    def __init__(self) -> None:
        self.participants: List[Any] = []

    @abstractmethod
    def __call__(self, x: Optional[dict] = None) -> dict:
        """Define the actions taken by this pipeline.

        Args:
            x (Optional[`dict`], optional):
                Dialog history and some environment information

        Returns:
            `dict`: The pipeline's response to the input.
        """


class IfElsePipeline(PipelineBase):
    r"""A template pipeline for implementing control flow like if-else.

    IfElsePipeline(condition_func, if_body_operators, else_body_operators)
    represents the following workflow::

        if condition_func(x):
            if_body_operators(x)
        else:
            else_body_operators(x)
    """

    def __init__(
        self,
        condition_func: Callable[[dict], bool],
        if_body_operators: Operators,
        else_body_operators: Operators = placeholder,
    ) -> None:
        r"""Initialize an IfElsePipeline.

        Args:
            condition_func (`Callable[[dict], bool]`):
                A function that determines whether to execute
                if_body_operators or else_body_operators based on the input x.
            if_body_operators (`Operators`):
                Operators executed when condition_func returns True.
            else_body_operators (`Operators`):
                Operators executed when condition_func returns False,
                does nothing and just return the input by default.
        """
        self.condition_func = condition_func
        self.if_body_operator = if_body_operators
        self.else_body_operator = else_body_operators
        self.participants = [self.if_body_operator] + [self.else_body_operator]

    def __call__(self, x: Optional[dict] = None) -> dict:
        return ifelsepipeline(
            condition_func=self.condition_func,
            if_body_operators=self.if_body_operator,
            else_body_operators=self.else_body_operator,
            x=x,
        )


class SwitchPipeline(PipelineBase):
    r"""A template pipeline for implementing control flow like switch-case.

    SwitchPipeline(condition_func, case_operators, default_operators)
    represents the following workflow::

        switch condition_func(x):
            case k1: return case_operators[k1](x)
            case k2: return case_operators[k2](x)
            ...
            default: return default_operators(x)
    """

    def __init__(
        self,
        condition_func: Callable[[dict], Any],
        case_operators: Mapping[Any, Operators],
        default_operators: Operators = placeholder,
    ) -> None:
        """Initialize a SwitchPipeline.

        Args:
            condition_func (`Callable[[dict], Any]`):
                A function that determines which case_operator to execute
                based on the input x.
            case_operators (`dict[Any, Operators]`):
                A dictionary containing multiple operators and their
                corresponding trigger conditions.
            default_operators (`Operators`, defaults to `placeholder`):
                Operators that are executed when the actual condition do
                not meet any of the case_operators, does nothing and just
                return the input by default.
        """
        self.condition_func = condition_func
        self.case_operators = case_operators
        self.default_operators = default_operators
        self.participants = list(self.case_operators.values()) + [
            self.default_operators,
        ]

    def __call__(self, x: Optional[dict] = None) -> dict:
        return switchpipeline(
            condition_func=self.condition_func,
            case_operators=self.case_operators,
            default_operators=self.default_operators,
            x=x,
        )


class ForLoopPipeline(PipelineBase):
    r"""A template pipeline for implementing control flow like for-loop

    ForLoopPipeline(loop_body_operators, max_loop) represents the following
    workflow::

        for i in range(max_loop):
            x = loop_body_operators(x)

    ForLoopPipeline(loop_body_operators, max_loop, break_func)
    represents the following workflow::

        for i in range(max_loop):
            x = loop_body_operators(x)
            if break_func(x):
                break
    """

    def __init__(
        self,
        loop_body_operators: Operators,
        max_loop: int,
        break_func: Callable[[dict], bool] = lambda _: False,
    ):
        r"""Initialize a ForLoopPipeline.

        Args:
            loop_body_operators (`Operators`):
                Operators executed as the body of the loop.
            max_loop (`int`):
                Maximum number of loop executions.
            break_func (`Callable[[dict], bool]`, defaults to `lambda _:
            False`):
                A function used to determine whether to break out of the
                loop based on the output of the loop_body_operators.
        """
        self.loop_body_operators = loop_body_operators
        self.max_loop = max_loop
        self.break_func = break_func
        self.participants = [self.loop_body_operators]

    def __call__(self, x: Optional[dict] = None) -> dict:
        return forlooppipeline(
            loop_body_operators=self.loop_body_operators,
            max_loop=self.max_loop,
            break_func=self.break_func,
            x=x,
        )


class WhileLoopPipeline(PipelineBase):
    r"""A template pipeline for implementing control flow like while-loop

    WhileLoopPipeline(loop_body_operators, condition_operator, condition_func)
    represents the following workflow::

        i = 0
        while (condition_func(i, x))
            x = loop_body_operators(x)
            i += 1
    """

    def __init__(
        self,
        loop_body_operators: Operators,
        condition_func: Callable[[int, dict], bool] = lambda _, __: False,
    ):
        """Initialize a WhileLoopPipeline.

        Args:
            loop_body_operators (`Operators`):
                Operators executed as the body of the loop.
            condition_func (`Callable[[int, dict], bool]`, defaults to
            `lambda _, __: False`):
                A function that determines whether to continue executing the
                loop body based on the current loop number and output of the
                `loop_body_operator`
        """
        self.condition_func = condition_func
        self.loop_body_operators = loop_body_operators
        self.participants = [self.loop_body_operators]

    def __call__(self, x: Optional[dict] = None) -> dict:
        return whilelooppipeline(
            loop_body_operators=self.loop_body_operators,
            condition_func=self.condition_func,
            x=x,
        )


class SequentialPipeline(PipelineBase):
    r"""A template pipeline for implementing sequential logic.

    Sequential(operators) represents the following workflow::

        x = operators[0](x)
        x = operators[1](x)
        ...
        x = operators[n](x)
    """

    def __init__(self, operators: Sequence[Operator]) -> None:
        r"""Initialize a Sequential pipeline.

        Args:
            operators (`Sequence[Operator]`):
                A Sequence of operators to be executed sequentially.
        """
        self.operators = operators
        self.participants = list(self.operators)

    def __call__(self, x: Optional[dict] = None) -> dict:
        return sequentialpipeline(operators=self.operators, x=x)
