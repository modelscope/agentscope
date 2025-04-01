# -*- coding: utf-8 -*-
"""An example of how to use AutoServiceToolkit with ReAct agent."""
import os
from loguru import logger
from agentscope.agents import ReActAgent
from agentscope.service import (
    AutoServiceToolkit,
)
import agentscope
from agentscope.message import Msg


YOUR_MODEL_CONFIGURATION_NAME = "dashscope_config"
YOUR_MODEL_CONFIGURATION = {
    "model_type": "dashscope_chat",
    "config_name": YOUR_MODEL_CONFIGURATION_NAME,
    "api_key": os.getenv("DASHSCOPE_API_KEY"),
    "model_name": "qwen-max",
}

agentscope.init(
    model_configs=YOUR_MODEL_CONFIGURATION,
    project="Conversation with ReActAgent",
    save_api_invoke=True,
)

task = "Get the latest news of Alibaba and analysis its focuses"

logger.info(f"Task: {task}")
task_msg = Msg(
    role="user",
    name="user",
    content=task,
)

# Prepare the tools for the agent
model_based_service_toolkit = AutoServiceToolkit(
    model_config_name="dashscope_config",
    confirm_install=True,
)

model_free_service_toolkit = AutoServiceToolkit(
    model_free=True,
    confirm_install=True,
)

# Create agent with model-based service toolkit
agent1 = ReActAgent(
    name="assistant",
    model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
    verbose=True,
    service_toolkit=model_based_service_toolkit,
)

print("=" * 10, "Model-base AutoToolkit", "=" * 10)
print(agent1(task_msg))

# Create agent with model-free service toolkit
agent2 = ReActAgent(
    name="assistant",
    model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
    verbose=True,
    service_toolkit=model_free_service_toolkit,
)

print("=" * 10, "Model-free AutoToolkit", "=" * 10)
print(agent2(task_msg))
