# -*- coding: utf-8 -*-
"""
This module implements a neurosymbolic question-answering system
using AgentScope.

It sets up two student agents: one with access to Wolfram Alpha APIs
for solving mathematical problems, and another without such access.
The agents are tasked with solving game theory problems,
specifically finding mixed Nash equilibria.

The module demonstrates the use of ReActAgent, ServiceToolkit, and various
Wolfram Alpha query functions from AgentScope.
"""
from agentscope.service import ServiceToolkit
from agentscope.message import Msg
import agentscope
from agentscope.agents import DialogAgent
from agentscope.service import (
    query_wolfram_alpha_short_answers,
    query_wolfram_alpha_simple,
    query_wolfram_alpha_show_steps,
    query_wolfram_alpha_llm,
)
from agentscope.agents import ReActAgent


agentscope.init(
    # ...
    project="xxx",
    name="xxx",
    studio_url="http://127.0.0.1:5000",  # The URL of AgentScope Studio
)


YOUR_MODEL_CONFIGURATION = [
    {
        "model_type": "openai_chat",
        "config_name": "gpt",
        "model_name": "gpt-4o-mini",
        "api_key": "",
        "generate_args": {
            "temperature": 0.1,
        },
    },
]


# Initialize the ServiceToolkit and register the TripAdvisor API functions
service_toolkit = ServiceToolkit()
service_toolkit.add(
    query_wolfram_alpha_short_answers,
    api_key="",
)  # Replace with your actual TripAdvisor API key
service_toolkit.add(
    query_wolfram_alpha_simple,
    api_key="",
)  # Replace with your actual TripAdvisor API key
service_toolkit.add(
    query_wolfram_alpha_show_steps,
    api_key="",
)  # Replace with your actual TripAdvisor API key
service_toolkit.add(
    query_wolfram_alpha_llm,
    api_key="",
)  # Replace with your actual TripAdvisor API key

agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION)

student_agent1 = DialogAgent(
    name="Student1",
    sys_prompt="""You are a smart student. You are given problem to solve.""",
    model_config_name="gpt",  # replace by your model config name
)

student_agent2 = ReActAgent(
    name="Student2",
    sys_prompt="""You are a smart student. You are given problem to solve.
    Use the approprite wolfram alpha APIs to help you solve simultaneous
    equations/calculations. Note that wolfram alpha apis can only help you
    solve an explicitly given equation or calculation. Don't use them
    if you are not solving equations or doing calculations.""",
    model_config_name="gpt",
    service_toolkit=service_toolkit,
    verbose=True,  # set verbose to True to show the reasoning trace
)


x1 = Msg(
    "system",
    """Solve the problem: For the following games,
    compute all mixed Nash equilibria. In each table cell,
    the number on the left is the payoff to the row player, and
    the number on the right is the payoff to the column player.
        |   | L   | R   |
        |---|-----|-----|
        | T | 7,1 | 2,2 |
        | B | 0,5 | 3,1 |""",
    role="user",
)

student_agent1.speak(x1)
x1 = student_agent1(x1)


x2 = Msg(
    "system",
    """Solve the problem: For the following games,
    compute all mixed Nash equilibria. In each table cell,
    the number on the left is the payoff to the row player, and
    the number on the right is the payoff to the column player.
        |   | L   | R   |
        |---|-----|-----|
        | T | 7,1 | 2,2 |
        | B | 0,5 | 3,1 |
    You need to formulate the relevant equations
    and ask it to solve it for you.""",
    role="user",
)

student_agent2.speak(x2)
x2 = student_agent2(x2)
