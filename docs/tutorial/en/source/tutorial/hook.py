# -*- coding: utf-8 -*-
"""
.. _hook:
Hooks
===========================

Hooks are extension points in AgentScope that allow developers to customize agent behaviors at specific execution points. They provide a flexible way to modify or extend the agent's functionality without changing its core implementation.

Core Functions
-------------
AgentScope implements hooks around three core agent functions:

- `reply`: Generates response messages based on the agent's current state
- `speak`: Displays and records messages to the terminal
- `observe`: Records incoming messages

Available Hooks
-------------
Each core function has corresponding pre- and post-execution hooks:

- `pre_reply_hook` / `post_reply_hook`
- `pre_speak_hook` / `post_speak_hook`
- `pre_observe_hook` / `post_observe_hook`

For example, you can use `pre_speak_hook` to redirect messages to different outputs like web interfaces or external applications.

When working with hooks, keep these important rules in mind:

1. **Hook Function Signature**
 - First argument must be the `AgentBase` object
 - Subsequent arguments are copies of the original function arguments

2. **Execution Order**
 - Hooks are executed in registration order
 - Multiple hooks can be chained together

3. **Return Value Handling**
 - For pre-hooks: Non-None return values are passed to the next hook or target function
  - When a hook returns None, the next hook will use the most recent non-None return value from previous hooks
  - If all previous hooks return None, the next hook receives a copy of the original arguments
  - The final non-None return value (or original arguments if all hooks return None) is passed to the target function
 - For post-hooks: Only the `post-reply` hook has a return value, which works the same way as pre-hooks.

4. **Important**: Never call the target function (reply/speak/observe) within a hook to avoid infinite loops

Hooks Template
-----------------------

We provide templates for each hook function below to show their argument
signatures. You can copy and paste these templates into your code and
customize them as needed.
"""

from typing import Union, Optional

from agentscope.agents import AgentBase
from agentscope.message import Msg


def pre_reply_hook_template(
    self: AgentBase,
    x: Optional[Union[Msg, list[Msg]]] = None,
) -> Union[None, Msg, list[Msg]]:
    """Pre-reply hook template."""
    pass


def post_reply_hook_template(self: AgentBase, x: Msg) -> Msg:
    """Post-reply hook template."""
    pass


def pre_speak_hook_template(
    self: AgentBase,
    x: Msg,
    stream: bool,
    last: bool,
) -> Union[Msg, None]:
    """Pre-speak hook template."""
    pass


def post_speak_hook_template(self: AgentBase) -> None:
    """Post-speak hook template."""
    pass


def pre_observe_hook_template(
    self: AgentBase,
    x: Union[Msg, list[Msg]],
) -> Union[Msg, list[Msg]]:
    """Pre-observe hook template."""
    pass


def post_observe_hook_template(self: AgentBase) -> None:
    """Post-observe hook template."""
    pass


# %%
# Example Usage
# -------------------
# AgentScope allows to register, remove and clear hooks by calling the
# corresponding methods.
#
# We first create a simple agent that echoes the incoming message:

from typing import Optional, Union

from agentscope.agents import AgentBase
from agentscope.message import Msg


class TestAgent(AgentBase):
    def __init__(self):
        super().__init__(name="TestAgent")

    def reply(self, x: Optional[Union[Msg, list[Msg]]] = None) -> Msg:
        self.speak(x)
        return x


# %%
# Reply Hooks
# ^^^^^^^^^^^^^^^^^^^^^^^
# Next, we define two pre-hooks, which both modify the input message(s), but
# one return the modified message(s) and the other does not:


def pre_reply_hook_1(
    self,
    x=None,
) -> Union[None, Msg, list[Msg]]:
    """The first pre-reply hook that changes the message content."""
    if isinstance(x, Msg):
        x.content = "[Pre-hook-1] " + x.content
    elif isinstance(x, list):
        for msg in x:
            msg.content = "[Pre-hook-1] " + msg.content


def pre_reply_hook_2(
    self,
    x=None,
) -> Union[None, Msg, list[Msg]]:
    """The second pre-reply hook that changes the message content."""
    if isinstance(x, Msg):
        x.content = "[Pre-hook-2] " + x.content
    elif isinstance(x, list):
        for msg in x:
            msg.content = "[Pre-hook-2] " + msg.content
    return x


