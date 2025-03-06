# -*- coding: utf-8 -*-
"""
.. _message:

消息
====================

消息是一种专用的数据结构，用于信息交换。
在 AgentScope 中，我们使用消息在智能体之间进行通信。

消息的最重要字段是：name、role 和 content。
name 和 role 字段标识消息的发送者，content 字段包含实际信息。

.. Note:: role 字段必须选择 `"system"`、`"assistant"`、 `"user"` 其中之一。
"""

from agentscope.message import Msg
import json

# %%
# 创建消息
# ----------------
# 可以通过指定 name、role 和 content 字段来创建消息。
#

msg = Msg(
    name="Jarvis",
    role="assistant",
    content="嗨！我能为您效劳吗？",
)

print(f'消息发送者："{msg.name}"')
print(f'发送者角色："{msg.role}"')
print(f'消息内容："{msg.content}"')

# %%
# 序列化
# ----------------
# 消息可以序列化为 JSON 格式的字符串。
#

serialized_msg = msg.to_dict()

print(type(serialized_msg))
print(json.dumps(serialized_msg, indent=4))

# %%
# 反序列化
# ----------------
# 从 JSON 格式的字典反序列化消息。
#

new_msg = Msg.from_dict(serialized_msg)

print(new_msg)
print(f'消息发送者："{new_msg.name}"')
print(f'发送者角色："{new_msg.role}"')
print(f'消息内容："{new_msg.content}"')
