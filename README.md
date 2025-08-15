[**中文主页**](https://github.com/agentscope-ai/agentscope/blob/main/README_ZH.md) | [**Tutorial**](https://doc.agentscope.io/) | [**Roadmap**](https://github.com/agentscope-ai/agentscope/blob/main/docs/ROADMAP.md) | [**FAQ**](https://doc.agentscope.io/tutorial/faq.html)

<p align="center">
  <img
    src="https://img.alicdn.com/imgextra/i1/O1CN01nTg6w21NqT5qFKH1u_!!6000000001621-55-tps-550-550.svg"
    alt="AgentScope Logo"
    width="200"
  />
</p>

<h2 align="center">AgentScope: Agent-Oriented Programming for Building LLM Applications</h2>

<p align="center">
    <a href="https://arxiv.org/abs/2402.14034">
        <img
            src="https://img.shields.io/badge/cs.MA-2402.14034-B31C1C?logo=arxiv&logoColor=B31C1C"
            alt="arxiv"
        />
    </a>
    <a href="https://pypi.org/project/agentscope/">
        <img
            src="https://img.shields.io/badge/python-3.10+-blue?logo=python"
            alt="pypi"
        />
    </a>
    <a href="https://pypi.org/project/agentscope/">
        <img
            src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpypi.org%2Fpypi%2Fagentscope%2Fjson&query=%24.info.version&prefix=v&logo=pypi&label=version"
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
            src="https://img.shields.io/badge/GUI-AgentScope_Studio-blue?logo=look&logoColor=green&color=dark-green"
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

Easy for beginners, powerful for experts.

- **Transparent to Developers**: Transparent is our **FIRST principle**. Prompt engineering, API invocation, agent building, workflow orchestration, all are visible and controllable for developers. No deep encapsulation or implicit magic.
- **Realtime Steering**: Interrupt the agent at **ANY** time, and **customize** the handling.
- **Model Agnostic**: Programming once, run with all models.
- **LEGO-style Agent Building**: All components are **modular** and **independent**.
- **Multi-Agent Oriented**: Designed for **multi-agent**, **explicit** message passing and workflow orchestration, NO deep encapsulation.
- **Highly Customizable**: Tools, prompt, agent, workflow, third-party libs & visualization, customization is encouraged everywhere.
- **Developer-friendly**: Low-code development, visual tracing & monitoring. From developing to deployment, all in one place.


Quick overview of AgentScope's new features in v1.0:

| Module     | Feature                                                                            | Tutorial                                                                |
|------------|------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| model      | Support async invocation                                                           | [Model](https://doc.agentscope.io/tutorial/task_model.html)             |
|            | Support reasoning model                                                            |                                                                         |
|            | Support streaming/non-streaming returns                                            |                                                                         |
|            | Support tools API                                                                  |                                                                         |
| tool       | Support async/sync tool functions                                                  | [Tool](https://doc.agentscope.io/tutorial/task_tool.html)               |
|            | Support streaming/non-streaming returns                                            |                                                                         |
|            | Support user interruption                                                          |                                                                         |
|            | Support post-processing                                                            |                                                                         |
|            | Support group-wise tool management                                                 |                                                                         |
|            | Support agent-controlled tools management                                          |                                                                         |
| MCP        | Support streamable HTTP/SSE/StdIO transport                                        | [MCP](https://doc.agentscope.io/tutorial/task_mcp.html)                 |
|            | Support client- & function-level fine-grained control                              |                                                                         |
| agent      | Support async execution                                                            |                                                                         |
|            | Support parallel tool calls                                                        |                                                                         |
|            | Support realtime steering interruption and customized handling                     |                                                                         |
|            | Support automatic state management                                                 |                                                                         |
|            | Support agent-controlled long-term memory                                          |                                                                         |
|            | Support agent hooks                                                                |                                                                         |
| tracing    | Support tracing model, agent, tool                                                 | [Tracing](https://doc.agentscope.io/tutorial/task_tracing.html)         |
|            | Support connecting to third-party tracing platforms (e.g. Arize-Phoenix, Langfuse) |                                                                         |
| memory     | Support long-term memory                                                           | [Memory](https://doc.agentscope.io/tutorial/task_long_term_memory.html) |
| session    | Provide session/application-level state management                                 | [Session](https://doc.agentscope.io/tutorial/task_state.html)           |
| evaluation | Provide distributed and parallel evaluation                                        | [Evaluation](https://doc.agentscope.io/tutorial/task_eval.html)         |
| formatter  | Support multi-agent prompt formatting with tools API                               | [Prompt Formatter](https://doc.agentscope.io/tutorial/task_prompt.html) |
| ...        |                                                                                    |                                                                         |

## 📢 News
- **[2025-08]** The new tutorial of v1 is online now! Check out the [tutorial](https://doc.agentscope.io) for more details.
- **[2025-08]** 🎉🎉 AgentScope v1 is released now! This version fully embraces the asynchronous execution, providing many new features and improvements. Check out [changelog](https://github.com/agentscope-ai/agentscope/blob/main/docs/changelog.md) for detailed changes.

## 💬 Contact

Welcome to join our community on

| [Discord](https://discord.gg/eYMpfnkG8h)                                                                                         | DingTalk                                                                                                                          |
|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i1/O1CN01LxzZha1thpIN2cc2E_!!6000000005934-2-tps-497-477.png" width="100" height="100"> |

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## 🚀 Quickstart

### 💻 Installation

> AgentScope requires **Python 3.10** or higher.

#### 🛠️ From source

```bash
# Pull the source code from GitHub
git clone -b main https://github.com/agentscope-ai/agentscope.git

# Install the package in editable mode
cd agentscope
pip install -e .
```

#### 📦 From PyPi

```bash
pip install agentscope
```

## 👋 Hello AgentScope!

Start with a conversation between user and a ReAct agent 🤖 named "Friday"!

```python
from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, execute_python_code, execute_shell_command
import os, asyncio


async def main():
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(execute_shell_command)

    agent = ReActAgent(
        name="Friday",
        sys_prompt="You're a helpful assistant named Friday.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True,
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
    )

    user = UserAgent(name="user")

    msg = None
    while True:
        msg = await agent(msg)
        msg = await user(msg)
        if msg.get_text_content() == "exit":
            break

asyncio.run(main())
```

## 📖 Documentation

- Tutorial
  - [Installation](https://doc.agentscope.io/tutorial/quickstart_installation.html)
  - [Key Concepts](https://doc.agentscope.io/tutorial/quickstart_key_concept.html)
  - [Create Message](https://doc.agentscope.io/tutorial/quickstart_message.html)
  - [ReAct Agent](https://doc.agentscope.io/tutorial/quickstart_agent.html)
- Workflow
  - [Conversation](https://doc.agentscope.io/tutorial/workflow_conversation.html)
  - [Multi-Agent Debate](https://doc.agentscope.io/tutorial/workflow_multiagent_debate.html)
  - [Concurrent Agents](https://doc.agentscope.io/tutorial/workflow_concurrent_agents.html)
  - [Routing](https://doc.agentscope.io/tutorial/workflow_routing.html)
  - [Handoffs](https://doc.agentscope.io/tutorial/workflow_handoffs.html)
- FAQ
  - [FAQ](https://doc.agentscope.io/tutorial/faq.html)
- Task Guides
  - [Model](https://doc.agentscope.io/tutorial/task_model.html)
  - [Prompt Formatter](https://doc.agentscope.io/tutorial/task_prompt.html)
  - [Tool](https://doc.agentscope.io/tutorial/task_tool.html)
  - [Memory](https://doc.agentscope.io/tutorial/task_memory.html)
  - [Long-Term Memory](https://doc.agentscope.io/tutorial/task_long_term_memory.html)
  - [Agent](https://doc.agentscope.io/tutorial/task_agent.html)
  - [State/Session Management](https://doc.agentscope.io/tutorial/task_state.html)
  - [Agent Hooks](https://doc.agentscope.io/tutorial/task_hook.html)
  - [MCP](https://doc.agentscope.io/tutorial/task_mcp.html)
  - [AgentScope Studio](https://doc.agentscope.io/tutorial/task_studio.html)
  - [Tracing](https://doc.agentscope.io/tutorial/task_tracing.html)
  - [Evaluation](https://doc.agentscope.io/tutorial/task_eval.html)
  - [Embedding](https://doc.agentscope.io/tutorial/task_embedding.html)
  - [Token](https://doc.agentscope.io/tutorial/task_token.html)
- API
  - [API Docs](https://doc.agentscope.io/api/agentscope.html)


## 💻 AgentScope Studio

Use the following command to install and start AgentScope Studio, to trace and visualize your agent application.

```bash
npm install -g @agentscope/studio

as_studio
```

## ⚖️ License

AgentScope is released under Apache License 2.0.

## 📚 Publications

If you find our work helpful for your research or application, please cite our papers.

[AgentScope: A Flexible yet Robust Multi-Agent Platform](https://arxiv.org/abs/2402.14034)

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

## ✨ Contributors

All thanks to our contributors:

<a href="https://github.com/agentscope-ai/agentscope/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=agentscope-ai/agentscope&max=999&columns=12&anon=1" />
</a>