# -*- coding: utf-8 -*-
"""The utilities for unit tests in AgentScope."""
from agentscope.manager import ModelManager, FileManager


def clean_singleton_instances() -> None:
    """Clean all singleton instances."""
    ModelManager.get_instance().clear_model_configs()
    FileManager.flush()
