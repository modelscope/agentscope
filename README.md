[**中文主页**](https://github.com/modelscope/agentscope/blob/main/README_ZH.md) | [**日本語のホームページ**](https://github.com/modelscope/agentscope/blob/main/README_JA.md) | [**Tutorial**](https://doc.agentscope.io/) | [**Roadmap**](https://github.com/modelscope/agentscope/blob/main/docs/ROADMAP.md)

# Agent-oriented programming for building LLM applications

<h5 align="left">
<img src="https://img.alicdn.com/imgextra/i2/O1CN01cdjhVE1wwt5Auv7bY_!!6000000006373-0-tps-1792-1024.jpg" width="600" alt="agentscope-logo">
</h5>

[![](https://img.shields.io/badge/cs.MA-2402.14034-B31C1C?logo=arxiv&logoColor=B31C1C)](https://arxiv.org/abs/2402.14034)
[![](https://img.shields.io/badge/python-3.9+-blue)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/pypi-v0.1.1-blue?logo=pypi)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/Docs-English%7C%E4%B8%AD%E6%96%87-blue?logo=markdown)](https://modelscope.github.io/agentscope/#welcome-to-agentscope-tutorial-hub)
[![](https://img.shields.io/badge/Docs-API_Reference-blue?logo=markdown)](https://modelscope.github.io/agentscope/)
[![](https://img.shields.io/badge/Docs-Roadmap-blue?logo=markdown)](https://github.com/modelscope/agentscope/blob/main/docs/ROADMAP.md)

[![](https://img.shields.io/badge/Drag_and_drop_UI-WorkStation-blue?logo=html5&logoColor=green&color=dark-green)](https://agentscope.io/)
[![](https://img.shields.io/badge/license-Apache--2.0-black)](./LICENSE)
[![](https://img.shields.io/badge/Contribute-Welcome-green)](https://modelscope.github.io/agentscope/tutorial/contribute.html)

<img src="https://trendshift.io/api/badge/repositories/10079" alt="modelscope%2Fagentscope | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/>

- Welcome to join our community on

| [Discord](https://discord.gg/eYMpfnkG8h)                                                                                         | DingTalk                                                                                                                          |
|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i1/O1CN01LxzZha1thpIN2cc2E_!!6000000005934-2-tps-497-477.png" width="100" height="100"> |

## News
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-03-20]** Agentscope now supports [MCP Server](https://github.com/modelcontextprotocol/servers)! You can learn how to use it by following this [tutorial](https://doc.agentscope.io/build_tutorial/mcp.html).

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-03-05]** Our [multi-source RAG Application](applications/multisource_rag_app/README.md) (the chatbot used in our Q&A DingTalk group) is open-source now!

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-02-24]** [Chinese version tutorial](https://doc.agentscope.io/zh_CN) is online now!

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-02-13]** We have released the [technical report](https://doc.agentscope.io/tutorial/swe.html) of our solution in [SWE-Bench(Verified)](https://www.swebench.com/)!

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-02-07]** 🎉 AgentScope has achieved a **63.4% resolve rate** in [SWE-Bench(Verified)](https://www.swebench.com/). More details about our solution are coming soon!

- **[2025-01-04]** AgentScope supports Anthropic API now.

- [**Older News**](https://github.com/modelscope/agentscope/blob/main/docs/news_en.md)

## Why AgentScope?

* **Transparent**: All are visible and controllable for developers, from [agent building](https://doc.agentscope.io/build_tutorial/agent.html) to [workflow orchestration](https://doc.agentscope.io/build_tutorial/conversation.html), from [prompt construction](https://doc.agentscope.io/build_tutorial/prompt.html) to [prompt optimization](https://doc.agentscope.io/build_tutorial/prompt_optimization.html),
 from [API calling](https://doc.agentscope.io/build_tutorial/model.html) to [response parsing](https://doc.agentscope.io/build_tutorial/structured_output.html).

* **Explicit Programming**: What you see is what you get, no implicit magic, no deep encapsulation. The workflow is explicitly constructed through [message passing](https://doc.agentscope.io/build_tutorial/message.html), providing developers with full control and visibility over the execution flow.

* **Modular**: All components are independent, use them or not, it's your choice.

* **Model-agnostic**: Develop once to [adapt to all models](https://doc.agentscope.io/build_tutorial/prompt.html).

* **Multi-agent oriented Programming**: Pythonic programming for [building multi-agent applications](https://doc.agentscope.io/build_tutorial/conversation.html#more-than-two-agents). Simple for beginners, powerful for experts.

* **Distribution**: Centralized programming for distributed multi-agent applications with [automatic parallelization](https://doc.agentscope.io/build_tutorial/distribution.html).

* **Graphical Programming**: Provide [visual tracing](https://doc.agentscope.io/build_tutorial/visual.html) for multi-agent applications, as well as [low-code development](https://doc.agentscope.io/build_tutorial/low_code.html).


## Quickstart

### Installation

AgentScope requires **Python 3.9** or higher.

#### From source

- Install AgentScope in editable mode:

```bash
# Pull the source code from GitHub
git clone https://github.com/modelscope/agentscope.git

# Install the package in editable mode
cd agentscope
pip install -e .
```

#### Using pip

- Install AgentScope from pip:

```bash
pip install agentscope
```

### Hello World

Create a multi-agent conversation with AgentScope:

```python
from agentscope.agents import DialogAgent, UserAgent
import agentscope

# Load model configs
agentscope.init(
    model_configs=[
        {
            "config_name": "my_openai_config",
            "model_type": "openai_chat",
            "model_name": "gpt-4o",
            "api_key": "xxx",
        }
    ]
)

# Create a dialog agent and a user agent
dialog_agent = DialogAgent(
   name="assistant",
   model_config_name="my_openai_config"
)
user_agent = UserAgent()

# Build the workflow/conversation explicitly
x = None
while True:
    x = dialog_agent(x)
    x = user_agent(x)
    if x.content == "exit":
        break
```

## License

AgentScope is released under Apache License 2.0.

## Publications

If you find our work helpful for your research or application, please cite our papers.

1. [AgentScope: A Flexible yet Robust Multi-Agent Platform](https://arxiv.org/abs/2402.14034)

    ```
    @article{agentscope,
        author  = {Dawei Gao and
                   Zitao Li and
                   Xuchen Pan and
                   Weirui Kuang and
                   Zhijian Ma and
                   Bingchen Qian and
                   Fei Wei and
                   Wenhao Zhang and
                   Yuexiang Xie and
                   Daoyuan Chen and
                   Liuyi Yao and
                   Hongyi Peng and
                   Ze Yu Zhang and
                   Lin Zhu and
                   Chen Cheng and
                   Hongzhu Shi and
                   Yaliang Li and
                   Bolin Ding and
                   Jingren Zhou}
        title   = {AgentScope: A Flexible yet Robust Multi-Agent Platform},
        journal = {CoRR},
        volume  = {abs/2402.14034},
        year    = {2024},
    }
    ```

## Contributors ✨

All thanks to our contributors:

<a href="https://github.com/modelscope/agentscope/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=modelscope/agentscope&max=999&columns=12&anon=1" />
</a>