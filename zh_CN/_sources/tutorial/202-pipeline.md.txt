(202-pipeline-zh)=

# Pipeline 和 MsgHub

**Pipeline**和**Message Hub**主要用于描绘应用中信息的交换和传播过程，它们极大简化了Multi-Agent应用流程的编排工作。
在本教程中，我们将详细的介绍Pipeline和Message Hub的原理和使用方式。

## Pipeline

在AgentScope中，消息的交换、传播构成了Multi-Agent应用。但是对复杂应用来说，细致的描绘每一次信息交流对开发者来说是非常困难的。
`Pipeline`主要用于简化“描述消息传播”的编程工作。

`Pipeline`中接收的对象是`Operator`，即信息的加工和传播单元（例如智能体`Agent`是`Operator
`的一个子类），而`Pipeline`自身也是`Operator`的子类。以下是所有`Pipeline`的基类：

```python
class PipelineBase(Operator):
   """所有pipelines的基础接口."""
    # ... [为简洁起见省略代码]
    @abstractmethod
    def __call__(self, x: Optional[dict] = None) -> dict:
        """在这定义pipeline采取的操作。

        Args:
            x (Optional[`dict`], optional):
                对话历史以及一些环境信息。

        Returns:
            `dict`: 经过Pipeline处理后的返回消息。
        """
```

### 类别

为了方便开发者的使用，对于同一功能的Pipeline，AgentScope提供了两种不同的实现策略：

* **对象类型Pipeline**

  * 这些Pipeline是面向对象的，继承自
    `PipelineBase`。它们本身是`Operator`，可以与其他运算符组合以创建复杂的交互模式，并且可以复用。

    ```python
    # 实例化并调用
    pipeline = ClsPipeline([agent1, agent2, agent3])
    x = pipeline(x)
    ```

* **函数式Pipeline**

  * 函数式Pipeline是独立的函数实现，在不需要复用的一次性使用场景中很有用。

    ```python
    # 只需要调用
    x = funcpipeline([agent1, agent2, agent3], x)
    ```

Pipeline根据其功能被分类成以下的类型。下表概述了 AgentScope 中可用的不同 Pipeline：

| 运算符类型Pipeline | 函数式Pipeline | 描述                                                |
| -------------------- | ------------------- | ------------------------------------------------------------ |
| `SequentialPipeline` | `sequentialpipeline` | 按顺序执行一系列运算符，将一个运算符的输出作为下一个运算符的输入。 |
| `IfElsePipeline`     | `ifelsepipeline`    | 实现条件逻辑，如果条件为真，则执行一个运算符；如果条件为假，则执行另一个运算符。 |
| `SwitchPipeline`     | `switchpipeline`    | 实现分支选择，根据条件的结果从映射集中执行一个运算符。 |
| `ForLoopPipeline`    | `forlooppipeline`   | 重复执行一个运算符，要么达到设定的迭代次数，要么直到满足指定的中止条件。 |
| `WhileLoopPipeline`  | `whilelooppipeline` | 只要给定条件保持为真，就持续执行一个运算符。 |
| -                    | `placeholder`       | 在流控制中不需要任何操作的分支，如 if-else/switch 中充当占位符。 |

### 使用说明

本节通过比较有无 Pipeline 的情况下多智能体应用程序中逻辑实现的方式，来阐释 Pipeline 如何简化逻辑实现。
**注意：** 请注意，在下面提供的示例中，我们使用术语 `agent` 来代表任何可以作为 `Operator` 的实例。这是为了便于理解，并说明 Pipeline 是如何协调不同操作之间的交互的。您可以将 `agent` 替换为任何 `Operator`，从而在实践中允许 `agent` 和 `pipeline` 的混合使用。

#### `SequentialPipeline`

* 不使用 pipeline:

  ```python
  x = agent1(x)
  x = agent2(x)
  x = agent3(x)
  ```

* 使用 pipeline:

  ```python
  from agentscope.pipelines import SequentialPipeline

  pipe = SequentialPipeline([agent1, agent2, agent3])
  x = pipe(x)
  ```

* 使用函数式 pipeline:

  ```python
  from agentscope.pipelines import sequentialpipeline

  x = sequentialpipeline([agent1, agent2, agent3], x)
  ```

#### `IfElsePipeline`

* 不使用 pipeline:

  ```python
  if condition(x):
      x = agent1(x)
  else:
      x = agent2(x)
  ```

* 使用 pipeline:

  ```python
  from agentscope.pipelines import IfElsePipeline

  pipe = IfElsePipeline(condition, agent1, agent2)
  x = pipe(x)
  ```

* 使用函数式 pipeline:

  ```python
  from agentscope.functional import ifelsepipeline

  x = ifelsepipeline(condition, agent1, agent2, x)
  ```

#### `SwitchPipeline`

