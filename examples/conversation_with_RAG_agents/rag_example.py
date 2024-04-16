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
    tutorial_agent = LlamaIndexAgent(**agent_configs[0]["args"])
    code_explain_agent = LlamaIndexAgent(**agent_configs[1]["args"])
    summarize_agent = DialogAgent(**agent_configs[2]["args"])
    rag_agents = [
        tutorial_agent,
        code_explain_agent,
    ]
    rag_agent_names = [agent.name for agent in rag_agents]
    summarize_agents = [summarize_agent]
    summarize_agent_names = [agent.name for agent in summarize_agents]
    helper_agents = rag_agents + summarize_agents

    user_agent = UserAgent()
    # start the conversation between user and assistant
    while True:
        x = user_agent()
        x.role = "user"  # to enforce dashscope requirement on roles
        if len(x["content"]) == 0 or str(x["content"]).startswith("exit"):
            break
        speak_list = filter_agents(x.get("content", ""), helper_agents)
        if len(speak_list) == 0:
            # if no agent is @ (mentioned), default invoke all rag agents and
            # summarize agents
            speak_list = rag_agents + summarize_agents
        for agent in speak_list:
            if agent.name in summarize_agent_names:
                # if summarize agent is mentioned, then also call rag agents
                # TODO: let summarize agent choose which agent to call
                speak_list = rag_agents + summarize_agents

        agent_name_list = [agent.name for agent in speak_list]
        rag_agent_responses = []
        for agent_name, agent in zip(agent_name_list, speak_list):
            if agent_name in rag_agent_names:
                rag_agent_responses.append(agent(x))

        msg = Msg(
            name="user",
            role="user",
            content="/n".join([msg.content for msg in rag_agent_responses]),
        )
        for agent_name, agent in zip(agent_name_list, speak_list):
            if agent_name in summarize_agent_names:
                agent(msg)


if __name__ == "__main__":
    main()
