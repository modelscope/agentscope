# -*- coding: utf-8 -*-
"""
.. _prompt-engineering:

Prompt Engineering
================================

The prompt engineering is a crucial part of LLM-empowered applications,
especially for the multi-agent ones.
However, most API providers focus on the chatting scenario, where a user and
an assistant speak alternately.

To support multi-agent applications, AgentScope builds different prompt
strategies to convert a list of `Msg` objects to the required format.

.. note:: There is no **one-size-fits-all** solution for prompt crafting.
 The goal of built-in strategies is to **enable beginners to smoothly invoke
 the model API, rather than achieve the best performance**.
 For advanced users, we highly recommend developers to customize prompts
 according to their needs and model API requirements.

Using Built-in Strategy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The built-in prompt strategies are implemented in the `format` method of the
model objects. Taking DashScope Chat API as an example:

"""

from agentscope.models import DashScopeChatWrapper
from agentscope.message import Msg
import json


model = DashScopeChatWrapper(
    config_name="_",
    model_name="qwen-max",
)

# `Msg` objects or a list of `Msg` objects can be passed to the `format` method
prompt = model.format(
    Msg("system", "You're a helpful assistant.", "system"),
    [
        Msg("assistant", "Hi!", "assistant"),
        Msg("user", "Nice to meet you!", "user"),
    ],
)

print(json.dumps(prompt, indent=4, ensure_ascii=False))

# %%
# After formatting the input messages, we can input the prompt into the model
# object.

response = model(prompt)

print(response.text)

# %%
# Non-Vision Models
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# In the following table, we list the built-in prompt strategies, as well as
# the prefix of supported LLMs.
#
# Taking the following messages as an example:
#
# .. code-block:: python
#
#     Msg("system", "You're a helpful assistant named Alice.", "system"),
#     Msg("Alice", "Hi!", "assistant"),
#     Msg("Bob", "Nice to meet you!", "user")
#
#
# .. list-table::
#     :header-rows: 1
#
#     * - LLMs
#       - `model_name`
#       - Constructed Prompt
#     * - OpenAI LLMs
#       - `gpt-`
#       - .. code-block:: python
#
#             [
#                 {
#                     "role": "system",
#                     "name": "system",
#                     "content": "You're a helpful assistant named Alice."
#                 },
#                 {
#                     "role": "user",
#                     "name": "Alice",
#                     "content": "Hi!"
#                 },
#                 {
#                     "role": "user",
#                     "name": "Bob",
#                     "content": "Nice to meet you!"
#                 }
#             ]
#     * - Gemini LLMs
#       - `gemini-`
#       - .. code-block:: python
#
#             [
#                 {
#                     "role": "user",
#                     "parts": [
#                         "You're a helpful assistant named Alice.\\n## Conversation History\\nAlice: Hi!\\nBob: Nice to meet you!"
#                     ]
#                 }
#             ]
#     * - All other LLMs
#
#         (e.g. DashScope, ZhipuAI ...)
#       -
#       - .. code-block:: python
#
#             [
#                 {
#                     "role": "system",
#                     "content": "You're a helpful assistant named Alice."
#                 },
#                 {
#                     "role": "user",
#                     "content": "## Conversation History\\nAlice: Hi!\\nBob: Nice to meet you!"
#                 }
#             ]
#
# .. tip:: Considering some API libraries can support different LLMs (such as OpenAI Python library), AgentScope uses the `model_name` field to distinguish different models and decides the used strategy.
#
# Vision Models
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# For vision models, AgentScope currently supports OpenAI vision models and
# Dashscope multi modal API.
# The more supported APIs will be added in the future.
