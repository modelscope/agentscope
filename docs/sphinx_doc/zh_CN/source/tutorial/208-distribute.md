(208-distribute-zh)=

# 分布式

为了提供更好的性能以及支持更多的 Agent 同时运行，AgentScope 实现了基于 Actor 范式的 并行/分布式模式（后续简称为分布式模式）。该模式相比传统单进程模式具有以下特点：

- **高性能**: 同一应用中的不同 Agent 以及其他服务可以运行不同进程甚至不同机器上，充分利用计算资源释放性能。
- **自动并行化**: 基于 Actor 模式，每个 Agent都具有独立的状态，在编写应用时无需考虑调用顺序、资源竞争等问题，自动实现应用并行化。
- **零迁移成本**: 代码与单机模式完全兼容，单机模式可运行的应用可以零成本直接迁移至并行/分布式模式。

本节将详细介绍 AgentScope 分布式的使用方法并阐述其原理。

(basic_usage-zh)=

## 基础用法

分布式模式相比传统模式对运行代码几乎没有任何修改，仅需要在 Agent 初始化阶段调用 {func}`to_dist<agentscope.rpc.RpcMeta.to_dist>` 函数即可。

```python
# import some packages

# init agentscope

# 传统模式下的初始化
# agent = Agent(...)

# 分布式模式下的初始化
agent = Agent(...).to_dist()

x = Msg(...)
y = agent(x)
```

本节接下来将以一个网页检索的案例来展示具体如何使用 AgentScope 的分布式模式。
为了突出 AgentScope 分布式模式所能带来的加速效果，这里使用了一个简单的自定义 `WebAgent`。
该 Agent 会用 sleep 5 秒来模拟爬取网页并从中寻找问题答案的过程，样例中共有 5 个 Agent，每个 Agent 都会爬取一个网页并寻找问题答案。

传统模式与分布式模式的区别仅在与初始化阶段，即 `init_without_dist` 和 `init_with_dist`。
`init_with_dist` 函数相较于 `init_without_dist` 的唯一区别在于额外调用了 `to_dist` 函数。
在初始化完成后具体运行部分的代码完全相同，都是 `run` 函数，但两种模式的运行耗时却有较大差异。

```python
# 请不要使用 jupyter notebook 运行该代码
# 请将代码拷贝到 `dist_main.py` 文件后使用 `python dist_main.py` 命令运行该代码
# 运行该代码前请先安装 agentscope 的分布式版本
# pip install agentscope[distribute]

import time
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg

class WebAgent(AgentBase):

    def __init__(self, name):
        super().__init__(name)

    def get_answer(self, url: str, query: str):
        """模拟爬取网页并从中寻找问题答案"""
        time.sleep(5)
        return f"Answer from {self.name}"

    def reply(self, x: dict = None) -> dict:
        return Msg(
            name=self.name,
            role="assistant",
            content=self.get_answer(x.content["url"], x.content["query"])
        )


QUERY = "example query"
URLS = ["page_1", "page_2", "page_3", "page_4", "page_5"]

def init_without_dist():
    return [WebAgent(f"W{i}") for i in range(len(URLS))]


def init_with_dist():
    return [WebAgent(f"W{i}").to_dist() for i in range(len(URLS))]


def run(agents):
    start = time.time()
    results = []
    for i, url in enumerate(URLS):
        results.append(agents[i].reply(
            Msg(
                name="system",
                role="system",
                content={
                    "url": url,
                    "query": QUERY
                }
            )
        ))
    for result in results:
        print(result.content)
    end = time.time()
    return end - start


if __name__ == "__main__":
    agentscope.init()
    start = time.time()
    simple_agents = init_without_dist()
    dist_agents = init_with_dist()
    end = time.time()
    print(f"初始化的耗时：{end - start}")
    print(f"不使用分布式模式的耗时：{run(simple_agents)}")
    print(f"使用分布式模式的耗时：{run(dist_agents)}")
```

上述代码的输出样例如下：

```text
初始化的耗时：12.944042921066284
[W0] Answer from page_1
[W1] Answer from page_2
[W2] Answer from page_3
[W3] Answer from page_4
[W4] Answer from page_5
不使用分布式模式的耗时：25.022241830825806
[W0] Answer from page_1
[W1] Answer from page_2
[W2] Answer from page_3
[W3] Answer from page_4
[W4] Answer from page_5
使用分布式模式的耗时：5.021369934082031
```

