(208-distribute-zh)=

# 分布式运行

AgentScope 完全基于分布式设计，一个应用程序中的不同 Agent 实例可以部署在不同的机器上并行运行。本教程将介绍 AgentScope 分布式的特点和分布式部署方法。

## 设计理念

### 每个 “Agent” 都是一个“Actor”

[Actor 模式](https://en.wikipedia.org/wiki/Actor_model)是大规模分布式系统中广泛使用的编程范式，AgentScope 也是基于该范式。每个 Agent 都是一个 Actor，并通过消息与其他 Agent 交互。消息的流转暗示了 Agent 的执行顺序。每个 Agent 都有一个 `reply` 方法，它消费一条消息并生成另一条消息，生成的消息可以发送给其他 Agent。例如，下面的图表显示了多个 Agent 的工作流程。`A` ~ `F` 都是 Agent，箭头代表消息。

```{mermaid}
graph LR;
A-->B
A-->C
B-->D
C-->D
E-->F
D-->F
```

其中，`B` 和 `C` 可以在接收到来自 `A` 的消息后同时启动执行，而 `E` 可以立即运行，无需等待 `A`、`B`、`C` 和 `D`。
通过将每个 Agent 实现为一个 Actor， Agent 将自动等待其输入 Msg 准备好后开始执行 `reply` 方法，并且如果多个 Agent 的输入消息准备就绪，它们也可以同时自动执行 `reply`，这避免了复杂的并行控制。

### 集中式编写，分布式运行

在 AgentScope 中，可以在同一台或多台不同的机器上将 Agent 启动为单独的进程。但应用程序开发者不需要关心这些 Agent 在哪里运行；您只需使用面向过程式编程范式在主进程中编写应用程序代码。AgentScope 将帮助您将任务转换为分布式版本。下面是一段应用程序代码，其中 `A`、`B` 和 `C` 运行在不同的机器上。

```
x = A()
y = B(x)
z = C(x)
```

尽管这段代码看起来是完全顺序执行的，但 AgentScope 将自动检测您代码中的潜在并行性，如下面的流图所示，这意味着 `C` 将不会等待 `B` 完成就开始执行。

```{mermaid}
graph LR;
A-->B
A-->C
```

## 分布式部署

请按照以下步骤分布式部署您的应用程序。

### 转换 Agent

`AgentBase` 提供了 `to_dist` 方法将该 Agent 自身转换为分布式版本。
`to_dist` 需要几个参数。

- `host`: 运行 Agent 的机器的主机名或 IP 地址，默认为 `localhost`。
- `port`: 此 Agent 的 RPC 服务器端口，默认为 `80`。
- `launch_server`: 是否在本地启动 RPC 服务器，默认为 `True`。
- `local_mode`: 如果所有 Agent 都在同一台机器上运行，则设置为 `True`，默认为 `True`。
- `lazy_launch`:  如果设置为 `True`，则只在调用 Agent 时启动服务器。

> `to_dist` 方法基于 [gRPC](https://grpc.io/). 当设置 'launch_server' 为 `True` 时，它将启动一个 gRPC 服务器进程，并将原始 Agent 转移到新进程中运行。

### Run in multi-process mode

AgentScope 支持在多进程模式下部署，其中每个 Agent 是应用程序主进程的子进程，所有 Agent 都在同一台机器上运行。
其使用方式与单进程模式完全相同，您只需要在初始化后调用 `to_dist` 方法。

假设您有两个 class， `A` 和 `B`，它们都继承自 `AgentBase`。

```python
# 导入依赖包

a = A(
    name="A",
    ...,
).to_dist()
b = B(
    name="B",
    ...,
).to_dist()

x = None
while x is None or x.content != 'exit':
    x = a(x)
    x = b(x)
```

### 在多台机器上运行

AgentScope 也支持在多台机器上运行 Agent。在这种情况下，您需要分别启动 Agent。例如，您可以使用以下代码在 IP 地址为 `ip_a` 的机器上启动 Agent A。

```python
# 导入依赖包

server_a = RpcAgentServerLauncher(
    agent_class=A,
    agent_kwargs={
        "name": "A"
        ...
    },
    host=ip_a,
    port=12001,
)
server_a.launch()
server_a.wait_until_terminate()
```

同样，您可以在 IP 地址为 `ip_b` 的机器上启动 Agent B。
请确保两台机器可以使用 IP 地址相互访问。

```python
# 导入依赖包

a = A(
    name="A",
    ...
).to_dist(
    host=ip_a,
    port=12001,
    launch_server=False,
)
b = B(
    name="B",
    ...
).to_dist(
    host=ip_b,
    port=12002,
    launch_server=False,
)

x = None
while x is None or x.content != 'exit':
    x = a(x)
    x = b(x)
```

[[回到顶部]](#分布式运行)
