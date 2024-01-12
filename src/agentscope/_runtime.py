# -*- coding: utf-8 -*-
"""Manage the id for each runtime"""
from agentscope.utils.tools import _get_timestamp
from agentscope.utils.tools import _generate_random_code

_RUNTIME_ID_FORMAT = "run_%Y%m%d-%H%M%S_{}"


class Runtime:
    """Used to record the runtime information."""

    project: str = None
    """The project name, which is used to identify the project."""

    name: str = None
    """The name for runtime, which is used to identify this runtime."""

    runtime_id: str = _get_timestamp(_RUNTIME_ID_FORMAT).format(
        _generate_random_code(),
    )
    """The id for runtime, which is used to identify the this runtime and
    name the saving directory."""
