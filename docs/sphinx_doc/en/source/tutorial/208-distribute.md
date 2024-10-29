(208-distribute-en)=

# Distribution

To provide better performance and support the concurrent of more agents, AgentScope implements a parallel/distributed mode based on the Actor model. Compared to the traditional single-process mode, it has the following characteristics:

- **High Performance**: Different agents and other services within the same application can run on different processes or even different machines, fully utilizing computing resources to unleash performance.
- **Automatic Parallelization**: Based on the Actor model, each agent has an independent state. When implementing applications, there's no need to consider invocation order, resource competition, etc., enabling automatic application parallelization.
- **Zero Migration Cost**: The code is fully compatible with the single-machine mode. Applications that can run in single-process mode can be migrated to the distributed mode at zero cost.

This section will detail the usage of AgentScope's distributed mode and introduce its principles.

(basic_usage-en)=

## Basic Usage

The distributed mode requires almost no modification to the running code compared to the traditional mode. Simply call the {func}`to_dist<agentscope.rpc.RpcMeta.to_dist>` function during the agent initialization phase.

```python
# import some packages

# init agentscope

# Initialization in traditional mode
# agent = Agent(...)

# Initialization in distributed mode
agent = Agent(...).to_dist()

x = Msg(...)
y = agent(x)
```

In this section, we will demonstrate how to specifically use AgentScope's distributed mode with a webpage retrieval example. To highlight the acceleration effect brought by AgentScope's distributed mode, a simple custom `WebAgent` is used here.
This agent simulates the process of crawling webpages and looking for answers by sleeping for 5 seconds. In the example, there are a total of 5 agents, each crawling a webpage and searching for answers.

The only difference between the traditional mode and the distributed mode lies in the initialization phase, specifically in `init_without_dist` and `init_with_dist`.
The only difference in `init_with_dist` compared to `init_without_dist` is the additional call to the `to_dist` function.
After initialization, the `run` function is exactly the same for both modes. However, the running time differs significantly between the two modes.

```python
# Please do not run this code in a Jupyter notebook
# Copy the code to a `dist_main.py` file and run it using `python dist_main.py`
# Ensure you have installed the distributed version of agentscope before running the code
# pip install agentscope[distribute]

import time
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg

class WebAgent(AgentBase):

    def __init__(self, name):
        super().__init__(name)

    def get_answer(self, url: str, query: str):
        """Simulate crawling the web and looking for answers"""
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
    print(f"Time taken for initialization: {end - start}")
    print(f"Time taken without distributed mode: {run(simple_agents)}")
    print(f"Time taken with distributed mode: {run(dist_agents)}")
```

Sample output of the above code is as follows:

```text
Time taken for initialization: 12.944042921066284
[W0] Answer from page_1
[W1] Answer from page_2
[W2] Answer from page_3
[W3] Answer from page_4
[W4] Answer from page_5
Time taken without distributed mode: 25.022241830825806
[W0] Answer from page_1
[W1] Answer from page_2
[W2] Answer from page_3
[W3] Answer from page_4
[W4] Answer from page_5
Time taken with distributed mode: 5.021369934082031
```

As observed from the output, there is a significant reduction in running time when using the distributed mode (from 25 seconds to 5 seconds).
The example above represents the most common usage of AgentScope's distributed mode. When not aiming for ultimate performance or the number of Agents is relatively small (e.g., no more than 10), it is advisable to use the method demonstrated above.
For further performance optimization, a deeper understanding of AgentScope's distributed model is required, and subsequent sections will introduce advanced usage of the distributed mode in detail.

## Advanced Usage

This section will introduce advanced uses of the AgentScope distributed mode to further enhance efficiency. Before delving into advanced usage, we need to have a basic understanding of the fundamental concepts of the AgentScope distributed mode.

### Fundamental Concepts

- **Main Process**: The process where the AgentScope application resides is called the main process. For instance, the `run` function in the example from the previous section runs in the main process. Each AgentScope application will have only one main process.
- **Agent Server Process**: In distributed mode, the agent server process is where agents run. For example, in the example from the previous section, all agents in `dist_agents` actually run in the agent server process. Multiple agent server processes can exist at the same time. Agent server processes can run on any network-accessible node, and within each agent server process, multiple agents can run simultaneously.