从上述输出中可以观察到，在采用分布式模式后，运行速度有明显的提升（从 25 s 降低到 5 s）。
上述样例也是 AgentScope 分布式模式最常见的使用用法，在不追求极致性能的性能且 Agent 数量相对较少（例如不超过 10 个）的情况下，建议采用直接采用上述方法。
而如果需要进一步优化性能，则需要对 AgentScope 分布式模式有更加深入的了解，下面的章节我们将具体介绍 AgentScope 分布式模式中的进阶使用方法。

## 进阶用法

本节将介绍 AgentScope 分布式模式的进阶使用方法，以进一步提升运行效率。在介绍进阶用法之前，我们需要先对 AgentScope 分布式模式的基本概念有一些初步认识。

### 基本概念

- **主进程 (Main Process)**: AgentScope 应用程序所在的进程被称为主进程。例如上一节例子中的 `run` 函数就是在主进程中运行的。每个 AgentScope 应用中只会有一个主进程。
- **智能体服务器进程 (Agent Server Process)**: AgentScope 智能体服务器进程是分布式模式下 Agent 所运行的进程。例如上一节的例子中 `dist_agents` 中的所有 Agent 的本体实际上都运行于智能体服务器进程中。AgentScope 智能体服务器进程可以存在多个。智能体服务器进程可以运行在任意网络可达的机器上，并且每个智能体服务器进程中都可以同时运行多个 Agent。

