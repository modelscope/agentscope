# -*- coding: utf-8 -*-
"""
A simple example for conversation between user and
an agent with RAG capability.
"""
import json
import os

from rag_agents import LlamaIndexAgent
from groupchat_utils import filter_agents

import agentscope
from agentscope.agents import UserAgent

from agentscope.message import Msg
from agentscope.agents import DialogAgent


def main() -> None:
    """A RAG multi-agent demo"""
    with open("configs/model_config.json", "r", encoding="utf-8") as f:
        model_configs = json.load(f)
    # for internal API
    for config in model_configs:
        if config.get("model_type", "") == "post_api_chat":
            # for gpt4 API
            config["headers"]["Authorization"] = (
                "Bearer " + f"{os.environ.get('HTTP_LLM_API_KEY')}"
            )
        else:
            # for dashscope
            config["api_key"] = f"{os.environ.get('DASHSCOPE_API_KEY')}"
    agentscope.init(model_configs=model_configs)

    with open("configs/agent_config.json", "r", encoding="utf-8") as f:
        agent_configs = json.load(f)
    # define RAG-based agents for tutorial and code
    tutorial_agent = LlamaIndexAgent(**agent_configs[0]["args"])
    code_explain_agent = LlamaIndexAgent(**agent_configs[1]["args"])
    agent_configs[2]["args"].pop("description")
    # define a guide agent
    guide_agent = LlamaIndexAgent(**agent_configs[3]["args"])
    rag_agents = [
        tutorial_agent,
        code_explain_agent,
        guide_agent, # this is the new one
    ]
    rag_agent_names = [agent.name for agent in rag_agents]
    helper_agents = rag_agents

    user_agent = UserAgent()
    while True:
        x = user_agent()
        x.role = "user"  # to enforce dashscope requirement on roles
        if len(x["content"]) == 0 or str(x["content"]).startswith("exit"):
            break
        speak_list = filter_agents(x.get("content", ""), rag_agents)
        if len(speak_list) == 0:
            guide_response = guide_agent(x)
            speak_list = filter_agents(guide_response.get("content", ""),
                                       helper_agents)

        agent_name_list = [agent.name for agent in speak_list]
        for agent_name, agent in zip(agent_name_list, speak_list):
            if agent_name in rag_agent_names:
                agent(x)

if __name__ == "__main__":
    main()
