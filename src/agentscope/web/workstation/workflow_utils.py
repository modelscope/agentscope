# -*- coding: utf-8 -*-
"""Workflow node utils."""


def is_callable_expression(s: str) -> bool:
    """Check a expression whether a callable expression"""
    try:
        # Do not detect exp like this
        if s in ["input", "print"]:
            return False
        result = eval(s)
        return callable(result)
    except Exception:
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


def deps_converter(dep_vars: list) -> str:
    """Convert a dep_vars list to a string."""
    return f"[{', '.join(dep_vars)}]"


def dict_converter(dictionary: dict) -> str:
    """Convert a dictionary to a string."""
    result_parts = []
    for key, value in dictionary.items():
        result_parts.append(f'"{key}": {value}')
    return "{" + ", ".join(result_parts) + "}"
