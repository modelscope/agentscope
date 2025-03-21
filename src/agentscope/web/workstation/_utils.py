# -*- coding: utf-8 -*-
"""The utility functions for the workstation."""
from typing import (
    Callable,
    Union,
    Optional,
    Any,
    Mapping,
)

from agentscope.message import Msg
from agentscope.pipelines import sequential_pipeline


_Operators = Union[Callable, list[Callable]]


def _placeholder(x: dict = None) -> dict:
    """A placeholder that do nothing."""
    return x


def _operators(
    operators: _Operators,
    x: Optional[Msg] = None,
) -> Msg:
    """Syntactic sugar for executing a single operator or a sequence of
    operators."""
    if isinstance(operators, list):
        return sequential_pipeline(operators, x)
    elif operators is None:
        return x
    else:
        return operators(x)


def _if_else_pipeline(
    condition_func: Callable,
    if_body_operators: _Operators,
    else_body_operators: _Operators = _placeholder,
    x: Optional[Msg] = None,
) -> Msg:
    """Functional version of IfElsePipeline"""
    if condition_func(x):
        return _operators(if_body_operators, x)
    else:
        return _operators(else_body_operators, x)


def _switch_pipeline(
    condition_func: Callable[[Any], Any],
    case_operators: Mapping[Any, _Operators],
    default_operators: _Operators = _placeholder,
    x: Optional[dict] = None,
) -> Msg:
    """Functional version of SwitchPipeline."""
    target_case = condition_func(x)
    if target_case in case_operators:
        return _operators(case_operators[target_case], x)
    else:
        return _operators(default_operators, x)


def _for_loop_pipeline(
    loop_body_operators: _Operators,
    max_loop: int,
    break_func: Callable[[Msg], bool] = lambda _: False,
    x: Optional[Msg] = None,
) -> Msg:
    """Functional version of ForLoopPipeline."""
    for _ in range(max_loop):
        # loop body
        x = _operators(loop_body_operators, x)
        # check condition
        if break_func(x):
            break
    return x  # type: ignore[return-value]


def _while_loop_pipeline(
    loop_body_operators: _Operators,
    condition_func: Callable[[int, Any], bool] = lambda _, __: False,
    x: Optional[Msg] = None,
) -> Msg:
    """Functional version of WhileLoopPipeline."""
    i = 0
    while condition_func(i, x):
        # loop body
        x = _operators(loop_body_operators, x)
        # check condition
        i += 1
    return x


class _IfElsePipeline:
    """IF-else pipeline class."""

    def __init__(
        self,
        condition_func: Callable,
        if_body_operators: Union[Callable, list[Callable]],
        else_body_operators: Union[Callable, list[Callable]] = _placeholder,
    ) -> None:
        """Initialize IfElsePipeline class."""
        self.condition_func = condition_func
        self.if_body_operator = if_body_operators
        self.else_body_operator = else_body_operators
        self.participants = [self.if_body_operator] + [self.else_body_operator]

    def __call__(self, x: Optional[Msg] = None) -> Msg:
        return _if_else_pipeline(
            condition_func=self.condition_func,
            if_body_operators=self.if_body_operator,
            else_body_operators=self.else_body_operator,
            x=x,
        )


class _SwitchPipeline:
    """Switch pipeline class."""

    def __init__(
        self,
        condition_func: Callable[[dict], Any],
        case_operators: Mapping[Any, Union[Callable, list[Callable]]],
        default_operators: Union[Callable, list[Callable]] = _placeholder,
    ) -> None:
        """Initialize SwitchPipeline class."""
        self.condition_func = condition_func
        self.case_operators = case_operators
        self.default_operators = default_operators
        self.participants = list(self.case_operators.values()) + [
            self.default_operators,
        ]

    def __call__(self, x: Optional[Msg] = None) -> Msg:
        return _switch_pipeline(
            condition_func=self.condition_func,
            case_operators=self.case_operators,
            default_operators=self.default_operators,
            x=x,
        )


class _ForLoopPipeline:
    """For loop pipeline class."""

    def __init__(
        self,
        loop_body_operators: Union[Callable, list[Callable]],
        max_loop: int,
        break_func: Callable[[Msg], bool] = lambda _: False,
    ):
        """Initialize ForLoopPipeline class."""
        self.loop_body_operators = loop_body_operators
        self.max_loop = max_loop
        self.break_func = break_func
        self.participants = [self.loop_body_operators]

    def __call__(self, x: Optional[Msg] = None) -> Msg:
        return _for_loop_pipeline(
            loop_body_operators=self.loop_body_operators,
            max_loop=self.max_loop,
            break_func=self.break_func,
            x=x,
        )


class _WhileLoopPipeline:
    """While loop pipeline class."""

    def __init__(
        self,
        loop_body_operators: Union[Callable, list[Callable]],
        condition_func: Callable[[int, Msg], bool] = lambda _, __: False,
    ):
        """Initialize WhileLoopPipeline class"""
        self.condition_func = condition_func
        self.loop_body_operators = loop_body_operators
        self.participants = [self.loop_body_operators]

    def __call__(self, x: Optional[Msg] = None) -> Msg:
        return _while_loop_pipeline(
            loop_body_operators=self.loop_body_operators,
            condition_func=self.condition_func,
            x=x,
        )
