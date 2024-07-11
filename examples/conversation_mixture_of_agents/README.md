# Using Mixture of Agents to Enhance Performance in AgentScope

This example will show how to use Mixture of Agents in AgentScope.

## Background

There are many existing efforts to enhance the performance of large language models (LLMs) by stacking the number of models during inference time.
Existing works such as [MoA](https://github.com/togethercomputer/MoA), [More Agent is All You Need](https://arxiv.org/abs/2402.05120) have already shown promising results.
You can refer to the [paper of MoA](https://arxiv.org/abs/2406.04692) or their [Readme.md](https://github.com/togethercomputer/MoA/blob/main/README.md) for more details.

## Implementation

Here, we implement the MoA algorithm in AgentScope, and provide an example of using MoA.
For implementation, please refer to [mixture_of_agent.py](https://github.com/modelscope/agentscope/blob/main/src/agentscope/utils/mixture_of_agent.py).


## Usage
You can have a conversation with the MoA module by running the following code:


```python
python conversation_moa.py --show_internal --multi_turn --rounds 1
```

## Prerequisites
To set up model serving with open-source LLMs, follow the guidance in
[scripts/README.md](https://github.com/modelscope/agentscope/blob/main/scripts/README.md).

## Notice
With the MoA module, inference time will increase and more tokens are used.