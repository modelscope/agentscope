[**中文主页**](https://github.com/modelscope/agentscope/blob/main/README_ZH.md) | [**日本語のホームページ**](https://github.com/modelscope/agentscope/blob/main/README_JA.md) | [**Tutorial**](https://doc.agentscope.io/) | [**Roadmap**](https://github.com/modelscope/agentscope/blob/main/docs/ROADMAP.md)

<p align="center">
    <img align="center" src="https://img.alicdn.com/imgextra/i3/O1CN01ywJShe1PU90G8ZYtM_!!6000000001843-55-tps-743-743.svg" width="110" height="110" style="margin: 30px">
</p>
<h2 align="center">AgentScope: Agent-oriented programming for building LLM applications</h2>

<p align="center">
    <a href="https://arxiv.org/abs/2402.14034">
        <img
            src="https://img.shields.io/badge/cs.MA-2402.14034-B31C1C?logo=arxiv&logoColor=B31C1C"
            alt="arxiv"
        />
    </a>
    <a href="https://pypi.org/project/agentscope/">
        <img
            src="https://img.shields.io/badge/python-3.9+-blue"
            alt="pypi"
        />
    </a>
    <a href="https://pypi.org/project/agentscope/">
        <img
            src="https://img.shields.io/badge/pypi-v0.1.5-blue?logo=pypi"
            alt="pypi"
        />
    </a>
    <a href="https://doc.agentscope.io/">
        <img
            src="https://img.shields.io/badge/Docs-English%7C%E4%B8%AD%E6%96%87-blue?logo=markdown"
            alt="docs"
        />
    </a>
    <a href="https://agentscope.io/">
        <img
            src="https://img.shields.io/badge/Drag_and_drop_UI-WorkStation-blue?logo=html5&logoColor=green&color=dark-green"
            alt="workstation"
        />
    </a>
    <a href="./LICENSE">
        <img
            src="https://img.shields.io/badge/license-Apache--2.0-black"
            alt="license"
        />
    </a>
</p>

<p align="center">
<img src="https://trendshift.io/api/badge/repositories/10079" alt="modelscope%2Fagentscope | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/>
</p>

## ✨ Why AgentScope?

* **Transparent**: All are visible and controllable for developers, from [agent building](https://doc.agentscope.io/build_tutorial/agent.html) to [workflow orchestration](https://doc.agentscope.io/build_tutorial/conversation.html), from [prompt construction](https://doc.agentscope.io/build_tutorial/prompt.html) to [prompt optimization](https://doc.agentscope.io/build_tutorial/prompt_optimization.html),
 from [API calling](https://doc.agentscope.io/build_tutorial/model.html) to [response parsing](https://doc.agentscope.io/build_tutorial/structured_output.html).

* **Explicit Programming**: What you see is what you get, no implicit magic, no deep encapsulation. The workflow is explicitly constructed through [message passing](https://doc.agentscope.io/build_tutorial/message.html), providing developers with full control and visibility over the execution flow.

* **Modular**: All components are independent, use them or not, it's your choice.

* **Model-agnostic**: Develop once to [adapt to all models](https://doc.agentscope.io/build_tutorial/prompt.html).

* **Multi-agent oriented Programming**: Pythonic programming for [building multi-agent applications](https://doc.agentscope.io/build_tutorial/conversation.html#more-than-two-agents). Simple for beginners, powerful for experts.

* **Distribution**: Centralized programming for distributed multi-agent applications with [automatic parallelization](https://doc.agentscope.io/build_tutorial/distribution.html).

* **Graphical Programming**: Provide [visual tracing](https://doc.agentscope.io/build_tutorial/visual.html) for multi-agent applications, as well as [low-code development](https://doc.agentscope.io/build_tutorial/low_code.html).



## 📢 News
- **[2025-04-27]** A new AgentScope Studio is online now. Refer [here](https://doc.agentscope.io/build_tutorial/visual.html) for more details.

- **[2025-03-21]** AgentScope supports hooks functions now. Refer to our [tutorial](https://doc.agentscope.io/build_tutorial/hook.html) for more details.

- **[2025-03-19]** AgentScope supports tools API now. Refer to our [tutorial](https://doc.agentscope.io/build_tutorial/tool.html).

- **[2025-03-20]** Agentscope now supports [MCP Server](https://github.com/modelcontextprotocol/servers)! You can learn how to use it by following this [tutorial](https://doc.agentscope.io/build_tutorial/MCP.html).

- **[2025-03-05]** Our [multi-source RAG Application](applications/multisource_rag_app/README.md) (the chatbot used in our Q&A DingTalk group) is open-source now!

- **[2025-02-24]** [Chinese version tutorial](https://doc.agentscope.io/zh_CN) is online now!

- **[2025-02-13]** We have released the [technical report](https://doc.agentscope.io/tutorial/swe.html) of our solution in [SWE-Bench(Verified)](https://www.swebench.com/)!

- **[2025-02-07]** 🎉 AgentScope has achieved a **63.4% resolve rate** in [SWE-Bench(Verified)](https://www.swebench.com/). More details about our solution are coming soon!

- **[2025-01-04]** AgentScope supports Anthropic API now.

👉👉 [**Older News**](https://github.com/modelscope/agentscope/blob/main/docs/news_en.md)

## Table of Contents

---

<!-- START doctoc -->
<!-- END doctoc -->


## 🚀 Quickstart

### Installation

> AgentScope requires **Python 3.9** or higher.

#### From source

```bash
# Pull the source code from GitHub
git clone https://github.com/modelscope/agentscope.git

# Install the package in editable mode
cd agentscope
pip install -e .
```

#### From PyPi

```bash
pip install agentscope
```

## 👋 Hello AgentScope

Creating a basic multi-agent conversation with AgentScope:

```python
from agentscope.agents import DialogAgent, UserAgent
import agentscope

# Load model configs
agentscope.init(
    model_configs=[
        {
            "config_name": "my_config",
            "model_type": "dashscope_chat",
            "model_name": "qwen-max",
        }
    ]
)

# Create a dialog agent and a user agent
dialog_agent = DialogAgent(
   name="assistant",
   model_config_name="my_config"
)
user_agent = UserAgent(name="user")

# Build the workflow/conversation explicitly
x = None
while True:
    x = dialog_agent(x)
    x = user_agent(x)
    if x.content == "exit":
        break
```

## 🧑‍🤝‍🧑 Multi-agent Conversation

```python

```

## 💡 Reasoning Agent with Tools

Creating a reasoning agent with built-in tools and **MCP servers**!

```python
from agentscope.agents import ReActAgentV2, UserAgent
from agentscope.service import ServiceToolkit, execute_python_code
import agentscope

agentscope.init(
    model_configs={
        "model_config": "my_config",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
    }
)

# Add tools
toolkit = ServiceToolkit()
toolkit.add(execute_python_code)

# Connect to MCP server
toolkit.add_mcp_servers(
    {
        "mcpServers": {
            "puppeteer": {
                "url": "http://127.0.0.1:8000/sse",
            },
        },
    }
)

# Create a reasoning-acting agent
agent = ReActAgentV2(
    name="Friday",
    model_config_name="my_config",
    service_toolkit=toolkit,
    max_iters=20
)
user_agent = UserAgent(name="user")

# Build the workflow/conversation explicitly
x = None
while True:
    x = agent(x)
    x = user_agent(x)
    if x.content == "exit":
        break
```

## 🔠 Structured Output

Specifying structured output easily!

```python
from agentscope.agents import ReActAgentV2
from agentscope.service import ServiceToolkit
from agentscope.message import Msg
from pydantic import BaseModel, Field
from typing import Literal
import agentscope

agentscope.init(
    model_configs={
        "model_config": "my_config",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
    }
)

# Create a reasoning-acting agent
agent = ReActAgentV2(
    name="Friday",
    model_config_name="my_config",
    service_toolkit=ServiceToolkit(),
    max_iters=20
)

class CvModel(BaseModel):
    name: str = Field(max_length=50, description="The name")
    description: str = Field(max_length=200, description="The brief description")
    aget: int = Field(gt=0, le=120, description="The age of the person")

class ChoiceModel(BaseModel):
    choice: Literal["apple", "banana"]

# Specify structured output using `structured_model`
res_msg = agent(
    Msg("user", "Introduce Einstein", "user"),
    structured_model=CvModel
)
print(res_msg.metadata)

# Switch to different structured model
res_msg = agent(
    Msg("user", "Choice a fruit", "user"),
    structured_model=ChoiceModel
)
print(res_msg.metadata)
```

## ⚡️ Distribution and Parallelization

Using a magic function `to_dist` to run the agent in distributed mode!

```python
from agentscope.agents import DialogAgent
from agentscope.message import Msg
import agentscope

# Load model configs
agentscope.init(
    model_configs=[
        {
            "config_name": "my_config",
            "model_type": "dashscope_chat",
            "model_name": "qwen-max",
        }
    ]
)

# Using `to_dist()` to run the agent in distributed mode
agent1 = DialogAgent(
   name="Saturday",
   model_config_name="my_config"
).to_dist()

agent2 = DialogAgent(
   name="Sunday",
   model_config_name="my_config"
).to_dist()

# The two agent will run in parallel
agent1(Msg("user", "", "user"))
agent2(Msg("user", "", "user"))
```

## 👀 Visualization

AgentScope supports **Gradio** and **AgentScope Studio** for visualization. Third-party visualization tools are also supported.

<p align="center">
    <img
        src="https://img.alicdn.com/imgextra/i4/O1CN01eCEYvA1ueuOkien7T_!!6000000006063-1-tps-960-600.gif"
        alt="AgentScope Studio"
        width="45%"
    />
    <img
        src="https://img.alicdn.com/imgextra/i4/O1CN01eCEYvA1ueuOkien7T_!!6000000006063-1-tps-960-600.gif"
        alt="AgentScope Studio"
        width="45%"
    />
</p>

Connect to **Third-party visualization** is also supported!

```python
from agentscope.agents import AgentBase
from agentscope.message import Msg
import requests


def forward_message_hook(self, msg: Msg, stream: bool, last: bool) -> None:
    """Forward the displayed message to third-party visualization tools."""
    # Taking RESTFul API as an example
    requests.post(
        "https://xxx.com",
        json={
            "msg": msg.to_dict(),
            "stream": stream,
            "last": last
        }
    )

# Register as a class-level hook, that all instances will use this hook
AgentBase.register_class_hook(
    hook_type='pre_speak',
    hook_name='forward_to_third_party',
    hook=forward_message_hook
)
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