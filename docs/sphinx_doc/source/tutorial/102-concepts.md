(102-concepts)=

# Fundamental Concepts

In this tutorial, you'll have an initial understanding of the **fundamental concepts** of AgentScope. We will focus on how a multi-agent application runs based on our platform and familiarize you with the essential terms. Let's get started!

![Concepts](https://img.alicdn.com/imgextra/i1/O1CN01ELiTw41KGKqTmWZua_!!6000000001136-2-tps-756-598.png)

## Essential Terms and Concepts

* **Agent** refers to an autonomous entity capable of performing actions to achieve specific objectives (probably powered by LLMs). In AgentScope, an agent takes the message as input and generates a corresponding response message. Agents can interact with each other to simulate human-like behaviors (e.g., discussion or debate) and cooperate to finish complicated tasks (e.g., generate runnable and reliable code).
* **Message** is a carrier of communication information among agents. It encapsulates information that needs to be conveyed, such as instructions, multi-modal data, or status updates.  In AgentScope, a message is a subclass of Python's dict with additional features for inter-agent communication, including fields such as `name` and `content` for identification and payload delivery.
* **Memory** refers to the structures (e.g., list-like memory, database-based memory) used to store and manage `Msg` (Message) that agents need to remember and store. This can include chat history, knowledge, or other data that informs the agent's future actions.
* **Service** is a collection of functionality tools (e.g., web search, code interpreter, file processing) that provide specific capabilities or processes that are independent of an agent's memory state. Services can be invoked by agents or other components and designed to be reusable across different scenarios.
* **Pipeline** refers to the interaction order or pattern of agents in a task. AgentScope provides built-in `pipelines` to streamline the process of collaboration across multiple agents, such as `SequentialPipeline` and `ForLoopPipeline`. When a `Pipeline` is executed, the *message* passes from predecessors to successors with intermediate results for the task.

## Code Structure

```bash
AgentScope
├── src
│   ├── agentscope
│   |   ├── agents               # Core components and implementations pertaining to agents.
│   |   ├── configs              # Configurations that can be customized for the application's needs.
│   |   ├── memory               # Structures for agent memory.
│   |   ├── models               # Interfaces for integrating diverse model APIs.
│   |   ├── pipeline             # Fundamental components and implementations for running pipelines.
│   |   ├── rpc                  # Rpc module for agent distributed deployment.
│   |   ├── service              # Services offering functions independent of memory and state.
│   |   ├── utils                # Auxiliary utilities and helper functions.
│   |   ├── message.py           # Definitions and implementations of messaging between agents.
|   |   ├── web_ui               # WebUI used to show dialogs.
│   |   ├── prompt.py            # Prompt engineering module for model input.
│   |   ├── ... ..
│   |   ├── ... ..
├── scripts                      # Scripts for launching local Model API
├── examples                     # Pre-built examples of different applications.
├── docs                         # Documentation tool for API reference.
├── tests                        # Unittest modules for continuous integration.
├── LICENSE                      # The official licensing agreement for AgentScope usage.
└── setup.py                     # Setup script for installing.
├── ... ..
└── ... ..
```

[[Return to the top]](#fundamental-concepts)
