(207-monitor-en)=

# Monitor

In multi-agent applications, particularly those that rely on external model APIs, it's crucial to monitor the usage and cost to prevent overutilization and ensure compliance with rate limits. The `MonitorBase` class and its implementation, `SqliteMonitor`, provide a way to track and regulate the usage of such APIs in your applications. In this tutorial, you'll learn how to use them to monitor API calls.

## Understanding the Monitor in AgentScope

The `MonitorBase` class serves as an interface for setting up a monitoring system that tracks various metrics, especially focusing on API usage. It defines methods that enable registration, checking, updating, and management of metrics related to API calls.

Here are the key methods of `MonitorBase`:

- **`register`**: Initializes a metric for tracking, such as the number of API calls made, with an optional quota to enforce limits.
- **`exists`**: Checks whether a metric is already being tracked.
- **`add`**: Increments the metric by a specified value, used to count each API call made.
- **`update`**: Updates multiple metrics at once, useful for batching updates.
- **`clear`**: Resets a metric to zero, which can be useful when the quota period resets.
- **`remove`**: Removes a metric from monitoring.
- **`get_value`**: Retrieves the current count for a particular metric.
- **`get_unit`**: Fetches the unit associated with the metric (e.g., "calls").
- **`get_quota`**: Obtains the maximum number of allowed API calls.
- **`set_quota`**: Adjusts the quota for a metric, if the terms of API usage change.
- **`get_metric`**: Returns detailed information about a specific metric.
- **`get_metrics`**: Retrieves information about all tracked metrics, with optional filtering based on metric names.
- **`register_budget`**: Sets a budget for a certain API call, which will initialize a series of metrics used to calculate the cost.

## Using the Monitor

### Get a Monitor Instance

Get a monitor instance from `MonitorFactory` to begin monitoring, and note that multiple calls to the `get_monitor` method return the same monitor instance.

```python
# make sure you have called agentscope.init(...) before
monitor = MonitorFactory.get_monitor()
```

> Currently the above code returns a `SqliteMonitor` instance, which is initialized in `agentscope.init`.
> The `SqliteMonitor` class is the default implementation of `MonitorBase` class, which is based on Sqlite3.

### Basic Usage

#### Registering API Usage Metrics

Register a new metric to start monitoring the number of tokens:

```python
monitor.register("token_num", metric_unit="token", quota=1000)
```

#### Updating Metrics

Increment the `token_num` metric:

```python
monitor.add("token_num", 20)
```

#### Handling Quotas

If the number of API calls exceeds the quota, a `QuotaExceededError` will be thrown:

```python
try:
    monitor.add("api_calls", amount)
except QuotaExceededError as e:
    # Handle the exceeded quota, e.g., by pausing API calls
    print(e.message)
```

#### Retrieving Metrics

Get the current number of tokens used:

```python
token_num_used = monitor.get_value("token_num")
```

#### Resetting and Removing Metrics

Reset the number of token count at the start of a new period:

```python
monitor.clear("token_num")
```

Remove the metric if it's no longer needed:

```python
monitor.remove("token_num")
```

### Advanced Usage

> Features here are under development, the interface may continue to change.

#### Using `prefix` to Distinguish Metrics

Assume you have multiple agents/models that use the same API call, but you want to calculate their token usage separately, you can add a unique `prefix` before the original metric name, and `get_full_name` provides such functionality.

For example, if model_A and model_B both use the OpenAI API, you can register these metrics by the following code.

```python
from agentscope.utils.monitor import get_full_name

...

# in model_A
monitor.register(get_full_name('prompt_tokens', 'model_A'))
monitor.register(get_full_name('completion_tokens', 'model_A'))

# in model_B
monitor.register(get_full_name('prompt_tokens', 'model_B'))
monitor.register(get_full_name('completion_tokens', 'model_B'))
```

To update those metrics, just use the `update` method.

```python
# in model_A
monitor.update(openai_response.usage.model_dump(), prefix='model_A')

# in model_B
monitor.update(openai_response.usage.model_dump(), prefix='model_B')
```

To get metrics of a specific model, please use the `get_metrics` method.

```python
# get metrics of model_A
model_A_metrics = monitor.get_metrics('model_A')

# get metrics of model_B
model_B_metrics = monitor.get_metrics('model_B')
```

#### Register a budget for an API

Currently, the Monitor already supports automatically calculating the cost of API calls based on various metrics, and you can directly set a budget of a model to avoid exceeding the quota.

Suppose you are using `gpt-4-turbo` and your budget is $10, you can use the following code.

```python
model_name = 'gpt-4-turbo'
monitor.register_budget(model_name=model_name, value=10, prefix=model_name)
```

Use `prefix` to set budgets for different models that use the same API.

```python
model_name = 'gpt-4-turbo'
# in model_A
monitor.register_budget(model_name=model_name, value=10, prefix=f'model_A.{model_name}')

# in model_B
monitor.register_budget(model_name=model_name, value=10, prefix=f'model_B.{model_name}')
```

`register_budget` will automatically register metrics that are required to calculate the total cost, calculate the total cost when these metrics are updated, and throw a `QuotaExceededError` when the budget is exceeded.

```python
model_name = 'gpt-4-turbo'
try:
    monitor.update(openai_response.usage.model_dump(), prefix=model_name)
except QuotaExceededError as e:
    # Handle the exceeded quota
    print(e.message)
```

> **Note:** This feature is still in the experimental stage and only supports some specified APIs, which are listed in `agentscope.utils.monitor._get_pricing`.

[[Return to the top]](#207-monitor-en)
