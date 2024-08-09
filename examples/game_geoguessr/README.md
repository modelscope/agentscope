# GeoGuessr-like Game with AgentScope

This example will show
- How to build a GeoGuessr-like game with AgentScope.
- How to use AgentScope Studio to visualize conversations between the agents.
- How to use the TripAdvisor API as tool functions in AgentScope.
- How to build a neurosymbolic agent and a generative agent in AgentScope.


## Background

This example demonstrates two different implementations of a GeoGuessr-like game using the AgentScope framework.

**Neurosymbolic Version:** This version features a gamemaster agent that selects locations and provides hints, and a player agent that tries to guess the locations based on images and clues. The gamemaster agent utilizes a rule-based-LLM hybrid approach to manage the game state and interact with the TripAdvisor API. `ExtendedDialogAgent.py` implements the agent with all the logics needed.

**Generative Version:** This version leverages the capabilities of a large language model (LLM) to handle the game logic and interaction with the player. The gamemaster agent, powered by an LLM, dynamically selects locations, retrieves images, and provides hints based on the player's guesses.

Both versions showcase the flexibility and power of AgentScope in building interactive and engaging AI applications.

## Tested Models

These models are tested in this example in the exact same way they are used in the examples. For other models, some modifications may be needed.
- gpt-4o
- qwen-vl-max


## Prerequisites

- **AgentScope:** Install the latest AgentScope library.
- **TripAdvisor API Key:** Obtain an API key from TripAdvisor and replace the placeholders in the code with your actual key.
- **OpenAI API Key (Optional):** If you want to use OpenAI models, obtain an API key from OpenAI and configure it accordingly.
- **Dashscope API Key (Optional):** If you want to use Dashscope models, obtain an API key from Dashscope and configure it accordingly.
- **Required Python Packages:**
```
requests
```
- **Access to the internet:** Required to interact with the TripAdvisor API and download images.

## Running the Example
Both examples have been set to run with AgentScope Studio by default. After starting running the script, open `http://127.0.0.1:5000` with your browser (Chorme is preferred).
For more information on AgentScope Studio see `http://doc.agentscope.io/en/tutorial/209-gui.html`