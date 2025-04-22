# -*- coding: utf-8 -*-
"""
.. _structured-output:

结构化输出
==========================

在本教程中，我们将构建一个简单的智能体，使用 `agentscope.parsers` 模块以 JSON 字典格式输出结构化数据。
"""
from agentscope.models import ModelResponse

# %%
# 定义解析器
# -------------------

from agentscope.parsers import MarkdownJsonDictParser


parser = MarkdownJsonDictParser(
    content_hint='{"thought": "你的想法", "speak": "你对用户说的话"}',
    required_keys=["thought", "speak"],
)


# %%
# 解析器将根据你的输入生成一个格式说明。你可以在提示中使用 `format_instruction` 属性来指导 LLM 生成所需的输出。

print(parser.format_instruction)

# %%
# 解析输出
# -------------------
# 当从 LLM 接收到输出时，使用 `parse` 方法来提取结构化数据。
# 它接受一个 `agentscope.models.ModelResponse` 对象作为输入，解析 `text` 字段的值，并在 `parsed` 字段中返回解析后的字典。

dummy_response = ModelResponse(
    text="""```json
{
    "thought": "我应该向用户打招呼",
    "speak": "嗨!我能为您做些什么?"
}
```""",
)

print(f"解析前parsed字段: {dummy_response.parsed}")

parsed_response = parser.parse(dummy_response)

print(f"解析后parsed字段: {parsed_response.parsed}")
print(type(parsed_response.parsed))

# %%
# 错误处理
# -------------------
# 如果LLM的输出与预期格式不匹配，解析器将抛出一个包含详细信息的错误。
# 因此开发人员可以将错误消息呈现给 LLM，以指导它纠正输出。
#

error_response = ModelResponse(
    text="""```json
{
    "thought": "我应该向用户打招呼"
}
```""",
)

try:
    parsed_response = parser.parse(error_response)
except Exception as e:
    print(e)

# %%
# 进阶用法
# -------------------
# 复杂结构化输出
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# 要求 LLM 直接生成 JSON 字典可能具有挑战性，特别是当 JSON 内容很复杂时（例如代码片段、嵌套结构）。
# 在这种情况下，你可以使用更高级的解析器来指导 LLM 生成所需的输出。
# 这里是一个更复杂的解析器示例，可以处理代码片段。
#

from agentscope.parsers import RegexTaggedContentParser

parser = RegexTaggedContentParser(
    format_instruction="""按以下格式作答:
<thought>你的想法</thought>
<number>这里放一个随机数字</number>
<code>你的python代码</code>
""",
    try_parse_json=True,  # 会尝试将每个键值解析为JSON对象，如果失败则保留为字符串
    required_keys=[  # 解析字典中的必需键
        "thought",
        "number",
        "code",
    ],
)

print(parser.format_instruction)

# %%
# `RegexTaggedContentParser` 支持使用正则表达式匹配文本中的标记内容并返回解析后的字典。
#
# .. note:: `RegexTaggedContentParser`的解析输出是一个字典，这意味着必需键应该是唯一的。
#  你也可以在初始化解析器时通过设置 `tagged_content_pattern` 参数来更改正则表达式模式。

import json

dummy_response = ModelResponse(
    text="""<thought>打印当前日期</thought>
<number>42</number>
<code>import datetime
print(datetime.datetime.now())
</code>
""",
)

parsed_response = parser.parse(dummy_response)

print("解析响应的类型: ", type(parsed_response.parsed))
print("number的类型: ", type(parsed_response.parsed["number"]))
print(json.dumps(parsed_response.parsed, indent=4, ensure_ascii=False))

# %%
# 自动后处理
# ^^^^^^^^^^^^^^^^^^^^
#
# 在解析后的字典中，不同的键可能需要不同的后处理步骤。
# 例如，在狼人杀游戏中，LLM 扮演预言家的角色，输出应该包含以下键值:
#
# - `thought`: 预言家的想法
# - `speak`: 预言家的发言
# - `use_ability`: 一个布尔值，表示预言家是否应该使用其能力
#
# 在这种情况下，`thought` 和 `speak` 内容应该存储在智能体的记忆中，以确保智能体行为/策略的一致性。
# `speak` 内容应该暴露给其它智能体或玩家。
# `use_ability` 键应该能在主流程中访问到，从而确定游戏下一步的操作（例如是否使用能力）。
#
# AgentScope 通过以下参数来自动对解析后的字典进行后处理。
#
# - `keys_to_memory`: 应存储在智能体记忆中的键
# - `keys_to_content`: 应存储在返回消息的 content 字段中的键，会暴露给其它智能体
# - `keys_to_metadata`: 应存储在返回消息的元数据（metadata）字段中的键
#
# .. note:: 如果提供了一个字符串，解析器将从解析后的字典中提取给定键的值。如果提供了一个字符串列表，将创建一个包含给定键的子字典。
#
# 下面是使用 `MarkdownJsonDictParser` 自动后处理解析后字典的示例。
#

parser = MarkdownJsonDictParser(
    content_hint='{"thought": "你的想法", "speak": "你对用户说的话", "use_ability": "是否使用能力"}',
    keys_to_memory=["thought", "speak"],
    keys_to_content="speak",
    keys_to_metadata="use_ability",
)

dummy_response = ModelResponse(
    text="""```json
{
    "thought": "我应该...",
    "speak": "我不会使用我的能力",
    "use_ability": false
}```
""",
)

parsed_response = parser.parse(dummy_response)

print("解析后的响应: ", parsed_response.parsed)
print("存储到记忆", parser.to_memory(parsed_response.parsed))
print("存储到消息 content 字段: ", parser.to_content(parsed_response.parsed))
print("存储到消息 metadata 字段: ", parser.to_metadata(parsed_response.parsed))

# %%
# 这里我们展示如何创建一个智能体，它在 `reply` 方法中通过以下步骤实现自动化的后处理。
#
# 1. 在提示中放入格式说明，以指导 LLM 生成所需的输出
# 2. 解析 LLM 的返回值
# 3. 使用 `to_memory`、`to_content` 和 `to_metadata` 方法后处理解析后的字典
#
# .. tip:: 通过更改不同的解析器，智能体可以适应不同的场景，并以各种格式生成结构化输出。
#

from agentscope.models import DashScopeChatWrapper
from agentscope.agents import AgentBase
from agentscope.message import Msg


class Agent(AgentBase):
    def __init__(self):
        self.name = "Alice"
        super().__init__(name=self.name)

        self.sys_prompt = f"你是一个名为{self.name}的有用助手。"

        self.model = DashScopeChatWrapper(
            config_name="_",
            model_name="qwen-max",
        )

        self.parser = MarkdownJsonDictParser(
            content_hint='{"thought": "你的想法", "speak": "你对用户说的话", "use_ability": "是否使用能力"}',
            keys_to_memory=["thought", "speak"],
            keys_to_content="speak",
            keys_to_metadata="use_ability",
        )

        self.memory.add(Msg("system", self.sys_prompt, "system"))

    def reply(self, msg):
        self.memory.add(msg)

        prompt = self.model.format(
            self.memory.get_memory(),
            # 指示模型按要求的格式作答
            Msg("system", self.parser.format_instruction, "system"),
        )

        response = self.model(prompt)

        parsed_response = self.parser.parse(response)

        self.memory.add(
            Msg(
                name=self.name,
                content=self.parser.to_memory(parsed_response.parsed),
                role="assistant",
            ),
        )

        return Msg(
            name=self.name,
            content=self.parser.to_content(parsed_response.parsed),
            role="assistant",
            metadata=self.parser.to_metadata(parsed_response.parsed),
        )
