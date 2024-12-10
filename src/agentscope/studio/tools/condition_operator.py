# -*- coding: utf-8 -*-
"""Condition operator"""
from agentscope.message import Msg


def eval_condition_operator(
    actual_value: str,
    operator: str,
    target_value: str = None,
) -> bool:
    """Eval condition operator only for Msg content or string"""
    if isinstance(actual_value, Msg):
        if hasattr(actual_value, "content"):
            actual_value = actual_value.content

    operator_funcs = {
        "contains": lambda: target_value in actual_value,
        "not contains": lambda: target_value not in actual_value,
        "start with": lambda: actual_value.startswith(target_value),
        "end with": lambda: actual_value.endswith(target_value),
        "equals": lambda: actual_value == target_value,
        "not equals": lambda: actual_value != target_value,
        "is empty": lambda: not bool(actual_value),
        "is not empty": lambda: bool(actual_value),
        "is null": lambda: actual_value is None,
        "is not null": lambda: actual_value is not None,
    }

    if operator in operator_funcs:
        return operator_funcs[operator]()
    else:
        raise ValueError(f"Invalid condition operator: {operator}")
