# Using Mixture of Agents to enhance perfomance in AgentScope

This example will show how to use Mixture of Agents in AgentScope.


## Background

There are many exist efforts to enhance the performance large language model (LLM) by stacking the number of models during inference time.
Existing works such as [MoA](https://github.com/togethercomputer/MoA), [More Agent is All You Need](https://arxiv.org/abs/2402.05120) have already show promising results.

You can refere to the [paper of MoA](https://arxiv.org/abs/2406.04692) or their [Readme.md](https://github.com/togethercomputer/MoA/blob/main/README.md) for more details.

## Implementation
Here, we implement the MoA algorithm in the AgentScope, and provide an example of using MoA.

For Implementation, please refer to [mixture_of_agent.py](../../src/agentscope/utils/mixture_of_agent.py).


## Usage
You can have conversation with MoA module by runing the code:

```python
python converstaion_moa.py --show_internal --multi_turn --rounds 1
```

## Prerequisites
To set up model serving with open-source LLMs, follow the guidance in
[scripts/REAMDE.md](../../scripts/README.md).

## Notice
With MoA module, inference time will increase and more tokens are used.