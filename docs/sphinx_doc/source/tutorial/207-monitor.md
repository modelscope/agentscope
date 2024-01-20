(207-monitor)=

# Monitor

In multi-agent applications, particularly those that rely on external model APIs, it's crucial to monitor the usage and cost to prevent overutilization and ensure compliance with rate limits. The `MonitorBase` class and its implementation, `DictMonitor`, provide a way to track and regulate the usage of such APIs in your applications. In this tutorial, you'll learn how to use them to monitor API calls.

## Understanding the `MonitorBase` Class

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

## Using the `DictMonitor` Class

The `DictMonitor` class is a subclass of the `MonitorBase` class, which is implemented in an in-memory dictionary.

### Initializing DictMonitor

Create an instance of `DictMonitor` to begin monitoring:

```python
monitor = DictMonitor()
```

### Registering API Usage Metrics

Register a new metric to start monitoring the number of tokens:

```python
monitor.register("token_num", metric_unit="token", quota=1000)
```

### Updating Metrics

Increment the `token_num` metric:

```python
monitor.add("token_num", 20)
```

### Handling Quotas

If the number of API calls exceeds the quota, a `QuotaExceededError` will be thrown:

```python
try:
    monitor.add("api_calls", amount)
except QuotaExceededError as e:
    # Handle the exceeded quota, e.g., by pausing API calls
    print(e.message)
```

### Retrieving Metrics

Get the current number of tokens used:

```python
token_num_used = monitor.get_value("token_num")
```

### Resetting and Removing Metrics

Reset the number of token count at the start of a new period:

```python
monitor.clear("token_num")
```

Remove the metric if it's no longer needed:

```python
monitor.remove("token_num")
```

## Using Singleton Access

`MonitorFactory` provides a singleton instance of a `MonitorBase` to ensure consistent access throughout your application.

### Acquiring the Singleton Monitor Instance

Get the singleton instance of the monitor:

```python
monitor = MonitorFactory.get_monitor()
```

[[Return to the top]](#monitoring-and-logging)
