# Distributed Debate Competition

This example demonstrates:
- How to simulate a debate competition with three participant agents
- How to allow human participation in the debate

## Background

This example simulates a debate competition with three participant agents:
1. The affirmative side (**Pro**)
2. The negative side (**Con**)
3. The adjudicator (**Judge**)

The debate topic is whether AGI can be achieved using the GPT model framework. Pro argues in favor, while Con contests it. Judge listens to both sides' arguments and provides an analytical judgment on which side presented a more compelling case.

Each agent is an independent process and can run on different machines. Human participants can join as Pro or Con.

## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- Ollama Chat (qwen2:1.5b)
- Dashscope Chat (qwen-Max)
- Gemini Chat (gemini-pro)

## Prerequisites

Before running the example:
- Install the distributed version of AgentScope by running
```bash
# On windows
pip install -e .[distribute]
# On mac / linux
pip install -e .\[distribute\]
```
- Fill in your model configuration correctly in `configs/model_configs.json`
- Modify the `model_config_name` field in `configs/debate_agent_configs.json` accordingly
- Ensure the specified ports are available and IP addresses are accessible

## Setup and Execution

### Step 1: Setup Pro and Con agent servers

For an LLM-based Pro:
```shell
cd examples/distributed_debate
python distributed_debate.py --role pro --pro-host localhost --pro-port 12011
```

(Alternatively) for human participation as Pro:
```shell
python distributed_debate.py --role pro --pro-host localhost --pro-port 12011 --is-human
```

For an LLM-based Con:
```shell
python distributed_debate.py --role con --con-host localhost --con-port 12012
```

(Alternatively) for human participation as Con:
```shell
python distributed_debate.py --role con --con-host localhost --con-port 12012 --is-human
```

### Step 2: Run the main process

```shell
python distributed_debate.py --role main --pro-host localhost --pro-port 12011 --con-host localhost --con-port 12012
```

### Step 3: Watch or join the debate in your terminal

If you join as Con, you'll see something like:

```text
System: Welcome to the debate on whether Artificial General Intelligence (AGI) can be achieved
...
Pro: Thank you. I argue that AGI can be achieved using the GPT model framework.
...
User Input:
```
