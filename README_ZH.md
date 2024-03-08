# AgentScope

[![](https://img.shields.io/badge/cs.MA-2402.14034-B31C1C?logo=arxiv&logoColor=B31C1C)](https://arxiv.org/abs/2402.14034)
[![](https://img.shields.io/badge/python-3.9+-blue)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/pypi-v0.0.1-blue?logo=pypi)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/Docs-English%7C%E4%B8%AD%E6%96%87-blue?logo=markdown)](https://modelscope.github.io/agentscope/#welcome-to-agentscope-tutorial-hub)
[![](https://img.shields.io/badge/Docs-API_Reference-blue?logo=markdown)](https://modelscope.github.io/agentscope/)
[![](https://img.shields.io/badge/ModelScope-Demos-4e29ff.svg?logo=data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMjI0IDEyMS4zMyIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KCTxwYXRoIGQ9Im0wIDQ3Ljg0aDI1LjY1djI1LjY1aC0yNS42NXoiIGZpbGw9IiM2MjRhZmYiIC8+Cgk8cGF0aCBkPSJtOTkuMTQgNzMuNDloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzYyNGFmZiIgLz4KCTxwYXRoIGQ9Im0xNzYuMDkgOTkuMTRoLTI1LjY1djIyLjE5aDQ3Ljg0di00Ny44NGgtMjIuMTl6IiBmaWxsPSIjNjI0YWZmIiAvPgoJPHBhdGggZD0ibTEyNC43OSA0Ny44NGgyNS42NXYyNS42NWgtMjUuNjV6IiBmaWxsPSIjMzZjZmQxIiAvPgoJPHBhdGggZD0ibTAgMjIuMTloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzM2Y2ZkMSIgLz4KCTxwYXRoIGQ9Im0xOTguMjggNDcuODRoMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzYyNGFmZiIgLz4KCTxwYXRoIGQ9Im0xOTguMjggMjIuMTloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzM2Y2ZkMSIgLz4KCTxwYXRoIGQ9Im0xNTAuNDQgMHYyMi4xOWgyNS42NXYyNS42NWgyMi4xOXYtNDcuODR6IiBmaWxsPSIjNjI0YWZmIiAvPgoJPHBhdGggZD0ibTczLjQ5IDQ3Ljg0aDI1LjY1djI1LjY1aC0yNS42NXoiIGZpbGw9IiMzNmNmZDEiIC8+Cgk8cGF0aCBkPSJtNDcuODQgMjIuMTloMjUuNjV2LTIyLjE5aC00Ny44NHY0Ny44NGgyMi4xOXoiIGZpbGw9IiM2MjRhZmYiIC8+Cgk8cGF0aCBkPSJtNDcuODQgNzMuNDloLTIyLjE5djQ3Ljg0aDQ3Ljg0di0yMi4xOWgtMjUuNjV6IiBmaWxsPSIjNjI0YWZmIiAvPgo8L3N2Zz4K)](https://modelscope.cn/studios?name=agentscope&page=1&sort=latest)

[![](https://img.shields.io/badge/license-Apache--2.0-black)](./LICENSE)
[![](https://img.shields.io/badge/Contribute-Welcome-green)](https://modelscope.github.io/agentscope/tutorial/contribute.html)

AgentScope是一款全新的Multi-Agent框架，专为应用开发者打造，旨在提供高易用、高可靠的编程体验！

- **高易用**：AgentScope支持纯Python编程，提供多种语法工具实现灵活的应用流程编排，内置丰富的API服务（Service）以及应用样例，供开发者直接使用。同时，AgentScope提供了详尽的[教程](https://modelscope.github.io/agentscope/)，[API文档](https://modelscope.github.io/agentscope/)和[应用样例](https://modelscope.github.io/agentscope/)。

- **高鲁棒**：确保开发便捷性和编程效率的同时，针对不同能力的大模型，AgentScope提供了全面的重试机制、定制化的容错控制和面向Agent的异常处理，以确保应用的稳定、高效运行；

- **基于Actor的分布式机制**：AgentScope设计了一种新的基于Actor的分布式机制，实现了复杂分布式工作流的集中式编程和自动并行优化，即用户可以使用中心化编程的方式完成分布式应用的流程编排，同时能够零代价将本地应用迁移到分布式的运行环境中。

如果您觉得我们的工作对您有帮助，请引用[我们的论文](https://arxiv.org/abs/2402.14034)。

欢迎加入我们的社区

| [Discord](https://discord.gg/eYMpfnkG8h) | 钉钉群 | 微信 |
|---------|----------|--------|
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i2/O1CN01tuJ5971OmAqNg9cOw_!!6000000001747-0-tps-444-460.jpg" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i3/O1CN01UyfWfx1CYBM3WqlBy_!!6000000000092-2-tps-400-400.png" width="100" height="100"> |

目录
=================

- [AgentScope](#agentscope)
- [目录](#目录)
  - [安装](#安装)
    - [从源码安装](#从源码安装)
    - [使用pip](#使用pip)
  - [快速开始](#快速开始)
    - [基础使用](#基础使用)
      - [第1步：准备Model Configs](#第1步准备model-configs)
        - [OpenAI API Configs](#openai-api-configs)
        - [Post Request API Config](#post-request-api-config)
      - [第2步：创建Agent](#第2步创建agent)
      - [第3步：构造对话](#第3步构造对话)
    - [进阶使用](#进阶使用)
      - [**Pipeline**和**MsgHub**](#pipeline和msghub)
      - [定制您自己的Agent](#定制您自己的agent)
      - [内置资源](#内置资源)
        - [Agent Pool](#agent-pool)
        - [Services](#services)
        - [Example Applications](#example-applications)
  - [License](#license)
  - [贡献](#贡献)
  - [引用](#引用)

## 安装

要安装AgentScope，您需要安装Python 3.9或更高版本。

**_注意：该项目目前正在积极开发中，建议从源码安装AgentScope。_**

### 从源码安装

- 运行以下命令以编辑模式安装AgentScope。

```bash
# 从github拉取源代码
git clone https://github.com/modelscope/agentscope.git
# 以编辑模式安装包
cd AgentScope
pip install -e .
```

- 构建分布式Multi-Agent应用程序依赖于[gRPC](https://github.com/grpc/grpc)库，您可以按以下方式安装所需的依赖项。

```bash
# 在windows上
pip install -e .[distribute]
# 在mac上
pip install -e .\[distribute\]
```

### 使用pip

- 使用以下命令安装最新发布的AgentScope。

```bash
pip install agentscope
```

## 快速开始

### 基础使用

以用户和助手Agent对话的Multi-Agent应用程序为例，您需要执行以下步骤：

- [第1步：准备Model Configs](#第1步准备model-configs)

- [第2步：创建Agent](#第2步创建agent)

- [第3步：构造对话](#第3步构造对话)

#### 第1步：准备Model Configs

AgentScope支持以下模型API服务：

- OpenAI Python APIs，包括

  - OpenAI Chat, DALL-E和Embedding API

  - 兼容OpenAI的Inference库，例如[FastChat](https://github.com/lm-sys/FastChat)和[vllm](https://github.com/vllm-project/vllm)

- Post Request APIs，包括

  - [HuggingFace](https://huggingface.co/docs/api-inference/index)和[ModelScope](https://www.modelscope.cn/docs/%E9%AD%94%E6%90%ADv1.5%E7%89%88%E6%9C%AC%20Release%20Note%20(20230428)) Inference API

  - 自定义模型API

|                      | 模型类型参数 | 支持的API                                                   |
|----------------------|---------------------|----------------------------------------------------------------|
| OpenAI Chat API      | `openai`            | 标准OpenAI Chat API, FastChat和vllm                    |
| OpenAI DALL-E API    | `openai_dall_e`     | 标准DALL-E API                                            |
| OpenAI Embedding API | `openai_embedding`  | OpenAI 嵌入式API                                           |
| Post API             | `post_api`          | Huggingface/ModelScope 推理API, 以及定制化的post API  |

##### OpenAI API Configs

对于OpenAI API，您需要准备一个包含以下字段的模型配置字典：

```
{
    "config_name": "{配置名称}",                 # 用于识别配置的名称
    "model_type": "openai" | "openai_dall_e" | "openai_embedding",
    "model_name": "{模型名称，例如gpt-4}",        # openai API中的模型
    # 可选
    "api_key": "xxx",                           # OpenAI API的API密钥。如果未设置，将使用环境变量OPENAI_API_KEY。
    "organization": "xxx",                      # OpenAI API的组织。如果未设置，将使用环境变量OPENAI_ORGANIZATION。
}
```

##### Post Request API Config

对于post请求API，配置包含以下字段。

```
{
    "config_name": "{配置名称}",       # 用于识别配置的名称
    "model_type": "post_api",
    "api_url": "https://xxx",         # 目标url
    "headers": {                      # 需要的头信息
      ...
    },
}
```

为了方便开发和调试，AgentScope在[scripts](./scripts/README.md)目录下提供了丰富的脚本以快速部署模型服务。
有关模型服务的详细使用，请参阅我们的[教程](https://modelscope.github.io/agentscope/index.html#welcome-to-agentscope-tutorial-hub)和[API文档](https://modelscope.github.io/agentscope/index.html#indices-and-tables)。

#### 第2步：创建Agent

创建内置的用户和助手Agent：

```python
from agentscope.agents import DialogAgent, UserAgent
import agentscope

# 载入模型配置
agentscope.init(model_configs="./model_configs.json")

# 创建对话Agent和用户Agent
dialog_agent = DialogAgent(name="assistant",
                           model_or_config_name="your_config_name")
user_agent = UserAgent()
```

#### 第3步：构造对话

在AgentScope中，**Message**是Agent之间的桥梁，它是一个python**字典**（dict），包含两个必要字段`name`和`content`，以及一个可选字段`url`用于本地文件（图片、视频或音频）或网络链接。

```python
from agentscope.message import Msg

x = Msg(name="Alice", content="Hi!")
x = Msg("Bob", "What about this picture I took?", url="/path/to/picture.jpg")
```

使用以下代码开始两个Agent（dialog_agent和user_agent）之间的对话：

```python
x = None
while True:
  x = dialog_agent(x)
  x = user_agent(x)
  if x.content == "exit": # 用户输入"exit"退出对话
    break
```

### 进阶使用

#### **Pipeline**和**MsgHub**

为了简化Agent间通信的构建，AgentScope提供了两种语法工具：**Pipeline**和**MsgHub**。

- **Pipeline**：它允许用户轻松编写Agent间的通信。以Sequential Pipeline为例，以下两种代码等效，但是pipeline的实现方式更加简洁和优雅。

  - **不使用** pipeline的情况下，agent1、agent2和agent3顺序传递消息：

    ```python
    x1 = agent1(input_msg)
    x2 = agent2(x1)
    x3 = agent3(x2)
    ```

  - **使用** pipeline对象的情况下：

    ```python
    from agentscope.pipelines import SequentialPipeline

    pipe = SequentialPipeline([agent1, agent2, agent3])
    x3 = pipe(input_msg)
    ```

  - **使用** functional pipeline的情况下：

    ```python
    from agentscope.pipelines.functional import sequentialpipeline

    x3 = sequentialpipeline([agent1, agent2, agent3], x=input_msg)
    ```

- **MsgHub**：为了方便地实现多人对话，AgentScope提供了Message Hub。

  - **不使用** `msghub`：实现多人对话：

    ```python
    x1 = agent1(x)
    agent2.observe(x1)  # 消息x1应该广播给其他agent
    agent3.observe(x1)

    x2 = agent2(x1)
    agent1.observe(x2)
    agent3.observe(x2)
    ```

  - **使用** `msghub`：在Message Hub中，来自参与者的消息将自动广播给所有其他参与者，因此在这种情况下，Agent的调用甚至不需要明确输入和输出消息，我们需要做的就是决定发言的顺序。此外，`msghub`还支持动态控制参与者，如下所示。

    ```python
    from agentscope import msghub

    with msghub(participants=[agent1, agent2, agent3]) as hub:
        agent1() # `x = agent1(x)`也可行
        agent2()

        # 向所有参与者广播一条消息
        hub.broadcast(Msg("Host", "欢迎加入群组对话！"))

        # 动态地添加或删除参与者
        hub.delete(agent1)
        hub.add(agent4)
    ```

#### 定制您自己的Agent

要实现您自己的Agent，您需要继承`AgentBase`类并实现`reply`函数。

```python
from agentscope.agents import AgentBase

class MyAgent(AgentBase):

    def reply(self, x):

        # 在这里做一些事情，例如调用您的模型并获取原始字段作为agent的回应
        response = self.model(x).raw
        return response
```

#### 内置资源

AgentScope提供丰富的内置资源以便开发人员轻松构建自己的应用程序。更多内置Agent、Service和Example即将推出！

##### Agent Pool

- UserAgent
- DialogAgent
- DictDialogAgent
- ...

##### Services

- 网络搜索服务
- 代码执行服务
- 检索服务
- 数据库服务
- 文件服务
- ...

##### Example Applications

- 对话示例：[examples/conversation](examples/conversation/README.md)
- 狼人杀示例：[examples/werewolf](examples/werewolf/README.md)
- 分布式Agent示例：[examples/distributed](examples/distributed/README.md)
- ...

更多内置资源即将推出！

## License

AgentScope根据Apache License 2.0发布。

## 贡献

欢迎参与到AgentScope的构建中！

我们提供了一个带有额外 pre-commit 钩子以执行检查的开发者版本，与官方版本相比：

```bash
# 对于windows
pip install -e .[dev]
# 对于mac
pip install -e .\[dev\]
# 安装pre-commit钩子
pre-commit install
```

请参阅我们的[贡献指南](https://modelscope.github.io/agentscope/tutorial/contribute.html)了解更多细节。

## 引用

如果您觉得我们的工作对您的研究或应用有帮助，请引用[我们的论文](https://arxiv.org/abs/2402.14034)。

```
@article{agentscope,
  author  = {Dawei Gao and
             Zitao Li and
             Weirui Kuang and
             Xuchen Pan and
             Daoyuan Chen and
             Zhijian Ma and
             Bingchen Qian and
             Liuyi Yao and
             Lin Zhu and
             Chen Cheng and
             Hongzhu Shi and
             Yaliang Li and
             Bolin Ding and
             Jingren Zhou},
  title   = {AgentScope: A Flexible yet Robust Multi-Agent Platform},
  journal = {CoRR},
  volume  = {abs/2402.14034},
  year    = {2024},
}
```
