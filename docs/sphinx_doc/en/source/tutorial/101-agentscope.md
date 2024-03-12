(101-agentscope-en)=

# About AgentScope

In this tutorial, we will provide an overview of AgentScope by answering
several questions, including what's AgentScope, what can AgentScope provide,
and why we should choose AgentScope. Let's get started!

## What is AgentScope?

AgentScope is a developer-centric multi-agent platform, which enables
developers to build their LLM-empowered multi-agent applications with less
effort.

With the advance of large language models, developers are able to build
diverse applications.
In order to connect LLMs to data and services and solve complex tasks,
AgentScope provides a series of development tools and components for ease of
development.
It features

- **usability**,
- **robustness**, and
- **the support of multi-modal data** and
- **distributed deployment**.

## Key Concepts

### Message

Message is a carrier of information (e.g. instructions, multi-modal
data, and dialogue). In AgentScope, message is a Python dict subclass
with `name` and `content` as necessary fields, and `url` as an optional
field referring to additional resources.

### Agent

Agent is an autonomous entity capable of interacting with environment and
agents, and taking actions to change the environment. In AgentScope, an
agent takes message as input and generates corresponding response message.

### Service

Service refers to the functional APIs that enable agents to perform
specific tasks. In AgentScope, services are categorized into model API
services, which are channels to use the LLMs, and general API services,
which provide a variety of tool functions.

### Workflow

Workflow represents ordered sequences of agent executions and message
exchanges between agents, analogous to computational graphs in TensorFlow,
but with the flexibility to accommodate non-DAG structures.

## Why AgentScope?

**Exceptional usability for developers.**
AgentScope provides high usability for developers with flexible syntactic
sugars, ready-to-use components, and pre-built examples.

**Robust fault tolerance for diverse models and APIs.**
AgentScope ensures robust fault tolerance for diverse models, APIs, and
allows developers to build customized fault-tolerant strategies.

**Extensive compatibility for multi-modal application.**
AgentScope supports multi-modal data (e.g., files, images, audio and videos)
in both dialog presentation, message transmission and data storage.

**Optimized efficiency for distributed multi-agent operations.** AgentScope
introduces an actor-based distributed mechanism that enables centralized
programming of complex distributed workflows, and automatic parallel
optimization.

## How is AgentScope designed?

The architecture of AgentScope comprises three hierarchical layers. The
layers provide supports for multi-agent applications from different levels,
including elementary and advanced functionalities of a single agent
(**utility layer**), resources and runtime management (**manager and wrapper
layer**), and agent-level to workflow-level programming interfaces (**agent
layer**). AgentScope introduces intuitive abstractions designed to fulfill
the diverse functionalities inherent to each layer and simplify the
complicated interlayer dependencies when building multi-agent systems.
Furthermore, we offer programming interfaces and default mechanisms to
strengthen the resilience of multi-agent systems against faults within
different layers.

## AgentScope Code Structure

```bash
AgentScope
├── src
│   ├── agentscope
│   |   ├── agents               # Core components and implementations pertaining to agents.
│   |   ├── memory               # Structures for agent memory.
│   |   ├── models               # Interfaces for integrating diverse model APIs.
│   |   ├── pipeline             # Fundamental components and implementations for running pipelines.
│   |   ├── rpc                  # Rpc module for agent distributed deployment.
│   |   ├── service              # Services offering functions independent of memory and state.
|   |   ├── web                  # WebUI used to show dialogs.
│   |   ├── utils                # Auxiliary utilities and helper functions.
│   |   ├── message.py           # Definitions and implementations of messaging between agents.
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

[[Return to the top]](#101-agentscope)
