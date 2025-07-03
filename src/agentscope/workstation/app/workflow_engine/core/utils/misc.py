# -*- coding: utf-8 -*-
"""
This module provides utility functions for handling placeholders, formatting
intermediate results, and other miscellaneous tasks in a workflow system.
"""
import re
from typing import Any, Dict, List, Optional

from ..constant import PATTERN


def extract_placeholders(
    text: str,
    pattern: str = PATTERN,
) -> List[str]:
    """
    Extracts placeholder variables from a string using a specific pattern.
    """
    matches = re.findall(pattern, text)
    return matches


def extract_single_placeholder_fullmatch(
    text: str,
    pattern: str = PATTERN,
) -> Optional[str]:
    """
    Extracts a single placeholder variable from a string using a specific
    pattern, ensuring that the match is a full match and only one
    placeholder is extracted.

    Args:
    - text (str): The input string to search for the placeholder.
    - pattern (str): The regex pattern to use for matching the placeholder.

    Returns:
    - Optional[str]: The extracted placeholder if there is exactly one full
        match, otherwise None.
    """
    # Use fullmatch to ensure the entire string matches the pattern
    match = re.fullmatch(pattern, text)
    if match:
        # Check if exactly one group is captured and return it
        if len(match.groups()) == 1:
            return match.group(1)
    return None


def extract_value_from_format_map(
    format_map: Dict[str, Any],
    key: str,
) -> Any:
    """
    Extract a value from the format map using a key that might include array
    indexing. If an index is out of bounds, return the first or last element
    of the list.

    If not match, return None, otherwise return matched value.
    """
    matched = re.match(r"^(.*)\[(\d+)\]$", key)

    # Do not match index format
    if not matched:
        return get_value_from_dict(format_map, key)

    base_key, index = matched.groups()
    value = get_value_from_dict(format_map, base_key)

    if isinstance(value, (list, str)) and index is not None:
        try:
            index = int(index)
            if -len(value) <= index < len(value):
                return value[index]
            elif index < -len(value):
                return value[0]  # Return the first element
            else:
                return value[-1]  # Return the last element
        except ValueError:
            pass

    return value


def replace_placeholders(
    element: Any,
    format_map: Dict[str, Any],
    pattern: str = PATTERN,
) -> Any:
    """
    Replaces placeholders in a data structure with corresponding values
    from a format map.
    """
    # TODO: consider remove placeholder if not matches
    if isinstance(element, list):
        return [
            replace_placeholders(item, format_map, pattern) for item in element
        ]

    if isinstance(element, dict):
        return {
            key: replace_placeholders(value, format_map, pattern)
            for key, value in element.items()
        }

    if not isinstance(element, str):
        return element

    matches = extract_placeholders(element, pattern)

    # Replace placeholders with pattern one by one.
    for matched in matches:
        replacement = extract_value_from_format_map(format_map, matched)

        if replacement is not None:
            element = element.replace(
                generate_f_string(pattern, matched),
                f"{replacement}",
            )

            # Fully matched, do not change the data type
            if element == f"{replacement}":
                return replacement

    return element


def remove_placeholders(
    element: Any,
    pattern: str = PATTERN,
) -> Any:
    """
    Removes placeholders from a data structure.
    """
    if isinstance(element, list):
        return [remove_placeholders(item, pattern) for item in element]

    if isinstance(element, dict):
        return {
            key: remove_placeholders(value, pattern)
            for key, value in element.items()
        }

    if not isinstance(element, str):
        return element

    matches = extract_placeholders(element, pattern)

    # Remove placeholders with pattern
    for matched in matches:
        element = element.replace(generate_f_string(pattern, matched), "")

    return element


def find_value_placeholders(
    element: Any,
    pattern: str = PATTERN,
) -> List[str]:
    """
    Finds all placeholders in the values of a data structure and returns
    them as a list.
    """
    placeholders = set()

    if isinstance(element, list):
        for item in element:
            placeholders.update(find_value_placeholders(item, pattern=pattern))

    elif isinstance(element, dict):
        for value in element.values():
            placeholders.update(
                find_value_placeholders(value, pattern=pattern),
            )

    elif isinstance(element, str):
        matches = extract_placeholders(element, pattern)
        placeholders.update(matches)

    return list(placeholders)


