# -*- coding: utf-8 -*-
"""Interface for compile workflow to python code."""
from typing import Generator, Any


# pylint: disable=unused-argument
def exec_optimizer(**kwargs: Any) -> Generator:
    """
    A generator function for optimize workflow config.
    """
    yield
    raise NotImplementedError
