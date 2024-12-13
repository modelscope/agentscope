# -*- coding: utf-8 -*-
"""Workflow node utils."""
import ast
import builtins
import re

from typing import Any


def is_callable_expression(value: str) -> bool:
    """
    Check if the given string could represent a callable expression
    (including lambda and built-in functions).
    """
    try:
        if not isinstance(value, str):
            return False

        # Attempt to parse the expression using the AST module
        node = ast.parse(value, mode="eval")

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


def convert_str_to_callable(item: str) -> Any:
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


def replace_flow_name(
    string: str,
    output_value: str,
    input_values: list,
) -> str:
    """Replaces 'flow' based on its position relative to an equals sign,
    treating occurrences on both sides independently."""

    def format_replace_value(value: str) -> str:
        """Concatenates 'flow_' prefix with value, or 'flow' for empty
        value."""
        return f"flow_{value}" if value else "flow"

    # Prepare the replacement values
    output_value_formatted = format_replace_value(output_value)
    formatted_input_values = (
        [format_replace_value(value) for value in input_values]
        if input_values
        else ["flow"]
    )

    # Split the string by the first equals sign, if present
    parts = string.split("=", 1)
    left_part = parts[0] if parts else ""
    right_part = parts[1] if len(parts) > 1 else ""

    # Replace 'flow' on the left side of '=' with the output_value_formatted
    left_part = re.sub(
        r"\bflow\b",
        output_value_formatted,
        left_part,
        count=1,
    )

    # Replace 'flow' on the right side of '=' with the formatted input
    # values string
    if "flow" in right_part:
        input_values_str = ", ".join(formatted_input_values)
        # Here we replace all occurrences of 'flow' on the right side
        right_part = re.sub(r"\bflow\b", input_values_str, right_part)

    # Reassemble the string
    if len(parts) > 1:
        string = "=".join([left_part, right_part])
    else:
        string = left_part  # In case there was no '=' in the original string

    return string
