# -*- coding: utf-8 -*-
"""Main script for running the streaming agent."""
from typing import Optional, Union, Sequence

import agentscope
from agentscope.agents import AgentBase, UserAgent
from agentscope.message import Msg

agentscope.init(
    model_configs=[
        {
            "config_name": "stream_ds",
            "model_type": "dashscope_chat",
            "model_name": "qwen-max",
            "api_key": "",
            "stream": True,
        },
        {
            "config_name": "stream_ollama",
            "model_type": "ollama_chat",
            "model_name": "llama2",
            "stream": True,
        },
    ],
)


class StreamingAgent(AgentBase):
    """An agent that speaks streaming messages."""

    def __init__(
        self,
        name: str,
        sys_prompt: str,
        model_config_name: str,
    ) -> None:
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
        )

        self.memory.add(Msg(self.name, self.sys_prompt, "system"))

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        self.memory.add(x)

        prompt = self.model.format(self.memory.get_memory())

        print(prompt)

        res = self.model(prompt)

        for chunk in res.stream:
            self.speak(Msg(self.name, chunk, "assistant"))

        msg_returned = Msg(self.name, res.text, "assistant")

        self.memory.add(msg_returned)

        return msg_returned


agent = StreamingAgent(
    "assistant",
    "You're a helpful assistant",
    "stream_ollama",
)
user = UserAgent("user")

msg = None
while True:
    msg = agent(msg)
    msg = user(msg)
    if msg.content == "exit":
        break
