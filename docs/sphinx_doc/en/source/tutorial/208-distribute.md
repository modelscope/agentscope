(208-distribute-en)=

# Distribution

AgentScope implements an Actor-based distributed deployment and parallel optimization, providing the following features:

- **Automatic Parallel Optimization**: Automatically optimize the application for parallelism at runtime without additional optimization costs;
- **Centralized Application Writing**: Easily orchestrate distributed application flow without distributed background knowledge;
- **Zero-Cost Automatic Migration**: Centralized Multi-Agent applications can be easily converted to distributed mode

This tutorial will introduce the implementation and usage of AgentScope distributed in detail.

## Usage

In AgentScope, the process that runs the application flow is called the **main process**, and each agent can run in a separate process named **agent server process**.
According to the different relationships between the main process and the agent server process, AgentScope supports two modes for each agent: **Child Process** and **Independent Process** mode.

- In the Child Process Mode, agent server processes will be automatically started as sub-processes from the main process.
- While in the Independent Process Mode, the agent server process is independent of the main process and developers need to start the agent server process on the corresponding machine.

The above concepts may seem complex, but don't worry, for application developers, you only need to convert your existing agent to its distributed version.

### Step 1: Convert your agent to its distributed version

All agents in AgentScope can automatically convert to its distributed version by calling its {func}`to_dist<agentscope.agents.AgentBase.to_dist>` method.
But note that your agent must inherit from the {class}`agentscope.agents.AgentBase<agentscope.agents.AgentBase>` class, because the `to_dist` method is provided by the `AgentBase` class.

Suppose there are two agent classes `AgentA` and `AgentB`, both of which inherit from `AgentBase`.

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

Next we will introduce the conversion details of both modes.

#### Child Process Mode

To use this mode, you only need to call each agent's `to_dist()` method without any input parameter. AgentScope will automatically start all agent server processes from the main process.

```python
# Child Process mode
a = AgentA(
    name="A"
    # ...
).to_dist()
b = AgentB(
    name="B"
    # ...
).to_dist()
```

#### Independent Process Mode

In the Independent Process Mode, we need to start the agent server process on the target machine first.
When starting the agent server process, you need to specify a model config file, which contains the models which can be used in the agent server, the IP address and port of the agent server process
For example, start two agent server processes on the two different machines with IP `ip_a` and `ip_b`(called `Machine1` and `Machine2` accrodingly).
You can run the following code on `Machine1`.Before running, make sure that the machine has access to all models that used in your application, specifically, you need to put your model config file in `model_config_path_a` and set environment variables such as your model API key correctly in `Machine1`. The example model config file instances are located under `examples/model_configs_template`.

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

> For similarity, you can run the following command in your terminal rather than the above code:
>
> ```shell
> as_server --host ip_a --port 12001 --model-config-path model_config_path_a
> ```

Then put your model config file accordingly in `model_config_path_b`, set environment variables, and run the following code on `Machine2`.

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

> Similarly, you can run the following command in your terminal to setup the agent server:
>
> ```shell
> as_server --host ip_b --port 12002 --model-config-path model_config_path_b
> ```

Then, you can connect to the agent servers from the main process with the following code.

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

The above code will deploy `AgentA` on the agent server process of `Machine1` and `AgentB` on the agent server process of `Machine2`.
And developers just need to write the application flow in a centralized way in the main process.

#### Advanced Usage of `to_dist`

All examples described above convert initialized agents into their distributed version through the {func}`to_dist<agentscope.agents.AgentBase.to_dist>` method, which is equivalent to initialize the agent twice, once in the main process and once in the agent server process.
For agents whose initialization process is time-consuming, the `to_dist` method is inefficient. Therefore, AgentScope also provides a method to convert the Agent instance into its distributed version while initializing it, that is, passing in `to_dist` parameter to the Agent's initialization function.

In Child Process Mode, just pass `to_dist=True` to the Agent's initialization function.

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

In Independent Process Mode, you need to encapsulate the parameters of the `to_dist()` method in  {class}`DistConf<agentscope.agents.DistConf>` instance and pass it into the `to_dist` field, for example:

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

Compared with the original `to_dist()` function call, this method just initializes the agent once in the agent server process.

### Step 2: Orchestrate Distributed Application Flow

In AgentScope, the orchestration of distributed application flow is exactly the same as non-distributed programs, and developers can write the entire application flow in a centralized way.
At the same time, AgentScope allows the use of a mixture of locally and distributed deployed agents, and developers do not need to distinguish which agents are local and which are distributed.

The following is the complete code for two agents to communicate with each other in different modes. It can be seen that AgentScope supports zero-cost migration of distributed application flow from centralized to distributed.

- All agents are centralized

```python
# Create agent objects
a = AgentA(
    name="A",
    # ...
)

b = AgentB(
    name="B",
    # ...
)

# Application flow orchestration
x = None
while x is None or x.content == "exit":
    x = a(x)
    x = b(x)
```

- Agents are deployed in a distributed manner
  - `AgentA` in Child Process mode
  - `AgentB` in Independent Process Mode

```python
# Create agent objects
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

# Application flow orchestration
x = None
while x is None or x.content == "exit":
    x = a(x)
    x = b(x)
```

### About Implementation

#### Actor Model

[The Actor model](https://en.wikipedia.org/wiki/Actor_model) is a widely used programming paradigm in large-scale distributed systems, and it is also applied in the distributed design of the AgentScope platform.

In the distributed mode of AgentScope, each Agent is an Actor and interacts with other Agents through messages. The flow of messages implies the execution order of the Agents. Each Agent has a `reply` method, which consumes a message and generates another message, and the generated message can be sent to other Agents. For example, the following chart shows the workflow of multiple Agents. `A`~`F` are all Agents, and the arrows represent messages.

```{mermaid}
graph LR;
A-->B
A-->C
B-->D
C-->D
E-->F
D-->F
```

Specifically, `B` and `C` can start execution simultaneously after receiving the message from `A`, and `E` can run immediately without waiting for `A`, `B`, `C,` and `D`.
By implementing each Agent as an Actor, an Agent will automatically wait for its input `Msg` before starting to execute the `reply` method, and multiple Agents can also automatically execute `reply` at the same time if their input messages are ready, which avoids complex parallel control and makes things simple.

#### PlaceHolder

Meanwhile, to support centralized application orchestration, AgentScope introduces the concept of {class}`Placeholder<agentscope.message.PlaceholderMessage>`.
A Placeholder is a special message that contains the address and port number of the agent that generated the placeholder, which is used to indicate that the output message of the Agent is not ready yet.
When calling the `reply` method of a distributed agent, a placeholder is returned immediately without blocking the main process.
The interface of placeholder is exactly the same as the message, so that the orchestration flow can be written in a centralized way.
When getting values from a placeholder, the placeholder will send a request to get the real values from the source agent.
A placeholder itself is also a message, and it can be sent to other agents, and let other agents to get the real values, which can avoid sending the real values multiple times.

About more detailed technical implementation solutions, please refer to our [paper](https://arxiv.org/abs/2402.14034).

#### Agent Server

In agentscope, the agent server provides a running platform for various types of agents.
Multiple agents can run in the same agent server and hold independent memory and other local states but they will share the same computation resources.

After installing the distributed version of AgentScope, you can use the `as_server` command to start the agent server, and the detailed startup arguments can be found in the documentation of the {func}`as_server<agentscope.server.launcher.as_server>` function.

As long as the code is not modified, an agent server can provide services for multiple main processes.
This means that when running mutliple applications, you only need to start the agent server for the first time, and it can be reused subsequently.

[[Back to the top]](#208-distribute-en)
