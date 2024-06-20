###
# Multi-Agent Group Conversation in AgentScope

This example demonstrates a multi-agent group conversation facilitated by AgentScope. The script sets up a virtual chat room where a user agent interacts with several NPC (non-player character) agents. Participants can utilize a special "@" mention functionality to address specific agents directly.

## Background

The conversation takes place in a simulated chat room environment with predefined roles for each participant. Topics are open-ended and evolve based on the user's input and agents' responses.

## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- gemini_chat (models/gemini-pro, models/gemini-1.0-pro)
- dashscope_chat (qwen-max, qwen-turbo)
- ollama_chat (ollama_llama3_8b)

## Prerequisites

Fill the next cell to meet the following requirements:
- Set your `api_key` in the `configs/model_configs.json` file
- Optional: Launch agentscope gradio with `as_gradio main.py`

## How to Use

1. Run the script using the command: `python main.py`
2. Address specific agents by typing "@" followed by the agent's name.
3. Type "exit" to leave the chat.

## Customization Options

You can adjust the behavior and parameters of the NPC agents and conversation model by editing the `agent_configs.json` and `model_configs.json` files, respectively.

### Changing User Input Time Limit

Adjust the `USER_TIME_TO_SPEAK` variable in the `main.py` script to change the time limit for user input.
###
