# -*- coding: utf-8 -*-
"""
.. _tools:

工具
====================

在本教程中，我们将展示如何使用 AgentScope 中内置的工具函数，以及如何创建自定义工具函数。
"""
import json

import agentscope
from agentscope.message import Msg

# %%
# 内置工具函数
# --------------------------
# AgentScope 提供了一个 `ServiceToolkit` 模块，支持以下功能:
#
# - 工具介绍生成,
# - 提供一套默认的调用格式,
# - 模型返回值解析、工具调用和面向智能体的错误处理。
#
# 在使用 `ServiceToolkit` 之前,我们可以先看一下 `agentscope.service` 模块中可用的工具。
#

from agentscope.service import get_help, ServiceResponse, ServiceExecStatus

get_help()

# %%
# 以上所有函数都是用 Python 函数实现的。
# 可以通过调用 `add` 方法注册到 `ServiceToolkit` 中。
#

from agentscope.service import ServiceToolkit
from agentscope.service import bing_search, execute_shell_command

toolkit = ServiceToolkit()
toolkit.add(execute_shell_command)

# 注意,一些工具函数的参数（例如 api_key）应该由开发人员处理。
# 你可以直接在 add 方法中以关键字参数的形式传递这些参数，保留其他参数留给智能体填写。

toolkit.add(bing_search, api_key="xxx")

print("工具说明:")
print(toolkit.tools_instruction)

# %%
# 在 ServiceToolkit 中使用 MCP
# -------------------------------
# AgentScope 支持集成 MCP (Model Context Protocol) 服务器，使模型和工具具有增强的功能。
# 您可以使用 `add_mcp_servers` 方法将 MCP 服务器添加到 `ServiceToolkit` 中，并在其中指定每个服务器的配置。
# 请注意，MCP 要求 Python 版本>=3.10。

configs = {
    "mcpServers": {
        "puppeteer": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        },
    },
}

# 将 MCP 服务器配置添加到 ServiceToolkit
# `toolkit.add_mcp_servers(server_configs=configs)`

# %%
# 内置的默认调用格式:
#

print(toolkit.tools_calling_format)

# %%
# 自动生成的工具函数 JSON Schema 格式说明:
#
print(json.dumps(toolkit.json_schemas, indent=2))


# %%
# AgentScope 提供了 `ReActAgent` 智能体类来使用工具，只需要将 `ServiceToolkit` 对象传递给这个智能体。
# 有关该智能体的实现细节，请参阅 :ref:`builtin_agent`。
#

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
    sys_prompt="你是一个名为 Friday 的助手。",
)

msg_task = Msg("user", "帮我计算一下 1615114134*4343434343", "user")

res = agent(msg_task)

# 回收toolkit实例
del toolkit


# %%
# 创建工具函数
# --------------------------
# 自定义工具函数必须遵循以下规则:
#
# - 参数使用 typing 指定类型
# - 使用 Google 风格书写完整的 docstring
# - 函数返回值必须用 `ServiceResponse` 包装
#


def new_function(arg1: str, arg2: int) -> ServiceResponse:
    """简单介绍该函数。

    Args:
        arg1 (`str`):
            对 arg1 的简单描述
        arg2 (`int`):
            对 arg2 的简单描述
    """
    return ServiceResponse(
        status=ServiceExecStatus.SUCCESS,
        content="完成!",
    )
