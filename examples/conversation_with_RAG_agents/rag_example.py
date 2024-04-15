# -*- coding: utf-8 -*-
"""
A simple example for conversation between user and
an agent with RAG capability.
"""
import json
import os

from rag_agents import LlamaIndexAgent

import agentscope
from agentscope.agents import UserAgent

# from agentscope.message import Msg
# from agentscope.agents import DialogAgent


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
    # TODO: testing version only with tutorial agent
    # code_explain_agent = LlamaIndexAgent(**agent_configs[1]["args"])
    # summarize_agent = DialogAgent(**agent_configs[2]["args"])

    user_agent = UserAgent()
    # start the conversation between user and assistant
    while True:
        x = user_agent()
        x.role = "user"  # to enforce dashscope requirement on roles
        if len(x["content"]) == 0 or str(x["content"]).startswith("exit"):
            break
        tutorial_agent(x)
        # tutorial_response = tutorial_agent(x)
        # code_explain = code_explain_agent(x)
        # msg = Msg(
        #     name="user",
        #     role="user",
        #     content=tutorial_response["content"]
        #     + "\n"
        #     + code_explain["content"]
        #     + "\n"
        #     + x["content"],
        # )
        # summarize_agent(msg)


if __name__ == "__main__":
    main()
