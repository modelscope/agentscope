(207-monitor-zh)=

# 监控器

在多智能体应用程序中，特别是那些依赖外部模型 API 的应用程序，监控使用情况和成本以防止过度使用并确保遵守速率限制是至关重要的。`MonitorBase` 类及其实现 `SqliteMonitor` 提供了一种追踪和调节这些 API 在您的应用中使用情况的方法。在本教程中，您将学习如何使用它们来监控 API 调用。

## 理解 AgentScope 中的监控器

`MonitorBase` 类作为一个接口，用于设置一个监控系统，跟踪各种度量指标，特别是关注 API 使用情况。它定义了一些方法，使得可以注册、检查、更新和管理与 API 调用相关的度量指标。

以下是 `MonitorBase` 的关键方法：

- **`register`**：初始化用于跟踪的度量指标，例如进行的 API 调用次数，以及可选的配额用于执行限制。
- **`exists`**：检查是否已经跟踪了某个度量指标。
- **`add`**：将度量指标增加指定的值，用于每次 API 调用后计数。
- **`update`**：一次更新多个度量指标，适用于批量更新。
- **`clear`**：将度量指标重置为零，适用于配额周期重置。
- **`remove`**：从监控中移除一个度量指标。
- **`get_value`**：检索特定度量指标的当前值。
- **`get_unit`**：获取与度量指标相关联的单元（例如，“调用”）。
- **`get_quota`**：获取允许的 API 调用的最大值。
- **`set_quota`**：调整度量指标的配额，如果 API 使用条款变更。
- **`get_metric`**：返回有关特定度量指标的详细信息。
- **`get_metrics`**：检索所有跟踪度量指标的信息，可以基于度量指标名称可选地进行过滤。
- **`register_budget`**：为某个 API 调用设置预算，将初始化一系列用于计算成本的度量指标。

## 使用监控器

### 获取监控器实例

从 `MonitorFactory` 获取监控器实例开始监控，注意多次调用 `get_monitor` 方法将返回同一个监控器实例。

```python
# 确保在这之前你已经调用了agentscope.init(...)
monitor = MonitorFactory.get_monitor()
```

> 目前上述代码返回的是 `SqliteMonitor` 实例，它在 `agentscope.init` 中初始化。
> `SqliteMonitor`  类是基于Sqlite3的 `MonitorBase` 类的默认实现。

### 基本使用

#### 注册 API 使用度量指标

注册一个新的度量指标以开始监控 token 数量：

```python
monitor.register("token_num", metric_unit="token", quota=1000)
```

#### 更新度量指标

增加 `token_num` 度量指标：

```python
monitor.add("token_num", 20)
```

#### 处理配额

如果 API 调用次数超出了配额，将抛出 `QuotaExceededError`：

```python
try:
    monitor.add("api_calls", amount)
except QuotaExceededError as e:
    # 处理超出的配额，例如，通过暂停API调用
    print(e.message)
```

#### 检索度量指标

获取当前使用的 token 数量：

```python
token_num_used = monitor.get_value("token_num")
```

#### 重置和移除度量指标

在新的周期开始时重置 token 计数：

```python
monitor.clear("token_num")
```

如果不再需要，则移除度量指标：

```python
monitor.remove("token_num")
```

### 进阶使用

> 这里的功能仍在开发中，接口可能会继续变化。

#### 使用 `prefix` 来区分度量指标

假设您有多个智能体/模型使用相同的 API 调用，但您想分别计算它们的 token 使用量，您可以在原始度量指标名称前添加一个唯一的前缀 `prefix`，`get_full_name` 函数提供了这样的功能。

例如，如果 model_A 和 model_B 都使用 OpenAI API，您可以通过以下代码注册这些度量指标。

```python
from agentscope.utils.monitor import get_full_name

...

# 在model_A中
monitor.register(get_full_name('prompt_tokens', 'model_A'))
monitor.register(get_full_name('completion_tokens', 'model_A'))

# 在model_B中
monitor.register(get_full_name('prompt_tokens', 'model_B'))
monitor.register(get_full_name('completion_tokens', 'model_B'))
```

更新这些度量指标，只需使用 `update` 方法。

```python
# 在model_A中
monitor.update(openai_response.usage.model_dump(), prefix='model_A')

# 在model_B中
monitor.update(openai_response.usage.model_dump(), prefix='model_B')
```

获取特定模型的度量指标，请使用 `get_metrics` 方法。

```python
# 获取model_A的度量指标
model_A_metrics = monitor.get_metrics('model_A')

# 获取model_B的度量指标
model_B_metrics = monitor.get_metrics('model_B')
```

#### 为 API 注册预算

当前，监控器已经支持根据各种度量指标自动计算 API 调用的成本，您可以直接为模型设置预算以避免超出配额。

假设您正在使用 `gpt-4-turbo`，您的预算是10美元，您可以使用以下代码。

```python
model_name = 'gpt-4-turbo'
monitor.register_budget(model_name=model_name, value=10, prefix=model_name)
```

使用 `prefix` 为使用相同 API 的不同模型设置预算。

```python
model_name = 'gpt-4-turbo'
# 在model_A中
monitor.register_budget(model_name=model_name, value=10, prefix=f'model_A.{model_name}')

# 在model_B中
monitor.register_budget(model_name=model_name, value=10, prefix=f'model_B.{model_name}')
```

`register_budget` 将自动注册计算总成本所需的度量指标，当这些度量指标更新时计算总成本，并在超出预算时抛出 `QuotaExceededError`。

```python
model_name = 'gpt-4-turbo'
try:
    monitor.update(openai_response.usage.model_dump(), prefix=model_name)
except QuotaExceededError as e:
    # 处理超出的配额
    print(e.message)
```

> **注意：** 此功能仍在实验阶段，只支持一些特定的 API，这些 API 已在 `agentscope.utils.monitor._get_pricing` 中列出。

[[Return to the top]](#207-monitor-zh)
