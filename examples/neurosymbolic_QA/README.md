

# Neurosymbolic Question Answering with AgentScope

This example will show:
- How to set up and use the ReActAgent from AgentScope for neurosymbolic reasoning.
- How to integrate various Wolfram Alpha query functions into a neurosymbolic question-answering system, particularly for question involves mathetical reasoning.

## Background
LLMs are good at many tasks, but fall short in rigorous reasoning, like doing complex mathematical calcuations.
This script demonstrates a neurosymbolic question-answering system using AgentScope, which integrates various external APIs like Wolfram Alpha to assist LLM agents in solving problems that involve mathetical reasoning. The LLM agent first formulates the mathematical problems that need to be solved based on its interpretation of the problem statement, then it uses Wolfram Alpha to solve the mathematical problems, synthesizes the solution and finally returns a reply. 

Two LLM agents are set up in this demonstration: one with access to Wolfram Alpha APIs for solving mathematical problems, and another without such access, as a comparison, aiming to solve a game theory problem on finding mixed Nash equilibria.



## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- `claude-3-5-sonnet-20240620` - Note that this example currently is only compatible with claude-3-5-sonnet-20240620 API, since other models could not even formulate the right equations for wolfram almpha API to solve.
Furthermore, changing the temperature might affect the output since sometimes with a different temperature, the model could not properly adapt to the ReAct framework.


## Prerequisites

To run this example successfully, ensure you meet the following requirements:
- The latest AgentScope library installed (`pip install agentscope`).
- Valid API keys for Wolfram Alpha and Anthropic API, which should be replaced in the placeholders within the script.
- Network access to connect to the specified API services and AgentScope Studio at `http://127.0.0.1:5000`.
- [Optional] Knowledge in game theory and understanding of Nash equilibria for interpreting the agent's reasoning trace.