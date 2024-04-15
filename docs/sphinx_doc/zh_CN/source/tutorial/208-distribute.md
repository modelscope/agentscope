(208-distribute-zh)=

# 分布式

AgentScope实现了基于Actor模式的智能体分布式部署和并行优化，并提供以下的特点：

- **自动并行优化**：运行时自动实现应用并行优化，无需额外优化成本；
- **应用编写中心化**：无需分布式背景知识，轻松编排分布式应用程序流程；
- **零成本自动迁移**：中心化的Multi-Agent应用可以轻松转化成分布式模式

本教程将详细介绍AgentScope分布式的实现原理和使用方法。

## 使用方法

AgentScope中，我们将运行应用流程的进程称为“主进程”，而所有的智能体都会运行在“智能体进程”中。
子进程模式（Subprocess）和独立模式（Standalone）。
子进程模式中，开发者可以从主进程中启动所有的智能体进程，而独立模式中，智能体进程相对主进程来说是独立的，需要在对应的机器上启动智能体的服务。

上述概念有些复杂，但是不用担心，对于应用开发者而言，仅需将已有的智能体转化为对应的分布式版本，其余操作都和正常的单机版本完全一致。

### 步骤1: 转化为分布式版本

AgentScope 中所有智能体都可以通过 `to_dist` 方法转化为对应的分布式版本。
但需要注意，你的智能体必须继承自 `agentscope.agents.AgentBase` 类，因为是 `AgentBase` 提供了 `to_dist` 方法。

假设有两个智能体类`AgentA`和`AgentB`，它们都继承自 `AgentBase`。

```python
a = AgentA(
    name="A"
    # ...
)
b = AgentB(
    name="B"
    # ...
)
```

接下来我们将介绍如何将智能体转化到两种分布式模式。

#### 子进程模式

要使用该模式，你只需要调用各智能体的 `to_dist()` 方法，并且不需要提供任何参数。
AgentScope 会自动帮你从主进程中启动智能体子进程并将智能体部署到对应的子进程上。

```python
# Subprocess mode
a = AgentA(
    name="A"
    # ...
).to_dist()
b = AgentB(
    name="B"
    # ...
).to_dist()
```

#### 独立模式

在独立模式中，需要首先在目标机器上启动智能体服务进程。
例如想要将两个智能体服务进程部署在 IP 分别为 `a.b.c.d` 和 `e.f.g.h` 的机器上（假设这两台机器分别为`Machine1` 和 `Machine2`）。
你可以先在 `Machine1` 上运行如下代码：

```python
# import some packages

agentscope.init(
    ...
)
# Create an agent service process
server = RpcAgentServerLauncher(
    host="a.b.c.d",
    port=12001,  # choose an available port
)

# Start the service
server.launch()
server.wait_until_terminate()
```

之后在 `Machine2` 上运行如下代码：

```python
# import some packages

agentscope.init(
    ...
)
# Create an agent service process
server = RpcAgentServerLauncher(
    host="e.f.g.h",
    port=12002, # choose an available port
)

# Start the service
server.launch()
server.wait_until_terminate()
```

接下来，就可以使用如下代码从主进程中连接这两个智能体服务进程。

```python
a = AgentA(
    name="A",
    # ...
).to_dist(
    host="a.b.c.d",
    port=12001,
)
b = AgentB(
    name="B",
    # ...
).to_dist(
    host="e.f.g.h",
    port=12002,
)
```

上述代码将会把 `AgentA` 部署到 `Machine1` 的智能体服务进程上，并将 `AgentB` 部署到 `Machine2` 的智能体服务进程上。
开发者在这之后只需要用中心化的方法编排各智能体的交互逻辑即可。

#### `to_dist` 进阶用法

上面介绍的案例都是将一个已经初始化的 Agent 通过 `to_dist` 方法转化为其分布式版本。对于那些初始化耗时的 Agent 上述方法相当于要执行两次初始化操作，如果直接使用 `to_dist` 方法会严重影响运行效率。为此 AgentScope 也提供了在初始化 Agent 实例的同时将其转化为其分布式版本的方法，即在原 Agent 实例初始化时传入 `to_dist=True` 以及其他必要参数。

子进程模式下 Agent 的初始化可简化为如下代码：

```python
# Subprocess mode
a = AgentA(
    name="A",
    # ...
    to_dist=True
)
b = AgentB(
    name="B",
    # ...
    to_dist=True
)
```

独立模式下 Agent 的初始化可简化为如下代码：

```python
a = AgentA(
    name="A",
    # ...
    to_dist=True,
    host="a.b.c.d",
    port=12001,
)
b = AgentB(
    name="B",
    # ...
    to_dist=True,
    host="e.f.g.h",
    port=12002,
)
```

相较于原有的 `to_dist()` 函数调用，该方法只需要在原 Agent 的初始化函数中传入 `to_dist=True`，并将其他原来在 `to_dist()` 方法中传入的参数以键值对的形式传入 Agent 的初始化函数即可。

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

- 智能体分布式部署
  - `AgentA` 使用子进程模式部署
  - `AgentB` 使用独立模式部署

```python
# 创建智能体对象
a = AgentA(
    name="A"
    # ...
).to_dist()

b = AgentB(
    name="B",
    # ...
).to_dist(
    host="e.f.g.h",
    port=12002,
)

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

#### Agent Server

Agent Server 也就是智能体服务。在 AgentScope 中，Agent Server 提供了一个让不同 Agent 实例运行的平台。多个不同类型的 Agent 可以运行在同一个 Agent Server 中并保持独立的记忆以及其他本地状态信息，但是他们将共享同一份计算资源。
只要没有对代码进行修改，一个已经启动的 Agent Server 可以为多个主流程提供服务。
这意味着在运行多个应用时，只需要在第一次运行前启动 Agent Server，后续这些 Agent Server 进程就可以持续复用。

[[回到顶部]](#208-distribute-zh)
