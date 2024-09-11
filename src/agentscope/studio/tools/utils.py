# -*- coding: utf-8 -*-
"""
This module provides utilities for studio tools.
"""
import os
from urllib.parse import urlparse


def is_url(path: str) -> bool:
    """
    Check if the provided path is a URL.

    Parameters:
    - path: The path to be checked.

    Returns:
    - bool: True if the path is a valid URL, False otherwise.
    """
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_local_file(path: str) -> bool:
    """
    Check if the provided path is a local file.

    Parameters:
    - path: The path to be checked.

    Returns:
    - bool: True if the path exists and is a file, False otherwise.
    """
    return os.path.isfile(path)
