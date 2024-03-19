(208-distribute-zh)=

# 分布式

AgentScope实现了基于Actor模式的智能体分布式部署和并行优化，并提供以下的特点：

- **自动并行优化**：运行时自动实现应用并行优化，无需额外优化成本；
- **应用编写中心化**：无需分布式背景知识，轻松编排分布式应用程序流程；
- **零成本自动迁移**：中心化的Multi-Agent应用可以轻松转化成分布式模式

本教程将详细介绍AgentScope分布式的实现原理和使用方法。

## 使用方法

AgentScope中，我们将运行应用流程的进程称为“主进程”，而所有的智能体都会运行在独立的进程当中。
根据主进程和智能体进程之间关系的不同，AgentScope支持两种分布式模式：主从模式（Master-Slave）和对等模式（Peer-to-Peer，P2P）。
主从模式中，开发者可以从主进程中启动所有的智能体进程，而对等模式中，智能体进程相对主进程来说是独立的，需要在对应的机器上启动智能体的服务。

上述概念有些复杂，但是不用担心，对于应用开发者而言，它们仅仅在创建智能体阶段有微小的差别。下面我们介绍如何创建分布式智能体。

### 步骤1: 创建分布式智能体

首先，开发者的智能体必须继承`agentscope.agents.AgentBase`类，`AgentBase`提供了`to_dist`方法将该Agent转化为其分布式版本。`to_dist`主要依靠以下的参数实现智能体分布式部署：

- `host`: 用于部署智能体的机器IP地址，默认为`localhost`。
- `port`: 智能体的RPC服务器端口，默认为`80`。
- `launch_server`: 是否在本地启动RPC服务器，默认为`True`。

假设有两个智能体类`AgentA`和`AgentB`，它们都继承自 `AgentBase`。

#### 主从模式

主从模式中，由于所有智能体进程依赖于主进程，因此所有进程实际运行在一台机器上。
我们可以在主进程中启动所有智能体进程，即默认参数`launch_server=True`和`host="localhost"`，同时我们可以省略`port`参数，AgentScope将会为智能体进程自动寻找空闲的本地端口。

```python
a = AgentA(
    name="A"
    # ...
).to_dist()
```

#### 对等模式

对等模式中，我们需要首先在目标机器上启动对应智能体的服务，例如将`AgentA`的实例部署在IP为`a.b.c.d`的机器上，其对应的端口为12001。在这台目标机器上运行以下代码：

```python
from agentscope.agents import RpcAgentServerLauncher

# 创建智能体服务进程
server_a = RpcAgentServerLauncher(
    agent_class=AgentA,
    agent_kwargs={
        "name": "A"
        ...
    },
    host="a.b.c.d",
    port=12001,
)
# 启动服务
server_a.launch()
server_a.wait_until_terminate()
```

然后，我们可以在主进程当中用以下的代码连接智能体服务，此时主进程中创建的对象`a`可以当做智能体的本地代理，允许开发者可以在主进程中采取中心化的方式编写应用流程。

```python
a = AgentA(
    name="A",
    ...
).to_dist(
    host="a.b.c.d",
    port=12001,
    launch_server=False,
)
```

### 步骤2: 编排分布式应用流程

在AgentScope中，分布式应用流程的编排和非分布式的程序完全一致，开发者可以用中心化的方式编写全部应用流程。
同时，AgentScope允许本地和分布式部署的智能体混合使用，开发者不用特意区分哪些智能体是本地的，哪些是分布式部署的。

以下是不同模式下实现两个智能体之间进行对话的全部代码，对比可见，AgentScope支持零代价将分布式应用流程从中心化向分布式迁移。

- 智能体全部中心化：

```python
# 创建智能体对象
a = AgentA(
    name="A",
    # ...
)

b = AgentB(
    name="B",
    # ...
)

# 应用流程编排
x = None
while x is None or x.content == "exit":
    x = a(x)
    x = b(x)
```

- 智能体分布式部署（主从模式下）：

```python
# 创建智能体对象
a = AgentA(
    name="A"
    # ...
).to_dist()

b = AgentB(
    name="B",
    # ...
).to_dist()

# 应用流程编排
x = None
while x is None or x.content == "exit":
    x = a(x)
    x = b(x)
```

### 实现原理

#### Actor模式

[Actor模式](https://en.wikipedia.org/wiki/Actor_model)是大规模分布式系统中广泛使用的编程范式，同时也被应用于AgentScope平台的分布式设计中。
在Actor模型中，一个actor是一个实体，它封装了自己的状态，并且仅通过消息传递与其他actor通信。

在AgentScope的分布式模式中，每个Agent都是一个Actor，并通过消息与其他Agent交互。消息的流转暗示了Agent的执行顺序。每个Agent都有一个`reply`方法，它消费一条消息并生成另一条消息，生成的消息可以发送给其他 Agent。例如，下面的图表显示了多个Agent的工作流程。`A`~`F`都是Agent，箭头代表消息。

```{mermaid}
graph LR;
A-->B
A-->C
B-->D
C-->D
E-->F
D-->F
```

其中，`B`和`C`可以在接收到来自`A`的消息后同时启动执行，而`E`可以立即运行，无需等待`A`、`B`、`C`和`D`。
通过将每个Agent实现为一个Actor， Agent将自动等待其输入Msg准备好后开始执行`reply`方法，并且如果多个 Agent 的输入消息准备就绪，它们也可以同时自动执行`reply`，这避免了复杂的并行控制。

#### PlaceHolder

同时，为了支持中心化的应用编排，AgentScope引入了Placeholder这一概念。Placeholder是一个特殊的消息，它包含了产生该Placeholder的智能体的地址和端口号，用于表示Agent的输入消息还未准备好。
当Agent的输入消息准备好后，Placeholder会被替换为真实的消息，然后运行实际的`reply`方法

关于更加详细的技术实现方案，请参考我们的[论文](https://arxiv.org/abs/2402.14034)。

[[回到顶部]](#208-distribute-zh)