# %%
# Then we create a post-hook that appends a suffix to the message content:


def post_reply_hook(self, x) -> Msg:
    """The post-reply hook that appends a suffix to the message content."""
    x.content += " [Post-hook]"
    return x


# %%
# Finally, we register the hooks and test the agent:

agent = TestAgent()

agent.register_pre_reply_hook("pre_hook_1", pre_reply_hook_1)
agent.register_pre_reply_hook("pre_hook_2", pre_reply_hook_2)
agent.register_post_reply_hook("post_hook", post_reply_hook)

msg = Msg("user", "[Original message]", "user")

msg_response = agent(msg)

print("The content of the response message:\n", msg_response.content)

# %%
# We can see that the response has one "[Pre-hook-2]" prefix and one
# "[Post-hook]" suffix. The "[Pre-hook-1]" prefix is missing because the
# first pre-hook does not return the modified message(s).
#
# Speak Hooks
# ^^^^^^^^^^^^^^^^^^^^^^^
# To be compatible with the streaming output, the pre-speak hook takes two
# additional arguments:
#
# - `stream`: a boolean flag indicating the streaming status
# - `last`: a boolean flag indicating if the input message is the last one in the stream
#
# .. tip:: When dealing with the streaming output, you can use the msg id to determine
#  whether two messages are from the same streaming output or not.
#
# We show how to use the pre/post-speak hooks below:

from agentscope.agents import DialogAgent
import agentscope

agentscope.init(
    model_configs=[
        {
            "config_name": "streaming_config",
            "model_type": "dashscope_chat",
            "model_name": "qwen-max",
            "stream": True,
        },
    ],
)

streaming_agent = DialogAgent(
    name="TestAgent",
    model_config_name="streaming_config",
    sys_prompt="You're a helpful assistant.",
)


# Create a pre-speak hook that displays the message content
def pre_speak_hook(self, x: Msg, stream: bool, last: bool) -> None:
    """The pre-speak hook that display the message content."""
    # You can change or redirect the message here
    print(
        "id: ",
        x.id,
        "content: ",
        x.content,
        "stream: ",
        stream,
        "last: ",
        last,
    )


def post_speak_hook(self) -> None:
    """The post-speak hook that display the message content."""
    # We count the number of calling the speak function here.
    if not hasattr(self, "cnt"):
        self.cnt = 0
    self.cnt += 1


# Register the hooks
streaming_agent.register_pre_speak_hook("pre_speak_hook", pre_speak_hook)
streaming_agent.register_post_speak_hook("post_speak_hook", post_speak_hook)

msg = Msg(
    "user",
    "Now, count from 1 to 15, step by 1 and separate each number by a comma.",
    "user",
)

msg_response = streaming_agent(msg)

print("The cnt of calling the speak function:", streaming_agent.cnt)


# %%
# Observe Hooks
# ^^^^^^^^^^^^^^^^^^^^^^^
# Similar as the speak hooks, we show how to use the pre/post-observe hooks
# below:

import json


def pre_observe_hook(self, x: Union[Msg, list[Msg]]) -> Union[Msg, list[Msg]]:
    """The pre-observe hook that display the message content."""
    if isinstance(x, Msg):
        x.content = "Observe: " + x.content
    elif isinstance(x, list):
        for msg in x:
            msg.content = "Observe: " + msg.content
    return x


def post_observe_hook(self) -> None:
    """The post-observe hook that display the message content."""
    if not hasattr(post_observe_hook, "cnt"):
        setattr(post_observe_hook, "cnt", 0)
    post_observe_hook.cnt += 1


# Clear the memory first
agent.memory.clear()

agent.register_pre_observe_hook("pre_observe_hook", pre_observe_hook)
agent.register_post_observe_hook("post_observe_hook", post_observe_hook)

agent.observe(
    Msg(
        "user",
        "The sun is shining.",
        "user",
    ),
)

print(
    "The content of the memory:\n",
    json.dumps([_.to_dict() for _ in agent.memory.get_memory()], indent=4),
)
print("The cnt of calling the observe function:", post_observe_hook.cnt)
