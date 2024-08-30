(208-distribute-zh)=

# 并行/分布式

为了提供更好的性能以及支持更多的 Agent 同时运行，AgentScope 实现了基于 Actor 范式的 并行/分布式模式（后续简称为分布式模式）。该模式相比传统单进程模式具有以下特点：

- **高性能**: 同一应用中的不同 Agent 以及其他服务可以运行不同进程甚至不同机器上，充分利用计算资源释放性能。
- **自动并行化**: 基于 Actor 模式，每个 Agent都具有独立的状态，在编写应用时无需考虑调用顺序、资源竞争等问题，自动实现应用并行化。
- **零迁移成本**: 代码与单机模式完全兼容，单机模式可运行的应用可以零成本直接迁移至并行/分布式模式。

本节将详细介绍 AgentScope 分布式的使用方法并简述其原理。

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
- **独立进程模式 (Indpendent Mode)**: 在独立进程模式下，智能体进程相对主进程来说是独立的，需要预先在机器上启动智能体进程，并向 `to_dist` 函数传入一些特定的参数。如果需要实现 Agent 跨机器部署，必须使用该模式，另外如果对性能要求较高或是 Agent 数量较多也建议使用该模式。

### 使用独立进程模式

与子进程模式相比，独立进程模式能够避免子进程初始化的开销，从而消除运行初期的延迟，对于 Agent 数量较多的场景能够有效提升运行效率。

