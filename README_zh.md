[**English Homepage**](https://github.com/agentscope-ai/agentscope/blob/main/README.md) | [**Tutorial**](https://doc.agentscope.io/zh_CN/) | [**Roadmap**](https://github.com/agentscope-ai/agentscope/blob/main/docs/roadmap.md) | [**FAQ**](https://doc.agentscope.io/zh_CN/tutorial/faq.html)

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

## ✨ Why AgentScope？

浅显入门，精深致用。

- **对开发者透明**: 透明是 AgentScope 的**首要原则**。无论提示工程、API调用、智能体构建还是工作流程编排，坚持对开发者可见&可控。拒绝深度封装或隐式魔法。
- **实时引导**: 支持在**任意**时刻打断智能体回复，并支持**自定义**处理方式。
- **模型无关**: 一次编程，适配所有模型。
- **“乐高式”智能体构建**: 所有组件保持**模块化**且**相互独立**。
- **面向多智能体**：专为**多智能体**设计，**显式**的消息传递和工作流编排，拒绝深度封装。
- **高度可定制**: 工具、提示、Agent、工作流、第三方库和可视化，AgentScope 支持&鼓励开发者进行定制。
- **开发者友好**: 低代码开发，可视化追踪和监控。从开发到部署，一站式解决。

AgentScope v1.0 新功能概览:

| 模块         | 功能                                  | 文档                                                                            |
|------------|-------------------------------------|-------------------------------------------------------------------------------|
| model      | 支持异步调用                              | [Model](https://doc.agentscope.io/zh_CN/tutorial/task_model.html)             |
|            | 支持推理模型                              |                                                                               |
|            | 支持流式/非流式返回                          |                                                                               |
|            | 支持工具API                             |                                                                               |
| tool       | 支持异步/同步工具函数                         | [Tool](https://doc.agentscope.io/zh_CN/tutorial/task_tool.html)               |
|            | 支持工具函数流式/非流式返回                      |                                                                               |
|            | 支持用户打断                              |                                                                               |
|            | 支持工具函数的后处理                          |                                                                               |
|            | 支持分组工具管理                            |                                                                               |
|            | 允许智能体自主管理工具                         |                                                                               |
| MCP        | 支持 Streamable HTTP/SSE/StdIO 传输     | [MCP](https://doc.agentscope.io/zh_CN/tutorial/task_mcp.html)                 |
|            | 支持函数级别的精细控制                         |                                                                               |
| agent      | 支持异步执行                              |                                                                               |
|            | 支持并行工具调用                            |                                                                               |
|            | 支持用户实时中断和自定义的中断处理                   |                                                                               |
|            | 支持自动状态管理                            |                                                                               |
|            | 允许智能体自主控制长期记忆                       |                                                                               |
|            | 支持智能体钩子函数                           |                                                                               |
| tracing    | 支持追踪模型、智能体、工具                       | [Tracing](https://doc.agentscope.io/zh_CN/tutorial/task_tracing.html)         |
|            | 支持连接到第三方平台（如Arize-Phoenix、Langfuse） |                                                                               |
| memory     | 支持长期记忆                              | [Memory](https://doc.agentscope.io/zh_CN/tutorial/task_long_term_memory.html) |
| session    | 提供会话/应用级状态管理                        | [Session](https://doc.agentscope.io/zh_CN/tutorial/task_state.html)           |
| evaluation | 提供分布式和并行评估                          | [Evaluation](https://doc.agentscope.io/zh_CN/tutorial/task_eval.html)         |
| formatter  | 支持多Agent提示格式化与工具API                 | [Prompt Formatter](https://doc.agentscope.io/zh_CN/tutorial/task_prompt.html) |
| ...        |                                     |                                                                               |

## 📢 新闻
- **[2025-08]** v1 版本 Tutorial 已上线！查看[tutorial](https://doc.agentscope.io/zh_CN/)了解更多详情。
- **[2025-08]** 🎉🎉 AgentScope v1现已发布！在完全拥抱异步执行的基础上提供许多新功能和改进。查看[changelog](https://github.com/agentscope-ai/agentscope/blob/main/docs/changelog.md)了解详细变更。

## 💬 联系我们

欢迎加入我们的社区，获取最新的更新和支持！

| [Discord](https://discord.gg/eYMpfnkG8h)                                                                                         | 钉钉                                                                                                                              |
|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i1/O1CN01LxzZha1thpIN2cc2E_!!6000000005934-2-tps-497-477.png" width="100" height="100"> |

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## 🚀 快速开始

### 💻 安装

> AgentScope需要**Python 3.10**或更高版本。

#### 🛠️ 从源码安装

```bash
# 从 GitHub 拉取源码
git clone -b main https://github.com/agentscope-ai/agentscope.git

# 以可编辑模式安装包
cd agentscope
pip install -e .
```

#### 📦 从PyPi安装

```bash
pip install agentscope
```

## 👋 Hello AgentScope！

使用 AgentScope 显式地创建一个名为“Friday”的助手🤖，并与之对话。

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

## 📖 文档

- 教程
  - [安装](https://doc.agentscope.io/zh_CN/tutorial/quickstart_installation.html)
  - [核心概念](https://doc.agentscope.io/zh_CN/tutorial/quickstart_key_concept.html)
  - [创建消息](https://doc.agentscope.io/zh_CN/tutorial/quickstart_message.html)
  - [ReAct Agent](https://doc.agentscope.io/zh_CN/tutorial/quickstart_agent.html)
- 工作流
  - [对话（Conversation）](https://doc.agentscope.io/zh_CN/tutorial/workflow_conversation.html)
  - [多智能体辩论（Multi-Agent Debate）](https://doc.agentscope.io/zh_CN/tutorial/workflow_multiagent_debate.html)
  - [智能体并发（Concurrent Agents）](https://doc.agentscope.io/zh_CN/tutorial/workflow_concurrent_agents.html)
  - [路由（Routing）](https://doc.agentscope.io/zh_CN/tutorial/workflow_routing.html)
  - [交接（Handoffs）](https://doc.agentscope.io/zh_CN/tutorial/workflow_handoffs.html)
- 常见问题
  - [FAQ](https://doc.agentscope.io/zh_CN/tutorial/faq.html)
- 任务指南
  - [模型](https://doc.agentscope.io/zh_CN/tutorial/task_model.html)
  - [提示格式化器](https://doc.agentscope.io/zh_CN/tutorial/task_prompt.html)
  - [工具](https://doc.agentscope.io/zh_CN/tutorial/task_tool.html)
  - [记忆](https://doc.agentscope.io/zh_CN/tutorial/task_memory.html)
  - [长期记忆](https://doc.agentscope.io/zh_CN/tutorial/task_long_term_memory.html)
  - [智能体](https://doc.agentscope.io/zh_CN/tutorial/task_agent.html)
  - [管道（Pipeline）](https://doc.agentscope.io/zh_CN/tutorial/task_pipeline.html)
  - [状态/会话管理](https://doc.agentscope.io/zh_CN/tutorial/task_state.html)
  - [智能体钩子函数](https://doc.agentscope.io/zh_CN/tutorial/task_hook.html)
  - [MCP](https://doc.agentscope.io/zh_CN/tutorial/task_mcp.html)
  - [AgentScope Studio](https://doc.agentscope.io/zh_CN/tutorial/task_studio.html)
  - [追踪](https://doc.agentscope.io/zh_CN/tutorial/task_tracing.html)
  - [智能体评测](https://doc.agentscope.io/zh_CN/tutorial/task_eval.html)
  - [嵌入（Embedding）](https://doc.agentscope.io/zh_CN/tutorial/task_embedding.html)
  - [Token计数](https://doc.agentscope.io/zh_CN/tutorial/task_token.html)
- API
  - [API文档](https://doc.agentscope.io/zh_CN/api/agentscope.html)

## 💻 AgentScope Studio

使用以下命令安装并启动 AgentScope Studio，以追踪和可视化您的Agent应用。

```bash
npm install -g @agentscope/studio

as_studio
```

## 👨‍💻 开发

设置开发环境：

```bash
# 克隆代码仓库
git clone https://github.com/agentscope-ai/agentscope.git
cd agentscope

# 使用 uv 安装依赖
uv sync

# 安装完整依赖（可选）
uv sync --extra full

# 安装开发依赖（可选）
uv sync --extra dev
```

## ⚖️ 许可

AgentScope 基于 Apache License 2.0发布。

## 📚 论文

如果我们的工作对您的研究或应用有帮助，请引用我们的论文。

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

## ✨ 贡献者

感谢所有贡献者：

<a href="https://github.com/agentscope-ai/agentscope/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=modelscope/agentscope&max=999&columns=12&anon=1" />
</a>

