# -*- coding: utf-8 -*-
"""
.. _message:

Message
====================

Message is a specialized data structure for information exchange.
In AgentScope, we use message to communicate among agents.

The most important fields of a message are: `name`, `role`, and `content`.
The `name and `role` fields identify the sender of the message, and the
`content` field contains the actual information.

.. Note:: The `role` field must be chosen from `"system"`, `"assistant"` and `"user"`.
"""

from agentscope.message import Msg
import json

# %%
# Create a Message
# ----------------
# Message can be created by specifying the `name`, `role`, and `content` fields.


msg = Msg(
    name="Jarvis",
    role="assistant",
    content="Hi! How can I help you?",
)

print(f'The sender of the message: "{msg.name}"')
print(f'The role of the sender: "{msg.role}"')
print(f'The content of the message: "{msg.content}"')

# %%
# Serialize
# ----------------
# Message can be serialized to a string in JSON format.

serialized_msg = msg.to_dict()

print(type(serialized_msg))
print(json.dumps(serialized_msg, indent=4))

# %%
# Deserialize
# ----------------
# Deserialize a message from a string in JSON format.

new_msg = Msg.from_dict(serialized_msg)

print(new_msg)
print(f'The sender of the message: "{new_msg.name}"')
print(f'The role of the sender: "{new_msg.role}"')
print(f'The content of the message: "{new_msg.content}"')