- **子进程模式 (Child Mode)**: 在子进程模式下，智能体服务器进程由主进程启动的子进程。例如上一节的例子中，`dist_agents` 中的每个 Agent 实际上都是主进程的子进程。该模式是 AgentScope 分布式的默认运行模式，即直接调用 `to_dist` 函数不给定任何参数时会默认使用该模式，[基础用法](#basic_usage-zh)部分采用的就是这种模式。
- **独立进程模式 (Independent Mode)**: 在独立进程模式下，智能体进程相对主进程来说是独立的，需要预先在机器上启动智能体进程，并向 `to_dist` 函数传入一些特定的参数。如果需要实现 Agent 跨机器部署，必须使用该模式，另外如果对性能要求较高或是 Agent 数量较多也建议使用该模式。

### 使用独立进程模式

与子进程模式相比，独立进程模式能够避免子进程初始化的开销，从而消除运行初期的延迟，对于 Agent 数量较多的场景能够有效提升运行效率。

独立进程模式下，需要在机器上提前启动智能体服务器进程，并且向 `to_dist` 函数传入需要连接的智能体服务进程的 `host` 以及 `port`。
这里我们依旧使用基础用法部分的案例来演示，假设[基础用法](#basic_usage-zh)部分的代码文件为 `dist_main.py`，需要将如下代码保存为 `dist_server.py`。

```python
# 请不要使用 jupyter notebook 运行该代码
# 请将代码拷贝到 `dist_server.py` 文件后使用 `python dist_server.py` 命令运行该代码, 目录结构如下：
# your_project_dir
# ├── dist_main.py
# └── dist_server.py
# 运行该代码前请先安装 agentscope 的分布式版本
# pip install agentscope[distribute]

import agentscope
from agentscope.server import RpcAgentServerLauncher
from dist_main import WebAgent


if __name__ == "__main__":
    agentscope.init(
        # model_configs=...  # 模型配置，如果不需要模型，可以不设置该参数
    )
    assistant_server_launcher = RpcAgentServerLauncher(
        host="localhost",
        port=12345,
        custom_agent_classes=[WebAgent],
    )
    assistant_server_launcher.launch(in_subprocess=False)
    assistant_server_launcher.wait_until_terminate()
```

上述代码中，我们通过 `RpcAgentServerLauncher` 启动了一个智能体服务器进程，需要注意的是由于 `WebAgent` 不是 AgentScope 自带的 Agent 实现，需要将 `WebAgent` 添加到 `custom_agent_classes` ，才能在智能体服务器进程中创建该类型的 Agent。另外如果智能体服务器进程中需要使用模型 API，则需要在 `agentscope.init` 中配置对应的模型参数。

同时还需要将 `dist_main.py` 中的 `init_with_dist` 更新为下面的代码：

```python
def init_with_dist():
    return [WebAgent(f"W{i}").to_dist(host="localhost", port=12345) for i in range(len(URLS))]
```

这里新版本的 `init_with_dist` 相比原版本新增了 `host` 与 `port` 两个参数，用于连接智能体服务器进程。

在代码修改完成后，先在一个命令行窗口中运行 `dist_server.py` 文件，等待启动成功后在另一个命令行窗口运行 `dist_main.py` 文件，运行的时候会看到如下输出：

```text
初始化的耗时：0.005397319793701172
[W0] Answer from page_1
[W1] Answer from page_2
[W2] Answer from page_3
[W3] Answer from page_4
[W4] Answer from page_5
不使用分布式模式的耗时：25.023009061813354
[W0] Answer from page_1
[W1] Answer from page_2
[W2] Answer from page_3
[W3] Answer from page_4
[W4] Answer from page_5
使用分布式模式的耗时：5.021481990814209
```

此时的 `dist_main.py` 初始化的耗时将会明显减少，例如这里的耗时仅为 0.005 s。

### 避免重复初始化

上面的代码中都是在一个已经初始化完成的 Agent 上调用 `to_dist` 函数。
`to_dist` 本质上是将原 Agent 克隆到智能体服务器进程中，并在主进程中保留一个 {class}`RpcObject<agentscope.rpc.RpcObject>` 作为原 Agent 的代理，对该 `RpcObject`的调用都会转发到智能体服务器进程中的对应 Agent 上。

这样的流程存在一个潜在问题，即原 Agent 被初始化了两次，一次是在主进程中，一次是在智能体服务器进程中，并且这两次初始化是依次执行的，无法通过并行加速。对于初始化成本比较低的 Agent，直接调用 `to_dist` 函数不会对性能产生明显影响，但是对于初始化成本较高的 Agent，则需要尽量避免重复初始化行为，为此 AgentScope 分布式模式提供了另一种分布式模式的初始化方法，即直接在任意 Agent 的初始化函数内部传入 `to_dist` 参数，例如下面的代码就是对 `dist_main.py` 的`init_with_dist` 函数的修改。

- 对于子进程模式，只需要在初始化函数中传入 `to_dist=True` 即可。

    ```python
    def init_with_dist():
        return [WebAgent(f"W{i}", to_dist=True) for i in range(len(URLS))]
    ```

- 对于独立进程模式，则需要将原来传入`to_dist`函数的参数以字典的形式传入到 `to_dist` 域中。

    ```python
    def init_with_dist():
        return [WebAgent(f"W{i}", to_dist={"host": "localhost", "port": "12345"}) for i in range(len(URLS))]
    ```

```{note}
一些 IDE 的自动补全功能可能提示 `to_dist` 参数不存在，但实际运行时并不会报错。
另外，如果已经在初始化参数中传入了 `to_dist`，则不能再调用 `to_dist` 方法。
```

## 开发者指南

```{note}
本节主要面向基于 AgentScope 分布式模式开发新功能的开发者，需要开发者有一定的分布式编程基础，对进程、线程、同步、异步、gRPC、Python 元类以及GIL等概念有一定的理解。但即使没有上述基础，通过阅读本节也能学到 AgentScope 分布式模式的基本原理以及一些高级用法。
```

AgentScope 分布式模式的主要逻辑是:

**将原本运行在任意 Python 进程中的对象通过 `to_dist` 函数或是初始化参数转移到 RPC 服务器中运行，并在原进程中保留一个 `RpcObject` 作为代理，任何 `RpcObject` 上的函数调用或是属性访问都会转发到 RPC 服务器中的对象上，并且在调用函数时可以自行决定是使用同步调用还是异步调用。**

下图展示了`to_dist`初始化、同步函数调用以及异步函数调用的交互流程：

```{mermaid}
sequenceDiagram
    User -->> Process: initialize
    Process -->> RPC Server: to_dist
    User -->> Process: sync function call
    Process -->> RPC Server: sync function call
    RPC Server -->> RPC Server: calculate result
    RPC Server -->> Process: sync result
    Process -->> User: sync result
    User -->> Process: async function call
    Process -->> RPC Server: async function call
    RPC Server -->> RPC Server: calculate result
    User -->> Process: get async result
    Process -->> RPC Server: get async result
    RPC Server -->> Process: async result
    Process -->> User: async result
```

从上图可以观察到 AgentScope 分布式模式本质是一个 Client-Server 架构，用户编写的智能体应用（Process）作为Client 端，而智能体服务器进程（RPC Server）作为 Server 端。分布式模式下 Client 端将本地的智能体发送到 Server 端运行，并将本地的函数调用以及属性访问转发到 Server 端，而 Server 端则负责接收 Client 端发送的对象，并接收 Client 端发来的各种调用请求。

```{note}
AgentScope 分布式模式中 Client 与 Server 通信基于 gRPC 实现，对发送消息的大小有严格的限制，默认情况下单条消息不能超过 32 MB。可以通过修改 `src/agentscope/constants.py` 中的 `_DEFAULT_RPC_OPTIONS` 参数来进一步扩大该值。
```

接下来将分别介绍 Client 端以及 Server 端的实现。

### Client 端

Client 主要包含 `RpcMeta`、`RpcObject` 两个主要类，其中 `RpcMeta` 负责将本地对象发送到 Server 端运行，而 `RpcObject` 则负责后续的各种请求调用的转发。

#### `RpcMeta`

{class}`RpcMeta<agentscope.rpc.RpcMeta>` 类是一个元类(Meta class)，会自动向继承自己的子类添加 `to_dist` 方法以及 `to_dist` 初始化参数 (因此 IDE 可能会提示 `to_dist` 参数不存在，但实际运行时并不会报错)，其实现位于 `src/agentscope/rpc/rpc_meta.py`。

在一个已经初始化完成的对象上调用 `to_dist` 方法会将原对象的初始化参数打包发送到 智能体服务器进程 中，并在智能体服务器进程中重新初始化该对象，而在主进程中会返回一个 `RpcObject` 替代原有的对象。

由于是使用初始化参数来重建原有对象，无法维持创建后的状态变化，因此建议在初始化的同时立即调用 `to_dist` 方法，或者直接在原对象的初始化函数中传入 `to_dist` 参数。

由于 `to_dist` 是 `RpcMeta` 自动向子类添加的方法，因此不仅是 Agent 类，任何继承自 `RpcMeta` 的类都可以使用 `to_dist` 方法。

`RpcMeta` 除了提供 `to_dist` 方法外还会记录原对象上能够被调用的方法以及属性，以方便在 `RpcObject` 中调用。默认情况下只会记录原对象上的公有方法，并且使用同步调用 (调用时会阻塞调用发起方，直到原对象上的方法执行完毕)。如果需要使用异步调用需要在方法声明上添加 `async_func` 装饰器。

#### `async_func` 和 `AsyncResult`

{func}`async_func<agentscope.rpc.async_func>` 装饰器的实现位于 `src/agentscope/rpc/rpc_meta.py`。`AgentBase` 及其所有子类的 `__call__` 以及 `reply` 方法都被标记为了 `async_func` 以避免阻塞。

与 `async_func` 相对的还有 {func}`sync_func<agentscope.rpc.sync_func>` 装饰器，用于标识同步方法。但由于同步方法为默认情况，因此一般不需要显式标注。

如下是一个简单的示例，这里声明了一个 `Example` 类，其中 `sync_method` 是同步方法，`async_method_basic` 以及 `async_method_complex` 被标记为了异步方法，`_protected_method` 是私有方法。

```python
import time
from agentscope.rpc import RpcMeta, async_func


class Example(metaclass=RpcMeta):

    # @sync_func  # 默认即为 sync_func，可以不添加
    def sync_method(self) -> str:
        # 同步方法，调用者会被阻塞 1 s
        time.sleep(1)
        return "sync"

    @async_func
    def async_method_basic(self) -> str:
        # 异步方法，调用者不会被阻塞，可以继续执行直到尝试获取结果
        time.sleep(1)
        # 返回一个基本类型
        return "async"

    @async_func
    def async_method_composite(self) -> dict:
        # 异步方法
        time.sleep(1)
        # 返回一个字典
        return {"a": 1, "b": 2, "c": "hello world",}

    def _protected_method(self) -> str:
        # 不是公有方法，rpc object 无法调用该方法
        time.sleep(1)
        return "protected"


if __name__ == "__main__":
    example = Example(to_dist=True)
    # 访问 protected 方法会引发未定义行为，请避免使用
    # protected_result = example._protected_method()
    t1 = time.time()
    sync_result = example.sync_method()
    assert sync_result == "sync"
    t2 = time.time()
    print(f"Sync func cost: {t2 - t1} s")
    t3 = time.time()
    async_basic = example.async_method_basic()
    async_composite = example.async_method_composite()
    t4 = time.time()
    print(f"Async func cost: {t4 - t3} s")
    # 基本类型需要在返回值上调用 result 方法获取异步执行结果
    assert async_basic.result() == "async"
    # 复合类型在访问所需要的域时自动更新异步执行结果
    assert async_composite["a"] == 1
    assert async_composite["b"] == 2
    assert async_composite["c"] == "hello world"
```

上述代码的运行结果样例如下，可以观察到调用 `async_method` 的耗时比 `sync_method` 短很多，这是因为 `async_method` 是异步方法，不会阻塞调用发起方，而 `sync_method` 是同步方法，因此会阻塞调用发起方。

```text
Sync func cost: 1.0073761940002441 s
Async func cost: 0.0003597736358642578 s
```

上述代码中 `async_method_basic` 以及 `async_method_complex` 返回的是 {class}`AsyncResult<agentscope.rpc.AsyncResult>` 对象，该对象可以通过 `result` 方法获取异步执行结果。为了让异步与同步调用的接口尽可能统一，如果 `AsyncResult` 所代表的结果是复合类型，就不再需要手动调用 `result` 方法，在访问内部属性时会自动调用 `result` 更新执行结果 (如上述代码中 `async_composite` 所示)。

#### `RpcObject`

{class}`RpcObject<agentscope.rpc.RpcObject>` 的实现位于 `src/agentscope/rpc/rpc_object.py` 中。
`RpcObject` 是一个代理，其内部并不包含原对象的任何属性值或是方法，只记录了原对象所在的智能体服务器的地址以及该对象的 `id`，通过这些参数，`RpcObject` 可以通过网络连接原对象，从而实现对原对象的调用。

当用户调用 `RpcObject` 上的方法或访问属性时，`RpcObject` 会通过 `__getattr__` 方法将请求转发到位于智能体服务器进程的原对象上。对于调用同步方法 (`@sync_func`) 或是访问属性值的情况，`RpcObject` 会阻塞调用发起方，直到原对象上的方法执行完毕，并返回执行结果。而异步方法 (`@async_func`) 则会立即返回一个 {class}`AsyncResult<agentscope.rpc.AsyncResult>` 对象，如果主进程不去访问该对象的具体值就可以无阻塞地继续运行，而如果需要获取执行结果，则需要调用 `AsyncResult` 对象上的 `result` 方法，如果此时结果还没有返回，`result` 方法会阻塞调用发起方，直到结果返回。

```{note}
`RpcObject` 在初始化时如果发现没有提供 `host` 和 `port` 参数 (即子进程模式)，就会去启动一个新的智能体服务器进程，并在该进程上重新创建原对象，而启动新的智能体服务器进程相对缓慢，这也是导致子进程模式初始化时间较长的主要原因。
而如果提供了 `host` 和 `port` 参数 (即独立进程模式)，`RpcObject` 就会直接连接该服务器并重新创建原对象，避免了启动新进程的开销。
```

### Server 端

Server 端主要基于 gRPC 实现，主要包含 `AgentServerServicer` 和 `RpcAgentServerLauncher` 这两个类。

#### `AgentServerLauncher`

`AgentServerLauncher` 的实现位于 `src/agentscope/server/launcher.py`，用于启动 gRPC Server 进程。
具体来说，为了保证启动的 Server 进程中能够正确地重新初始化 Client 端发来的对象并正确调用模型API服务，需要在启动 Server 时注册在运行中可能用到的所有 `RpcMeta` 的子类，并且正确设置模型配置。具体来说有两种启动方法，分别是通过代码启动，和通过命令行指令启动。

- 通过代码启动的具体方法如下，需要指定 `host` 和 `port`，以及 `custom_agent_classes`，并且需要在调用 `agentscope.init` 时传入需要使用的模型配置。这里假设有 `AgentA`，`AgentB`，`AgentC` 这三个自定义类需要被注册，并且 `AgentA`，`AgentB`，`AgentC` 这三个类都位于 `myagents.py` 文件中且都是 `AgentBase` 的子类。

    ```python
    import agentscope
    from agentscope.server import RpcAgentServerLauncher
    from myagents import AgentA, AgentB, AgentC


    MODEL_CONFIGS = {}

    HOST = "localhost"
    PORT = 12345
    CUSTOM_CLASSES = [AgentA, AgentB, AgentC]

    if __name__ == "__main__":
        agentscope.init(
            model_configs=MODEL_CONFIGS,
        )
        launcher = RpcAgentServerLauncher(
            host=HOST,
            port=PORT,
            custom_agent_classes=CUSTOM_CLASSES,
        )
        launcher.launch(in_subprocess=False)
        launcher.wait_until_terminate()
    ```

- 通过命令行启动的具体方法如下，除了需要指定 `host` 和 `port` 外，还需要指定 `model_config_path` 和 `agent_dir`，分别对应模型配置文件路径和自定义 Agent 类所在的目录。在安装 `agentscope` 时默认会安装 `as_server` 指令，所以可以直接在命令行中使用该指令。

    ```shell
    as_server start --host localhost --port 12345 --model-config-path model_config_path  --agent-dir parent_dir_of_myagents.py
    ```

```{warning}
`AgentServerLauncher` 会加载并执行自定义的 Python 对象，在使用前请仔细检查被加载的对象，如果其中包含恶意代码可能会对系统造成严重损害。
`AgentServerLauncher` 类还存在一个 `local_mode` 参数用于表示是否只允许本地访问，默认为 `True`，如果需要允许其他机器访问，则需要设置为 `False`。为了避免网络攻击，建议仅在可信的网络环境下使用。
```

#### `AgentServerServicer`

`AgentServerServicer` 的实现位于 `src/agentscope/server/servicer.py`，是 gRPC 服务的实现类，负责具体接收并处理 Client 端发来的各种请求。

其中的 `create_agent` 方法会在 Client 端对某个 `RpcMeta` 的子类对象使用 `to_dist` 时被调用，并在 server 内部重新创建原对象，并以 `id` 为键将对象保存在 `agent_pool` 域中。

而 `call_agent_func` 方法会在 Client 端调用 `RpcObject` 对象上的方法或属性时被调用，输入参数中包含了被调用对象的 `id` 以及被调用方法的名称，具体的调用流程有一定差异。对于同步方法以及属性访问，`call_agent_func` 会直接从 `agent_pool` 取出对象并调用对应方法或属性，并在返回结果前阻塞调用发起方。对于异步方法，`call_agent_func` 会将输入参数打包放入任务队列中，并立即返回该任务的 `task_id` 从而避免阻塞调用发起方。

`AgentServerServicer` 内部包含了一个执行器池 (`executor`) 用于自动执行任务队列中提交的任务 (`_process_task`)，并执行将结果放入 `result_pool` 中，`AsyncResult` 的 `result` 方法会尝试从 `result_pool` 中取出对应任务的结果，如果任务结果不存在则会阻塞调用发起方，直到结果返回。

##### `executor`

executor 是一个线程池 (`concurrent.futures.ThreadPoolExecutor`)，其中的线程数量由 `capacity` 参数决定，`capacity` 的设置对运行效率的影响巨大，需要根据具体任务来针对性设置。
为了让 Server 中的各个 Agent 能够并发执行，最好保证 `capacity` 大于 `AgentServerServicer` 中同时运行的 Agent 的数量，否则可能会导致运行时间成倍增加，甚至在一些特殊场景 (多个 agent 之间进行递归调用) 中出现死锁现象。

`capacity` 参数可以在 `as_server` 命令中通过 `--capacity` 指定，或是直接在 `RpcAgentServerLauncher` 初始化时指定。

```python
# ...
launcher = RpcAgentServerLauncher(
    host="localhost",
    port=12345,
    custom_agent_classes=[],
    capacity=10,
)
```

```shell
as_server start --host localhost --port 12345 --model-config-path model_config_path  --agent-dir parent_dir_of_myagents --capacity 10
```

##### `result_pool`

`ResultPool` 的实现位于 `src/agentscope/server/async_result_pool.py`，用于管理异步方法的执行结果，目前有两种实现分别为 `local` 和 `redis`。其中 `local` 基于 Python 的字典类型 (`dict`) 实现，而 `redis` 则是基于 Redis 实现。为了避免结果占用过多内存两种实现都包含了过期自动删除机制，其中 `local` 可以设置超时删除 (`max_expire_time`) 或超过条数删除 (`max_len`)，而 `redis` 则仅支持超时删除 (`max_expire_time`)。
在启动 `AgentServerLauncher` 时可以通过传入 `pool_type` 来指定使用哪种实现，默认为`local`。
如果指定为 `redis` 则还必须传入 `redis_url`，如下是代码以及命令行的使用案例。

```python
# ...
launcher = RpcAgentServerLauncher(
    host="localhost",
    port=12345,
    custom_agent_classes=[],
    pool_type="redis",
    redis_url="redis://localhost:6379",
    max_expire_time=7200, # 2 hours
)
```

```shell
as_server start --host localhost --port 12345 --model-config-path model_config_path  --agent-dir parent_dir_of_myagents --pool-type redis --redis-url redis://localhost:6379 --max-expire-time 7200
```

[[回到顶部]](#208-distribute-zh)
