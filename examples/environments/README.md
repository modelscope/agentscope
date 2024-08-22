# Environments Example

This example will show
- How to set up a chat room and generate a conversation between three agents.
- How to set up a chat room with auto reply assistant.


## Background

The `envs/chatroom.py` provides a framework for creating a chatroom environment where multiple agents (represented by the `ChatRoomAgent` and `ChatRoomAgentWithAssistant` classes) can communicate and interact in real-time. This implementation simulates a collaborative workspace where agents can role-play as members of a team, collaborating on tasks and exchanging messages.

The core functionality is encapsulated within the `ChatRoom` class, which manages the participants, handles message history, and maintains the overall chat state. Each participant is an instance of `ChatRoomAgent`, which can generate responses based on given prompts and previous messages, thereby simulating intelligent conversation.

The system also supports event-driven features, such as listening for specific messages and responding to mentions of agents within the chat. This allows for a dynamic interaction where agents can refer to each other using the "@" symbol, prompting responses based on context.

Moreover, the framework allows for interaction with an external assistant through the `ChatRoomAgentWithAssistant`, which can assist in generating responses for agents who may be preoccupied or unavailable.

This implementation can be useful for various applications, including simulation of team meetings, brainstorming sessions, etc. The examples provided (`chatroom_example.py` and `chatroom_with_assistant_example.py`) demonstrate how to set up a chatroom with different agent configurations and facilitate dialogue exchanges based on predefined conditions and prompts.


## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- `dashscope_chat` with `qwen-turbo`
- gpt-4o


## Prerequisites

- Install the lastest version of AgentScope by

```bash
git clone https://github.com/modelscope/agentscope
cd agentscope
pip install -e .
```

- Prepare an OpenAI API key or Dashscope API key

## Running the Example

First fill your OpenAI API key or Dashscope API key in `chatroom_example.py` and `chatroom_with_assistant_example.py`, then execute the following command to run the chatroom.

```bash
python chatroom_example.py
```

```bash
python chatroom_with_assistant_example.py
```