独立进程模式下，需要在机器上提前启动智能体服务器进程，并且向 `to_dist` 函数传入需要连接的智能体服务进程的 `host` 以及 `port`。
这里我们依旧使用基础用法部分的案例来演示，假设[基础用法](#basic_usage-zh)部分的代码文件为 `dist_main.py`，需要将如下代码保存为 `dist_server.py`。

```python
# 请不要使用 jupyter notebook 运行该代码
# 请将代码拷贝到 `dist_server.py` 文件后使用 `python dist_server.py` 命令运行该代码
# 运行该代码前请先安装 agentscope 的分布式版本
# pip install agentscope[distribute]

import agentscope
from agentscope.server import RpcAgentServerLauncher

from dist_main import WebAgent


if __name__ == "__main__":
    agentscope.init()
    assistant_server_launcher = RpcAgentServerLauncher(
        host="localhost",
        port=12345,
        custom_agent_classes=[WebAgent],
    )
    assistant_server_launcher.launch(in_subprocess=False)
    assistant_server_launcher.wait_until_terminate()
```

注意将 `dist_main.py` 与 `dist_server.py` 放在相同目录下(这里假设为`your_project_dir`)。

```text
your_project_dir
├── dist_main.py
└── dist_server.py
```

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

- 对于独立进程模式，只需要在初始化函数中传入 `to_dist=True` 即可。

    ```python
    def init_with_dist():
        return [WebAgent(f"W{i}", to_dist=True) for i in range(len(URLS))]
    ```

- 对于子进程模式，则需要将原来传入`to_dist`函数的参数以字典的形式传入到 `to_dist` 域中。

    ```python
    def init_with_dist():
        return [WebAgent(f"W{i}", to_dist={"host": "localhost", "port": "12345"}) for i in range(len(URLS))]
    ```

> Note：
> 一些 IDE 的自动补全功能可能提示 `to_dist` 参数不存在，但实际运行时并不会报错。
> 另外，如果已经在初始化参数中传入了 `to_dist`，则不能再调用 `to_dist` 方法。

## 高级开发者指南

本节主要面向基于 AgentScope 分布式模式进行开发的开发者，需要开发者对进程、线程、同步、异步、RPC、Python 元类以及GIL等概念有一定的理解，如果只是常规使用 AgentScope，则无需阅读本节内容。
本节将会介绍 AgentScope 分布式模式的原理，如何基于现有的分布式模式实现自定义功能，以及如何优化分布式模式的性能。

AgentScope 分布式模式的本质是:

**将原本运行在某个 Python 进程 (即主进程) 中的对象通过 `to_dist` 函数或是初始化参数转移到另一个 RPC 服务器进程 (即智能体服务器进程) 中，并在原 Python 进程中保留一个 `RpcObject` 作为代理，任何 `RpcObject` 上的函数调用或是属性访问都会转发到 RPC 服务器中的原始对象上，并且开发者可以自行决定是使用同步调用还是异步调用。**

接下来将具体介绍用于实现分布式模式的关键组件 `RpcMeta` 以及 `RpcObject`。

### `RpcMeta`

{class}`RpcMeta<agentscope.rpc.RpcMeta>` 类是一个元类(Meta class)，会自动向继承自己的子类添加 `to_dist` 方法以及 `to_dist` 初始化参数 (因此 IDE 可能会提示 `to_dist` 参数不存在，但实际运行时并不会报错)，其实现位于 `src/agentscope/rpc/rpc_meta.py`。

在一个已经初始化完成的对象上调用 `to_dist` 方法会将原对象的初始化参数打包发送到 智能体服务器进程 中，并在智能体服务器进程中重新初始化该对象，而在主进程中会返回一个 `RpcObject` 替代原有的对象。

由于是使用初始化参数来重建原有对象，无法维持创建后的状态变化，因此建议在初始化的同时立即调用 `to_dist` 方法，或者直接在原对象的初始化函数中传入 `to_dist` 参数。

由于 `to_dist` 是 `RpcMeta` 自动向子类添加的方法，因此不仅是 Agent 类，任何继承自 `RpcMeta` 的类都可以使用 `to_dist` 方法。

`RpcMeta` 除了提供 `to_dist` 方法外还会记录原对象上能够被调用的方法以及属性，以方便在 `RpcObject` 中调用。默认情况下只会记录原对象上的公有方法，并且使用同步调用 (调用时会阻塞调用发起方，直到原对象上的方法执行完毕)。如果需要使用异步调用需要在方法声明上添加 `async_func` 装饰器。

{func}`async_func<agentscope.rpc.async_func>` 装饰器的实现位于 `src/agentscope/rpc/rpc_meta.py`，与之相对的还有一个 {func}`sync_func<agentscope.rpc.sync_func>` 装饰器。用于标识同步方法，但由于默认是同步方法，因此一般不使用。`AgentBase` 及其所有子类的 `__call__` 以及 `reply` 方法都被标记为了 `async_func` 以避免阻塞。

如下是一个简单的示例，这里声明了一个 `Example` 类，其中 `sync_method` 是同步方法，`async_method` 被标记为了异步方法，`_protected_method` 是私有方法。

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
    def async_method(self) -> str:
        # 异步方法，调用者不会被阻塞，可以继续执行直到尝试获取结果
        time.sleep(1)
        return "async"

    def _protected_method(self) -> str:
        # 不是公有方法，rpc object 无法调用该方法
        time.sleep(1)
        return "protected"

    @async_func
    def complex_result(self) -> dict:
        time.sleep(1)
        return {"a": 1, "b": 2, "c": "hello world",}


if __name__ == "__main__":
    example = Example(to_dist=True)
    t1 = time.time()
    sync_result = example.sync_method()
    assert sync_result == "sync"
    t2 = time.time()
    print(f"Sync func cost: {t2 - t1} s")
    t3 = time.time()
    async_result = example.async_method()
    t4 = time.time()
    print(f"Async func cost: {t4 - t3} s")
    # 需要在返回值上调用 result 方法获取异步执行结果
    assert async_result.result() == "async"
    # 访问 protected 方法会引发未定义行为，请避免使用
    # protected_result = example._protected_method()
    complex_result = example.complex_result()
    assert complex_result["a"] == 1
    assert complex_result["b"] == 2
    assert complex_result["c"] == "hello world"
```

上述代码的运行结果样例如下，可以观察到调用 `async_method` 的耗时比 `sync_method` 短很多，这是因为 `async_method` 是异步方法，不会阻塞调用发起方，而 `sync_method` 是同步方法，因此会阻塞调用发起方。

```text
Sync func cost: 1.0073761940002441 s
Async func cost: 0.0003597736358642578 s
```

### `RpcObject`

{class}`RpcObject<agentscope.rpc.RpcObject>` 的实现位于 `src/agentscope/rpc/rpc_object.py` 中。
`RpcObject` 是一个代理，其内部并不包含原对象的任何属性值或是方法，只记录了原对象所在的智能体服务器的地址以及该对象的 `id`。

`RpcObject` 在初始化时如果发现没有提供 `host` 和 `port` 参数 (即子进程模式)，就会去启动一个新的智能体服务器进程，并在该进程上重新创建原对象，而启动新的智能体服务器进程相对缓慢，这也是导致子进程模式初始化时间较长的主要原因。
而如果提供了 `host` 和 `port` 参数 (即独立进程模式)，`RpcObject` 就会直接连接该服务器并重新创建原对象，避免了启动新进程的开销。

当尝试访问 `RpcObject` 上不存在的方法或属性时，`RpcObject` 会通过 `__getattr__` 将请求转发到智能体服务器进程上。对于同步方法 (`@sync_func`)，`RpcObject` 会阻塞调用发起方，直到原对象上的方法执行完毕，并返回执行结果。而异步方法 (`@async_func`) 则会立即返回一个 {class}`AsyncResult<agentscope.rpc.AsyncResult>` 对象，如果主进程不去访问该对象的具体值就可以无阻塞地继续运行，而如果需要获取执行结果，则需要调用 `AsyncResult` 对象上的 `result` 方法，这时如果结果还没有返回，`result` 方法会阻塞调用发起方，直到结果返回。

为了进一步简化使用，`AsyncResult` 在返回的结果不是 `bool`，`int`，`float`，`string` 这些基本数据类型时，可以直接充当真实结果使用，可以直接在 `AsyncResult` 上获取属性，例如上述 `complex_result` 示例中的 `complex_result["a"]`，其内部的值会在访问时自动更新。