* 不使用 pipeline:

  ```python
  switch_result = condition(x)
  if switch_result == case1:
      x = agent1(x)
  elif switch_result == case2:
      x = agent2(x)
  else:
      x = default_agent(x)
  ```

* 使用 pipeline:

  ```python
  from agentscope.pipelines import SwitchPipeline

  case_operators = {case1: agent1, case2: agent2}
  pipe = SwitchPipeline(condition, case_operators, default_agent)
  x = pipe(x)
  ```

* 使用函数式 pipeline:

  ```python
  from agentscope.functional import switchpipeline

  case_operators = {case1: agent1, case2: agent2}
  x = switchpipeline(condition, case_operators, default_agent, x)
  ```

#### `ForLoopPipeline`

* 不使用 pipeline:

  ```python
  for i in range(max_iterations):
      x = agent(x)
      if break_condition(x):
          break
  ```

* 使用 pipeline:

  ```python
  from agentscope.pipelines import ForLoopPipeline

  pipe = ForLoopPipeline(agent, max_iterations, break_condition)
  x = pipe(x)
  ```

* 使用函数式 pipeline:

  ```python
  from agentscope.functional import forlooppipeline

  x = forlooppipeline(agent, max_iterations, break_condition, x)
  ```

#### `WhileLoopPipeline`

* 不使用 pipeline:

    ```python
    while condition(x):
        x = agent(x)
    ```

* 使用 pipeline:

    ```python
    from agentscope.pipelines import WhileLoopPipeline

    pipe = WhileLoopPipeline(agent, condition)
    x = pipe(x)
    ```

* 使用函数式 pipeline:

    ```python
    from agentscope.functional import whilelooppipeline

    x = whilelooppipeline(agent, condition, x)
    ```

### Pipeline 组合

值得注意的是，AgentScope 支持组合 Pipeline 来创建复杂的交互。例如，我们可以创建一个 Pipeline，按顺序执行一系列智能体，然后执行另一个 Pipeline，根据条件执行一系列智能体。

```python
from agentscope.pipelines import SequentialPipeline, IfElsePipeline
# 创建一个按顺序执行智能体的 Pipeline
pipe1 = SequentialPipeline([agent1, agent2, agent3])
# 创建一个条件执行智能体的 Pipeline
pipe2 = IfElsePipeline(condition, agent4, agent5)
# 创建一个按顺序执行 pipe1 和 pipe2 的 Pipeline
pipe3 = SequentialPipeline([pipe1, pipe2])
# 调用 Pipeline
x = pipe3(x)
```

## MsgHub

`MsgHub` 旨在管理一组智能体之间的对话/群聊，其中允许共享消息。通过 `MsgHub`，智能体可以使用 `broadcast` 向群组中的所有其他智能体广播消息。

以下是 `MsgHub` 的核心类：

```python
class MsgHubManager:
    """MsgHub 管理类，用于在一组智能体之间共享对话。"""
    # ... [为简洁起见省略代码]

    def broadcast(self, msg: Union[dict, list[dict]]) -> None:
        """将消息广播给所有参与者。"""
        for agent in self.participants:
            agent.observe(msg)

    def add(self, new_participant: Union[Sequence[AgentBase], AgentBase]) -> None:
       """将新参与者加入此 hub"""
        # ... [为简洁起见省略代码]

    def delete(self, participant: Union[Sequence[AgentBase], AgentBase]) -> None:
       """从参与者中删除智能体。"""
        # ... [为简洁起见省略代码]
```

### 使用说明

#### 创建一个 MsgHub

要创建一个 `MsgHub`，请通过调用 `msghub` 辅助函数并传入参与智能体列表来实例化一个 `MsgHubManager`。此外，您可以提供一个可选的初始声明`announcement`，如果提供，将在初始化时广播给所有参与者。

```python
from agentscope.msg_hub import msghub

# Initialize MsgHub with participating agents
hub_manager = msghub(
    participants=[agent1, agent2, agent3], announcement=initial_announcement
)
```

#### 在 MsgHub 中广播消息

`MsgHubManager` 可以与上下文管理器一起使用，以处理`MsgHub`环境的搭建和关闭：

```python
with msghub(
    participants=[agent1, agent2, agent3], announcement=initial_announcement
) as hub:
    # 智能体现在可以在这个块中广播和接收消息
    agent1()
    agent2()

    # 或者手动广播一条消息
    hub.broadcast(some_message)

```

退出上下文块时，`MsgHubManager` 会确保每个智能体的听众被清空，防止在中心环境之外的任何意外消息共享。

#### 添加和删除参与者

你可以动态地从 `MsgHub` 中添加或移除智能体：

```python
# 添加一个新参与者
hub.add(new_agent)

# 移除一个现有的参与者
hub.delete(existing_agent)
```

[[返回顶部]](#202-pipeline-zh)
