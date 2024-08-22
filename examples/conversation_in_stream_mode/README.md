# Conversation in Stream Mode

In this example, we will show
- How to set up the stream mode in AgentScope
- How to print in stream mode in both terminal and AgentScope Studio

Refer to our tutorial for more information: [Streaming](https://modelscope.github.io/agentscope/en/tutorial/203-stream.html).

## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- qwen-max in DashScope
- llama2 in ollama
- gpt-4
- gemini-pro
- gpt-4 in litellm


## Prerequisites

- Install the lastest version of AgentScope by

```bash
git clone https://github.com/modelscope/agentscope
cd agentscope
pip install -e .
```

- Fill your `api_key` in `main.py` to use your own model API. Then run the example by

```bash
python main.py
```

## What We do in this Example

We create a new StreamingAgent in `main.py` and print the text in stream mode. The text will be printed in both terminal and AgentScope Studio.

Please refer to `main.py` for more details.