- **Child Mode**: In child mode, the agent server process is spawned as a child process by the main process. In the example from the previous section, each agent in `dist_agents` is actually a child process of the main process. This mode is the default running mode for AgentScope distributed applications, meaning that when calling the `to_dist` function without any parameters, it defaults to this mode. This mode is employed in the [basic usage](#basic_usage-en) section.
- **Independent Mode**: In independent mode, the agent processes are independent of the main process. The agent processes need to be started on the machine in advance, and certain parameters need to be passed to the `to_dist` function. This mode must be used if agents need to be deployed across different machines. Additionally, this mode is recommended if performance is major concern, or you have a large number of agents.

### Using Independent Mode

Compared to child mode, independent mode can avoid the overhead of initializing child processes during runtime, thereby eliminating startup latency and enhancing operational efficiency in scenarios with many agents.

In independent mode, agent server processes need to be started in advance on the machines, and the `host` and `port` of the agent server process to connect to should be passed to the `to_dist` function.

We will still use the example from the basic usage section for demonstration. Assuming the code file from the [basic usage](#basic_usage-en) section is named `dist_main.py`, the following code should be saved as `dist_server.py`.

```python
# Do not run this code in a Jupyter notebook
# Copy the code to a file named `dist_server.py` and run it using the command `python dist_server.py`. The directory structure should be:
# your_project_dir
# ├── dist_main.py
# └── dist_server.py
# Install the distributed version of agentscope before running the code
# pip install agentscope[distribute]

import agentscope
from agentscope.server import RpcAgentServerLauncher
from dist_main import WebAgent

if __name__ == "__main__":
    agentscope.init(
        # model_configs=...  # Model configuration. If no model is needed, this parameter can be omitted.
    )
    assistant_server_launcher = RpcAgentServerLauncher(
        host="localhost",
        port=12345,
        custom_agent_classes=[WebAgent],
    )
    assistant_server_launcher.launch(in_subprocess=False)
    assistant_server_launcher.wait_until_terminate()
```

In the above code, we use `RpcAgentServerLauncher` to start an agent server process. Note that `WebAgent` is not an agent implementation provided by AgentScope, so it needs to be added to `custom_agent_classes`. Additionally, if model APIs are required in the agent server process, corresponding model parameters should be configured in `agentscope.init`.

Furthermore, the `init_with_dist` function in `dist_main.py` needs to be updated to the following code:

```python
def init_with_dist():
    return [WebAgent(f"W{i}").to_dist(host="localhost", port=12345) for i in range(len(URLS))]
```

In this new version of `init_with_dist`, two new parameters, `host` and `port`, are added to connect to the agent server process.

After modifying the code, run the `dist_server.py` file in one command line and wait for it to start successfully. Then run the `dist_main.py` file in another command line. During execution, the following output will be displayed:

```text
Initialization time: 0.005397319793701172
[W0] Answer from page_1
[W1] Answer from page_2
[W2] Answer from page_3
[W3] Answer from page_4
[W4] Answer from page_5
Non-distributed mode runtime: 25.023009061813354
[W0] Answer from page_1
[W1] Answer from page_2
[W2] Answer from page_3
[W3] Answer from page_4
[W4] Answer from page_5
Distributed mode runtime: 5.021481990814209
```

At this point, the initialization time of `dist_main.py` will be significantly reduced, for instance, just 0.005 seconds in this case.

### Avoiding Repeated Initialization

The above code calls the `to_dist` function on an already initialized agent. `to_dist` essentially clones the original agent to the agent server process, retaining an {class}`RpcObject<agentscope.rpc.RpcObject>` in the main process as a proxy for the original agent. Calls to this `RpcObject` are forwarded to the corresponding agent in the agent server process.

This process has a potential issue: the original agent is initialized twice, once in the main process and once in the agent server process. These two initializations occur sequentially, lacking the ability to be parallelized. For agents with low initialization costs, directly calling the `to_dist` function will not significantly impact performance. However, for agents with high initialization costs, repeated initialization should be avoided. Therefore, AgentScope distributed mode provides another method for initializing in distributed mode, which entails passing the `to_dist` parameter directly within the initialization function of any agent. The following code modifies the `init_with_dist` function in `dist_main.py`.

- For child mode, simply pass `to_dist=True` in the initialization function.

    ```python
    def init_with_dist():
        return [WebAgent(f"W{i}", to_dist=True) for i in range(len(URLS))]
    ```

- For independent mode, pass the parameters previously given to the `to_dist` function as a dictionary to the `to_dist` field.

    ```python
    def init_with_dist():
        return [WebAgent(f"W{i}", to_dist={"host": "localhost", "port": "12345"}) for i in range(len(URLS))]
    ```

```{note}
Some IDEs might display a hint indicating that the `to_dist` parameter does not exist, but this will not cause an error at runtime.
Additionally, if the `to_dist` parameter has already been passed in the initialization parameters, the `to_dist` method should not be called again.
```

## Developer Guide

```{note}
This section is aimed at developers who are developing new features based on the AgentScope distributed mode. It requires a certain understanding of distributed programming principles such as processes, threads, synchronization, asynchronicity, gRPC, Python metaclasses, and the Global Interpreter Lock (GIL). Even if you lack the aforementioned background, reading this section will still provide insights into the fundamental principles and advanced usages of the AgentScope distributed mode.
```

The core logic of the AgentScope distributed model is:

**By using the `to_dist` function or initialization parameters, objects that originally run in any Python process are transferred to an RPC server. In the original process, a `RpcObject` proxy is retained, and any function call or attribute access on this `RpcObject` will be forwarded to the object on the RPC server. When calling functions, you can decide whether to use synchronous or asynchronous invocation.**

The following graph illustrate the workflow of `to_dist`, synchronous and asynchronous invocation.

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

As illustrated in the previous figure, the distributed mode of AgentScope essentially follows a Client-Server architecture. In this setup, the user-authored agent applications (Processes) act as the Client, while the agent server process (RPC Server) functions as the Server. In distributed mode, the Client side sends the local agents to the Server side for execution. The Client forwards local function calls and property accesses to the Server, which is responsible for receiving the agents and handling various invocation requests from the Client.

```{note}
Communication between the Client and Server in AgentScope's distributed mode is implemented using gRPC. There is a strict limitation on the size of messages send/recv; by default, a single message cannot exceed 32 MB. This value can be further increased by modifying the `_DEFAULT_RPC_OPTIONS` parameter in `src/agentscope/constants.py`.
```

Next, we'll introduce the implementation of the Client and Server respectively.

### Client Side

The Client Side mainly consists of two primary classes: `RpcMeta` and `RpcObject`. `RpcMeta` is responsible for sending local objects to the Server, while `RpcObject` handles the forwarding of subsequent invocation requests.

#### `RpcMeta`

The class {class}`RpcMeta<agentscope.rpc.RpcMeta>` is a metaclass that automatically adds the `to_dist` method and `to_dist` initialization parameter to its subclasses (thus IDEs might indicate `to_dist` parameter does not exist, but in actuality, it won't cause an error during runtime). Its implementation can be found in `src/agentscope/rpc/rpc_meta.py`.

Calling the `to_dist` method on an already initialized object sends the object's initialization parameters to the Agent Server Process and reinitializes the object within that process. The main process returns a `RpcObject` to replace the original object.

Since the original object is reconstructed using initialization parameters, it cannot maintain state changes that occurred after creation. Thus, it is recommended to call the `to_dist` method immediately upon initialization or pass the `to_dist` parameter directly in the object's initialization function.

Since `to_dist` is automatically added to subclasses by `RpcMeta`, any class that inherits from `RpcMeta`, not just `Agent` classes, can use the `to_dist` method.

In addition to providing the `to_dist` method, `RpcMeta` also records callable methods and attributes from the original object to facilitate invocation within the `RpcObject`. By default, only public methods of the original object are recorded and invoked synchronously (the caller is blocked until the method on the original object has finished executing). If asynchronous invocation is needed, the `async_func` decorator should be added to the method declaration.

#### `async_func` and `AsyncResult`

The decorator {func}`async_func<agentscope.rpc.async_func>` is implemented in `src/agentscope/rpc/rpc_meta.py`. The `__call__` and `reply` methods of `AgentBase` and all its subclasses are marked with `async_func` to avoid blocking.

In contrast to `async_func`, there is also the {func}`sync_func<agentscope.rpc.sync_func>` decorator, which is used to mark synchronous methods. However, since synchronous methods are the default, they generally do not need to be explicitly marked.

Below is a simple example where we declare a class `Example`. In this class, `sync_method` is a synchronous method, `async_method_basic` and `async_method_complex` are marked as asynchronous methods, and `_protected_method` is a private method.

```python
import time
from agentscope.rpc import RpcMeta, async_func

class Example(metaclass=RpcMeta):

    # @sync_func  # Default is sync_func, can be omitted
    def sync_method(self) -> str:
        # Synchronous method, caller will be blocked for 1 s
        time.sleep(1)
        return "sync"

    @async_func
    def async_method_basic(self) -> str:
        # Asynchronous method, caller will not be blocked and can continue until attempting to get the result
        time.sleep(1)
        # Return a basic type
        return "async"

    @async_func
    def async_method_composite(self) -> dict:
        # Asynchronous method
        time.sleep(1)
        # Return a dictionary
        return {"a": 1, "b": 2, "c": "hello world"}

    def _protected_method(self) -> str:
        # Not a public method, rpc object cannot call this method
        time.sleep(1)
        return "protected"

if __name__ == "__main__":
    example = Example(to_dist=True)
    # Calling protected method will result in undefined behavior, avoid using it
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
    # Basic type results need to call the result method to get the asynchronous execution result
    assert async_basic.result() == "async"
    # Composite types automatically update asynchronous execution results when accessing required fields
    assert async_composite["a"] == 1
    assert async_composite["b"] == 2
    assert async_composite["c"] == "hello world"
```

The result of running the above code sample is shown below. You can observe that the time taken to call `async_method` is much shorter than `sync_method`. This is because `async_method` is asynchronous and does not block the caller, whereas `sync_method` is synchronous and blocks the caller.

```text
Sync func cost: 1.0073761940002441 s
Async func cost: 0.0003597736358642578 s
```

In the above code, `async_method_basic` and `async_method_complex` return instances of the {class}`AsyncResult<agentscope.rpc.AsyncResult>` class. This object can return the result of asynchronous execution through its `result` method. To maintain a consistent interface between asynchronous and synchronous calls, if the result represented by `AsyncResult` is a composite type, you do not need to call the `result` method manually. When accessing internal attributes, `result` is automatically called to update the execution result (as shown in the example for `async_composite`).

#### `RpcObject`

{class}`RpcObject<agentscope.rpc.RpcObject>` is implemented in `src/agentscope/rpc/rpc_object.py`.
`RpcObject` acts as a proxy and does not contain any attribute values or methods of the original object. It only records the address of the agent server process where the original object resides and the object's `id`. With these parameters, `RpcObject` can connect to the original object over the network, enabling invocation on the original object.

When a user calls methods or accesses attributes on a `RpcObject`, `RpcObject` will forward the request to the original object located in the agent server process through its `__getattr__` method. For synchronous method invocations (`@sync_func`) or attribute access, `RpcObject` will block the caller until the method on the original object completes execution and returns the result. In the case of asynchronous methods (`@async_func`), it immediately returns an {class}`AsyncResult<agentscope.rpc.AsyncResult>` object. The main process can continue running without blocking if it doesn't access the specific value of this object. To obtain the execution result, the `result` method of the `AsyncResult` object needs to be called, which will block the caller if the result has not yet been returned.

```{note}
When initializing `RpcObject`, if `host` and `port` parameters are not provided (i.e., sub-process mode), a new Agent Server process is started and the original object is recreated in that process. Starting a new Agent Server process is relatively slow, which is why initialization time is longer in sub-process mode.
If `host` and `port` parameters are provided (i.e., standalone process mode), `RpcObject` directly connects to the server and recreates the original object, avoiding the overhead of starting a new process.
```

### Server-Side

The server side is primarily based on gRPC and mainly consists of the `AgentServerServicer` and `RpcAgentServerLauncher` classes.

#### `AgentServerLauncher`

The implementation of `AgentServerLauncher` is located at `src/agentscope/server/launcher.py`, and it is used to launch the gRPC Server process. Specifically, to ensure that the server process can correctly reinitialize the objects sent from the client side and correctly call the model API services, it is necessary to register all subclasses of `RpcMeta` that may be used during runtime when launching the server, and properly set the model configurations. There are two ways to launch the server: through python code or command-line instructions.

- The method to launch through python code is as follows. You need to specify `host` and `port`, as well as `custom_agent_classes`, and you also need to pass the required model configurations when calling `agentscope.init`. Suppose there are custom classes `AgentA`, `AgentB`, and `AgentC` that need to be registered, and all three classes are located in the `myagents.py` file and are subclasses of `AgentBase`.

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

- The method to launch through command line is as follows. In addition to specifying `host` and `port`, you also need to specify `model_config_path` and `agent_dir`, which correspond to the model configuration file path and the directory where custom agent classes are located, respectively. When installing `agentscope`, the `as_server` command will be installed by default, so you can directly use this command in the command line.

    ```shell
    as_server start --host localhost --port 12345 --model-config-path model_config_path --agent-dir parent_dir_of_myagents.py
    ```

```{warning}
`AgentServerLauncher` will load and execute custom Python objects. Please thoroughly inspect the objects being loaded before use, as they might contain malicious code that could cause severe system damage. The `AgentServerLauncher` class also has a `local_mode` parameter indicating whether only local access is allowed. It defaults to `True`. If access from other machines is required, it should be set to `False`. To avoid network attacks, please only use it in a trusted network environment.
```

#### `AgentServerServicer`

The implementation of `AgentServerServicer` is located at `src/agentscope/server/servicer.py`. It is the implementation of the gRPC service responsible for receiving and processing various requests sent from the client side.

The `create_agent` method is called when the client uses `to_dist` on an object of a subclass of `RpcMeta`. It recreates the original object on the server and stores it in the `agent_pool` field with `id` as the key.

The `call_agent_func` method is called when the client calls methods or properties on `RpcObject` objects. The input parameters include the `id` of the object being called and the name of the method being called. The specific calling process varies slightly. For synchronous methods and property access, `call_agent_func` retrieves the object from `agent_pool`, calls the corresponding method or property, and blocks the caller until it returns the result. For asynchronous methods, `call_agent_func` packages the input parameters and places them in a task queue, immediately returning the task's `task_id` to avoid blocking the caller.

The `AgentServerServicer` has an executor pool to automatically execute tasks (`_process_task`). The results of these tasks are then placed into a `result_pool`. The `result` method of `AsyncResult` attempts to fetch the corresponding task result from the `result_pool`. If the task result does not exist, it will block the caller until the result is available.

##### `executor`

The executor is a thread pool (`concurrent.futures.ThreadPoolExecutor`), with the number of threads determined by the `capacity` parameter. The setting of `capacity` greatly impacts performance and needs to be tailored based on specific tasks.
To enable concurrent execution of various agents within the server, it is best to ensure that the `capacity` is greater than the number of agents running simultaneously in `AgentServerServicer`. Otherwise, this may lead to exponential increases in execution time, or even deadlocks in certain scenarios (such as recursive calls among multiple agents).

The `capacity` parameter can be specified in the `as_server` command via `--capacity`, or directly during the initialization of `RpcAgentServerLauncher`.

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
as_server start --host localhost --port 12345 --model-config-path model_config_path --agent-dir parent_dir_of_myagents --capacity 10
```

##### `result_pool`

The `ResultPool` implementation is located in `src/agentscope/server/async_result_pool.py` and is used for managing the execution results of asynchronous methods. There are currently two implementations: `local` and `redis`. The `local` implementation is based on Python's dictionary type (`dict`), whereas the `redis` implementation is based on Redis. Both implementations include automatic deletion mechanisms to prevent results from consuming too much memory. The `local` implementation allows for timeout-based deletion (`max_expire_time`) or deletion when a certain number of items is exceeded (`max_len`), while the `redis` implementation only supports timeout-based deletion (`max_expire_time`).
During the startup of `AgentServerLauncher`, you can specify which implementation to use by passing in the `pool_type` parameter, with the default being `local`.
If `redis` is specified, you must also provide the `redis_url`. Below are examples of code and command-line usage.

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
as_server start --host localhost --port 12345 --model-config-path model_config_path --agent-dir parent_dir_of_myagents --pool-type redis --redis-url redis://localhost:6379 --max-expire-time 7200
```

[[Back to the top]](#208-distribute-en)
