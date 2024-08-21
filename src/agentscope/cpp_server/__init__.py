# -*- coding: utf-8 -*-
"""Related functions for cpp server."""

import json
import base64
from loguru import logger

try:
    import dill
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    dill = ImportErrorReporter(import_error, "distribute")

from agentscope.manager import ASManager
from agentscope.agents.agent import AgentBase


def init_process_with_str(init_settings_str):
    init_settings = json.loads(init_settings_str)
    ASManager.get_instance().load_dict(init_settings)


def register_agent_classes(custom_agent_classes_str: str) -> None:
    """Register agent classes."""
    if custom_agent_classes_str:
        custom_agent_classes = dill.loads(base64.b64decode(custom_agent_classes_str.encode()))
        for agent_class in custom_agent_classes:
            AgentBase.register_agent_class(agent_class=agent_class)


def create_agent(agent_id: str, agent_init_args: str, agent_source_code: str):
    agent_configs = dill.loads(agent_init_args)
    if len(agent_source_code) > 0:
        cls = dill.loads(agent_source_code)
        cls_name = cls.__name__
        logger.info(
            f"Load class [{cls_name}] from uploaded source code.",
        )
    else:
        cls_name = agent_configs["class_name"]
        try:
            cls = AgentBase.get_agent_class(cls_name)
        except ValueError as e:
            err_msg = (
                f"Agent class [{cls_name}] not found: {str(e)}",
            )
            logger.error(err_msg)
            return None, str(err_msg)
    try:
        agent_instance = cls(
            *agent_configs["args"],
            **agent_configs["kwargs"],
        )
        agent_instance._agent_id = agent_id  # pylint: disable=W0212
        logger.info(f"create agent instance <{cls_name}>[{agent_id}] [{agent_instance.name}]")
        return agent_instance, ""
    except Exception as e:
        err_msg = (
            f"Failed to create agent instance <{cls_name}>: {str(e)}",
        )
        logger.error(err_msg)
        return None, str(err_msg)
