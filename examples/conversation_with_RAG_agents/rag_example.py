# -*- coding: utf-8 -*-
"""
An example for conversation between user and agents with RAG capability.
One agent is a tutorial assistant, the other is a code explainer.
"""
import json
import os

from groupchat_utils import filter_agents

import agentscope
from agentscope.agents import UserAgent, DialogAgent, LlamaIndexAgent


AGENT_CHOICE_PROMPT = """
There are following available agents. You need to choose the most appropriate
agent(s) to answer the user's question.

agent descriptions:{}

First, rephrase the user's question, which must contain the key information.
The you need to think step by step. If you believe some of the agents are
good candidates to answer the question (e.g., AGENT_1 and AGENT_2), then
you need to follow the following format to generate your output:

'
Because $YOUR_REASONING.
I believe @AGENT_1 and @AGENT_2 are the most appropriate agents to answer
your question.
'
"""


def prepare_docstring_html(repo_path: str, html_dir: str) -> None:
    """prepare docstring in html for API assistant"""
    os.system(
        f"sphinx-apidoc -f -o {repo_path}/docs/sphinx_doc/en/source "
        f"{repo_path}/src/agentscope -t template",
    )
    os.system(
        f"sphinx-build -b html  {repo_path}/docs/sphinx_doc/en/source "
        f"{html_dir} -W --keep-going",
    )


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

    # prepare html for api agent
    prepare_docstring_html(
        agent_configs[2]["args"]["rag_config"]["repo_base"],
        agent_configs[2]["args"]["rag_config"]["file_dir"],
    )
    # define an API agent
    api_agent = LlamaIndexAgent(**agent_configs[2]["args"])

    searching_agent = LlamaIndexAgent(**agent_configs[4]["args"])

    rag_agents = [
        tutorial_agent,
        code_explain_agent,
        api_agent,
        searching_agent,
    ]
    rag_agent_names = [agent.name for agent in rag_agents]

    # define a guide agent
    rag_agent_descriptions = [
        "agent name: "
        + agent.name
        + "\n agent description："
        + agent.description
        + "\n"
        for agent in rag_agents
    ]
    agent_configs[3]["args"].pop("description")
    agent_configs[3]["args"]["sys_prompt"] = agent_configs[3]["args"][
        "sys_prompt"
    ] + AGENT_CHOICE_PROMPT.format(
        "".join(rag_agent_descriptions),
    )

    guide_agent = DialogAgent(**agent_configs[3]["args"])

    user_agent = UserAgent()
    while True:
        # The workflow is the following:
        # 1. user input a message,
        # 2. if it mentions one of the agents, then the agent will be called
        # 3. otherwise, the guide agent will decide which agent to call
        # 4. the called agent will respond to the user
        # 5. repeat
        x = user_agent()
        x.role = "user"  # to enforce dashscope requirement on roles
        if len(x["content"]) == 0 or str(x["content"]).startswith("exit"):
            break
        speak_list = filter_agents(x.get("content", ""), rag_agents)
        if len(speak_list) == 0:
            guide_response = guide_agent(x)
            # Only one agent can be called in the current version,
            # we may support multi-agent conversation later
            speak_list = filter_agents(
                guide_response.get("content", ""),
                rag_agents,
            )
        agent_name_list = [agent.name for agent in speak_list]
        for agent_name, agent in zip(agent_name_list, speak_list):
            if agent_name in rag_agent_names:
                agent(x)


if __name__ == "__main__":
    main()
