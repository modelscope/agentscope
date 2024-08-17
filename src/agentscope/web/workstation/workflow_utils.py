# -*- coding: utf-8 -*-
"""Workflow node utils."""
import ast
import builtins

from typing import Any


def is_callable_expression(value: str) -> bool:
    """
    Check if the given string could represent a callable expression
    (including lambda and built-in functions).
    """
    try:
        # Attempt to parse the expression using the AST module
        node = ast.parse(value, mode='eval')

        # Check for callable expressions
        if isinstance(node.body, (ast.Call, ast.Lambda)):
            return True

        if isinstance(node.body, ast.Name):
            # Exclude undesired built-in functions
            excluded_builtins = {"input", "print"}
            if node.body.id in excluded_builtins:
                return False
            return node.body.id in dir(builtins)

        return False
    except (SyntaxError, ValueError):
        return False


def kwarg_converter(kwargs: dict) -> str:
    """Convert a kwarg dict to a string."""
    kwarg_parts = []
    for key, value in kwargs.items():
        if is_callable_expression(value):
            kwarg_parts.append(f"{key}={value}")
        else:
            kwarg_parts.append(f"{key}={repr(value)}")
    return ", ".join(kwarg_parts)


def convert_str_to_callable(item) -> Any:
    """Convert a str to callable if it can be called."""
    if is_callable_expression(item):
        return eval(item)
    return item


def deps_converter(dep_vars: list) -> str:
    """Convert a dep_vars list to a string."""
    return f"[{', '.join(dep_vars)}]"


def dict_converter(dictionary: dict) -> str:
    """Convert a dictionary to a string."""
    result_parts = []
    for key, value in dictionary.items():
        result_parts.append(f'"{key}": {value}')
    return "{" + ", ".join(result_parts) + "}"