def parse_dot_separated_string(s: Any) -> List[str]:
    """
    Parses a dot-separated string into its components.
    """
    if not isinstance(s, str):
        return []

    parts = s.split(".")

    if len(parts) == 3:
        return parts
    else:
        return []


def generate_f_string(pattern: str, matched: str) -> str:
    """
    Generates a formatted string by replacing placeholders in a regex
    pattern with a matched string.

    Args:
        pattern (str): The regex pattern containing placeholders.
        matched (str): The string to replace placeholders with.

    Returns:
        str: The formatted string with placeholders replaced by the matched
        string.
    """
    regex = re.compile(pattern)
    f_string = regex.pattern.replace(r"(.*?)", f"{matched}")
    f_string = f_string.replace("\\", "")
    return f_string


def convert_to_fstring_format(code: str, pattern: str = PATTERN) -> str:
    """
    Converts a code string by replacing placeholders with f-string format.

    Args:
        code (str): The code string to be converted, potentially containing
            placeholders.
        pattern (str, optional): The regex pattern used to identify
            placeholders within the string.

    Returns:
        str: The code string converted with f-string format applied to
        matched placeholders.
    """

    def replace_match(matched: re.Match) -> str:
        """Replaces the matched placeholder with f-string format."""
        # TODO: use self-defined pattern may cause error
        return f"{{${{{matched.group(1)}}}}}"

    def replace_in_quotes(matched: re.Match) -> str:
        """Replaces placeholders within quoted strings with f-string format."""
        quote = matched.group("quote")
        inner = matched.group("inner")

        # Check if the inner text contains any ${...} pattern
        if re.search(pattern, inner):
            replaced_inner_text = re.sub(pattern, replace_match, inner)
            return f"f{quote}{replaced_inner_text}{quote}"
        else:
            # Return the string as is if no pattern is found
            return matched.group(0)

    match_pattern = r"""
    (?:f)?
    (?P<quote>['"]{3}|['"])
    (?P<inner>.*?)
    (?P=quote)
"""

    # Adjusted regex to capture strings with any number of quotes (single or
    # triple quotes) and across multiple lines
    converted_code = re.sub(
        match_pattern,
        replace_in_quotes,
        code,
        flags=re.VERBOSE | re.DOTALL,
    )
    return converted_code


def get_value_from_dict(d: Dict[str, Any], key: str) -> Optional[Any]:
    """
    Retrieves a value from a nested dictionary using a dot-separated key
    string.

    Args:
        d (Dict[str, Any]): The dictionary to search, which may contain
            nested dictionaries.
        key (str): A dot-separated string representing the path to the
            desired value in the dictionary.

    Returns:
        Optional[Any]: The value from the dictionary corresponding to the
            given key, or None if the key is not found.
    """
    keys = key.split(".")
    current_key = key
    if current_key in d:
        return d[current_key]

    for i in range(len(keys) - 1, 0, -1):
        current_key = ".".join(keys[:i])
        remaining_key = ".".join(keys[i:])

        if current_key in d:
            sub_dict = d[current_key]
            if isinstance(sub_dict, dict) and remaining_key in sub_dict:
                return sub_dict[remaining_key]

    return None


def format_output(data: Any) -> str:
    """
    Formats various data structures into a string representation.

    This function recursively formats dictionaries, lists, and other data types
    into a string format that resembles Python literals.

    Args:
        data (Any): The data to format, which can be of any type.

    Returns:
        str: A string representation of the input data.
    """
    if isinstance(data, dict):
        formatted_items = [
            f"'{key}': {format_output(value)}" for key, value in data.items()
        ]
        return "{" + ", ".join(formatted_items) + "}"

    elif isinstance(data, list):
        formatted_items = [format_output(item) for item in data]
        return "[" + ", ".join(formatted_items) + "]"

    elif isinstance(data, str):
        return data

    else:
        return str(data)
