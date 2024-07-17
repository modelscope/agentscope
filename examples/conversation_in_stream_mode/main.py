# -*- coding: utf-8 -*-
"""Main script for running the streaming agent."""
from typing import Optional, Union, Sequence

import os

import agentscope
from agentscope.agents import AgentBase, UserAgent
from agentscope.message import Msg
from agentscope.utils import MonitorFactory


stream = True
model_name = "glm-4"

os.environ["OPENAI_API_KEY"] = ""

agentscope.init(
    model_configs=[
        {
            "config_name": "stream_ds",
            "model_type": "dashscope_chat",
            "model_name": "qwen-max",
            "api_key": "",
            "stream": stream,
        },
        {
            "config_name": "stream_ollama",
            "model_type": "ollama_chat",
            "model_name": "llama2",
            "stream": stream,
        },
        {
            "config_name": "stream_litellm",
            "model_type": "litellm_chat",
            "model_name": "gpt-4",
            "stream": stream,
        },
        {
            "model_type": "zhipuai_chat",
            "config_name": "glm-4",
            "model_name": "glm-4",
            "stream": stream,
            "api_key": "",
            # Load from env if not provided
            "generate_args": {
                "temperature": 0.5,
            },
        },
    ],
    save_api_invoke=True,
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

        self.speak(Msg(self.name, res.text, "assistant"))

        msg_returned = Msg(self.name, res.text, "assistant")

        self.memory.add(msg_returned)

        return msg_returned


agent = StreamingAgent(
    "assistant",
    "You're a helpful assistant",
    "glm-4",
)
user = UserAgent("user")

msg = None
while True:
    msg = user(msg)
    if msg.content == "exit":
        break
    msg = agent(msg)

print(MonitorFactory.get_monitor().get_value(f"{model_name}.prompt_tokens"))
print(
    MonitorFactory.get_monitor().get_value(f"{model_name}.completion_tokens"),
)
print(MonitorFactory.get_monitor().get_value(f"{model_name}.total_tokens"))
print(MonitorFactory.get_monitor().get_value(f"{model_name}.call_counter"))
