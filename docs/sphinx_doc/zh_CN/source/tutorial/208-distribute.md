(208-distribute-zh)=

# 分布式

AgentScope实现了基于Actor模式的智能体分布式部署和并行优化，并提供以下的特点：

- **自动并行优化**：运行时自动实现应用并行优化，无需额外优化成本；
- **应用编写中心化**：无需分布式背景知识，轻松编排分布式应用程序流程；
- **零成本自动迁移**：中心化的Multi-Agent应用可以轻松转化成分布式模式

本教程将详细介绍AgentScope分布式的实现原理和使用方法。

## 使用方法

AgentScope中，我们将运行应用流程的进程称为**主进程 (Main Process)**，而所有的智能体都会运行在额外的 **智能体服务器进程 (Agent Server Process)** 中。
根据主进程域智能体服务器进程之间的关系，AgentScope 为每个 Agent 提供了两种启动模式：**子进程模式 (Child)** 和 **独立进程模式 (Indpendent)**。
子进程模式中，开发者可以从主进程中启动所有的智能体服务器进程，而独立进程模式中，智能体服务器进程相对主进程来说是独立的，需要在对应的机器上启动智能体服务器进程。

上述概念有些复杂，但是不用担心，对于应用开发者而言，仅需将已有的智能体转化为对应的分布式版本，其余操作都和正常的单机版本完全一致。

### 步骤1: 转化为分布式版本

AgentScope 中所有智能体都可以通过 {func}`to_dist<agentscope.agents.AgentBase.to_dist>` 方法转化为对应的分布式版本。
但需要注意，你的智能体必须继承自 {class}`agentscope.agents.AgentBase<agentscope.agents.AgentBase>` 类，因为是 `AgentBase` 提供了 `to_dist` 方法。

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
AgentScope 会自动帮你从主进程中启动智能体服务器进程并将智能体部署到对应的子进程上。

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

#### 独立进程模式

在独立进程模式中，需要首先在目标机器上启动智能体服务器进程，启动时需要提供该服务器能够使用的模型的配置信息，以及服务器的 IP 和端口号。
例如想要将两个智能体服务进程部署在 IP 分别为 `ip_a` 和 `ip_b` 的机器上（假设这两台机器分别为`Machine1` 和 `Machine2`）。
你可以在 `Machine1` 上运行如下代码。在运行之前请确保该机器能够正确访问到应用中所使用的所有模型。具体来讲，需要将用到的所有模型的配置信息放置在 `model_config_path_a` 文件中，并检查API key 等环境变量是否正确设置，模型配置文件样例可参考 `examples/model_configs_template`。

```python
# import some packages

# register models which can be used in the server
agentscope.init(
    model_configs=model_config_path_a,
)
# Create an agent service process
server = RpcAgentServerLauncher(
    host="ip_a",
    port=12001,  # choose an available port
)

# Start the service
server.launch()
server.wait_until_terminate()
```

> 为了进一步简化使用，可以在命令行中输入如下指令来代替上述代码：
>
> ```shell
> as_server --host ip_a --port 12001  --model-config-path model_config_path_a
> ```

在 `Machine2` 上运行如下代码，这里同样要确保已经将模型配置文件放置在 `model_config_path_b` 位置并设置环境变量，从而确保运行在该机器上的 Agent 能够正常访问到模型。

```python
# import some packages

# register models which can be used in the server
agentscope.init(
    model_configs=model_config_path_b,
)
# Create an agent service process
server = RpcAgentServerLauncher(
    host="ip_b",
    port=12002, # choose an available port
)

# Start the service
server.launch()
server.wait_until_terminate()
```

> 这里也同样可以用如下指令来代替上面的代码。
>
> ```shell
> as_server --host ip_b --port 12002 --model-config-path model_config_path_b
> ```

接下来，就可以使用如下代码从主进程中连接这两个智能体服务器进程。

```python
a = AgentA(
    name="A",
    # ...
).to_dist(
    host="ip_a",
    port=12001,
)
b = AgentB(
    name="B",
    # ...
).to_dist(
    host="ip_b",
    port=12002,
)
```

上述代码将会把 `AgentA` 部署到 `Machine1` 的智能体服务器进程上，并将 `AgentB` 部署到 `Machine2` 的智能体服务器进程上。
开发者在这之后只需要用中心化的方法编排各智能体的交互逻辑即可。

#### `to_dist` 进阶用法

上面介绍的案例都是将一个已经初始化的 Agent 通过 {func}`to_dist<agentscope.agents.AgentBase.to_dist>` 方法转化为其分布式版本，相当于要执行两次初始化操作，一次在主进程中，一次在智能体进程中。如果 Agent 的初始化过程耗时较长，直接使用 `to_dist` 方法会严重影响运行效率。为此 AgentScope 也提供了在初始化 Agent 实例的同时将其转化为其分布式版本的方法，即在原 Agent 实例初始化时传入 `to_dist` 参数。

子进程模式下，只需要在 Agent 初始化函数中传入 `to_dist=True` 即可：

```python
# Child Process mode
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

独立进程模式下， 则需要将原来 `to_dist()` 函数的参数以 {class}`DistConf<agentscope.agents.DistConf>` 实例的形式传入 Agent 初始化函数的 `to_dist` 域：

```python
a = AgentA(
    name="A",
    # ...
    to_dist=DistConf(
        host="ip_a",
        port=12001,
    ),
)
b = AgentB(
    name="B",
    # ...
    to_dist=DistConf(
        host="ip_b",
        port=12002,
    ),
)
```

相较于原有的 `to_dist()` 函数调用，该方法只会在智能体进程中初始化一次 Agent，避免了重复初始化现象。

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
  - `AgentB` 使用独立进程模式部署

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
    host="ip_b",
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

同时，为了支持中心化的应用编排，AgentScope 引入了 {class}`Placeholder<agentscope.message.PlaceholderMessage>` 这一概念。
Placeholder 可以理解为消息的指针，指向消息真正产生的位置，其对外接口与传统模式中的消息完全一致，因此可以按照传统中心化的消息使用方式编排应用。
Placeholder 内部包含了该消息产生方的联络方法，可以通过网络获取到被指向消息的真正值。
每个分布式部署的 Agent 在收到其他 Agent 发来的消息时都会立即返回一个 Placeholder，从而避免阻塞请求发起方。
而请求发起方可以借助返回的 Placeholder 在真正需要消息内容时再去向原 Agent 发起请求，请求发起方甚至可以将 Placholder 发送给其他 Agent 让其他 Agent 代为获取消息内容，从而减少消息真实内容的不必要转发。

关于更加详细的技术实现方案，请参考我们的[论文](https://arxiv.org/abs/2402.14034)。

#### Agent Server

Agent Server 也就是智能体服务器。在 AgentScope 中，Agent Server 提供了一个让不同 Agent 实例运行的平台。多个不同类型的 Agent 可以运行在同一个 Agent Server 中并保持独立的记忆以及其他本地状态信息，但是他们将共享同一份计算资源。

在安装 AgentScope 的分布式版本后就可以通过 `as_server` 命令来启动 Agent Server，具体的启动参数在 {func}`as_server<agentscope.server.launcher.as_server>` 函数文档中可以找到。

只要没有对代码进行修改，一个已经启动的 Agent Server 可以为多个主流程提供服务。
这意味着在运行多个应用时，只需要在第一次运行前启动 Agent Server，后续这些 Agent Server 进程就可以持续复用。

[[回到顶部]](#208-distribute-zh)
