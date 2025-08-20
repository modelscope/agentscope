# -*- coding: utf-8 -*-
"""
Constant for workflow engine.
"""
import os

try:
    # pylint: disable=invalid-envvar-default
    DEFAULT_RETRY_INTERVAL = int(os.getenv("DEFAULT_RETRY_INTERVAL", 15))
except ValueError:
    DEFAULT_RETRY_INTERVAL = 15

try:
    # pylint: disable=invalid-envvar-default
    DEFAULT_NODE_RETRY = int(os.getenv("DEFAULT_NODE_RETRY", 3))
except ValueError:
    DEFAULT_NODE_RETRY = 3


PATTERN = r"\$\{(.*?)\}"
