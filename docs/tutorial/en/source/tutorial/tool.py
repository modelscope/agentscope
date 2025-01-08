# -*- coding: utf-8 -*-
"""
.. _tools:

Tools
====================

In this tutorial we show how to use the built-in tools in AgentScope and
how to create custom tools.
"""
import json

import agentscope
from agentscope.message import Msg

# %%
# Using Built-in Tools
# --------------------------
# AgentScope provides a `ServiceToolkit` module that supports
#
# - tool introduction generation,
# - a default call format,
# - response parsing, tools calling and agent-oriented error handling.
#
# Before using `ServiceToolkit`, we can take a look at the available tools in
# the `agentscope.service` module.

from agentscope.service import get_help, ServiceResponse, ServiceExecStatus

get_help()

# %%
# All above functions are implemented as Python functions.
# They can be registered to the `ServiceToolkit` by calling the `add` method.

from agentscope.service import ServiceToolkit
from agentscope.service import bing_search, execute_shell_command

toolkit = ServiceToolkit()
toolkit.add(execute_shell_command)

# Note some parameters of the tool functions (e.g. api_key) should be handled
# by developers.
# You can directly pass these parameters as keyword arguments in the add
# method as follows, the reserved parameters will be left to the agent to fill.

toolkit.add(bing_search, api_key="xxx")

print("The tools instruction:")
print(toolkit.tools_instruction)

# %%
# The built-in default calling format:

print(toolkit.tools_calling_format)

# %%
# The JSON Schema description of the tool functions:

print(json.dumps(toolkit.json_schemas, indent=2))


# %%

# %%
# After assembling the `ServiceToolkit`, you can integrate it into agent.
# In AgentScope, we provide a `ReActAgent` to handle the tool usage, you can
# directly pass the `ServiceToolkit` object into this agent.
# Refer to [] for implementation details of this agent.

from agentscope.agents import ReActAgent

agentscope.init(
    model_configs={
        "config_name": "my-qwen-max",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
    },
)

agent = ReActAgent(
    name="Friday",
    model_config_name="my-qwen-max",
    service_toolkit=toolkit,
    sys_prompt="You're a helpful assistant named Friday.",
)

msg_task = Msg("user", "Help me to calculate 1615114134*4343434343", "user")

res = agent(msg_task)


# %%
# Creating Custom Tools
# --------------------------
# A custom tool function must follow these rules:
#
# - Typing for arguments
# - Well-written docstring in Google style
# - The return of the function must be wrapped by `ServiceResponse`


def new_function(arg1: str, arg2: int) -> ServiceResponse:
    """A brief introduction of this function in one line.

    Args:
        arg1 (`str`):
            Brief description of arg1
        arg2 (`int`):
            Brief description of arg2
    """
    return ServiceResponse(
        status=ServiceExecStatus.SUCCESS,
        content="Done!",
    )
