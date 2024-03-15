# Create an Agent with LangChain

AgentScope is a highly flexible multi-agent platform. It allows developers
to create agents with third-party libraries.

In this example, we will show how to create an assistant agent with
LangChain in AgentScope, and interact with user in a conversation.

**Note** we use OpenAI API for LangChain in this example. Developers can
modify it according to their own needs.

## Install LangChain

Before running the example, please install LangChain by the following command:
```bash
pip install langchain==0.1.11 langchain-openai==0.0.8
```

## Create Agent with LangChain

In this example, the memory management, prompt engineering, and model
invocation are all handled by LangChain.
Specifically, we create an agent class named `LangChainAgent`.
In its `reply` function, developers only need parse the input message and
wrap the output message into `agentscope.message.Msg` class.
After that, developers can build the conversation in AgentScope, and the
`LangChainAgent` is the same as other agents in AgentScope.
