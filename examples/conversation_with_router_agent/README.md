# Conversation with Router Agent

This example will show
- How to build a router agent to route questions to agents with different abilities.

The router agent is expected to route questions to the corresponding agents according to the question type in the following response
```text
<thought>{The thought of router agent}</thought>
<agent>{agent name}</agent>
```
If the router agent decides to answer the question itself, the response should be
```text
<thought>{The thought of router agent}</thought>
<response>{The answer}</response>
```

## Note
This example is only for demonstration purposes. We simply use two agents who are good at math and history respectively.
You can replace them with any other agents according to your needs.

Besides, the memory management of the involved agents is not considered in this example.
For example, does the router agent need to know the answer from the sub-agents?
Improvements are encouraged by developers according to their own needs.

## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- gpt-4o
- qwen-max


## Prerequisites

1. Fill your model configuration correctly in `main.py`.
2. Install the latest version of Agentscope from GitHub.
```bash
git clone https://github.com/modelscope/agentscope.git
cd agentscope
pip install -e .
```
3. Run the example and input your questions.
```bash
python main.py
```
