(208-distribute-en)=

# Distribution

AgentScope implements an Actor-based distributed deployment and parallel optimization, providing the following features:

- **Automatic Parallel Optimization**: Automatically optimize the application for parallelism at runtime without additional optimization costs;
- **Centralized Application Writing**: Easily orchestrate distributed application flow without distributed background knowledge;
- **Zero-Cost Automatic Migration**: Centralized Multi-Agent applications can be easily converted to distributed mode

This tutorial will introduce the implementation and usage of AgentScope distributed in detail.

## Usage

In AgentScope, the process that runs the application flow is called the "main process", and each agent can run in a separate process named "agent server process".
According to the different relationships between the main process and the agent server process, AgentScope supports two modes for each agent: **Subprocess** and **Standalone** mode.
In the Subprocess mode, agent server processes will be automatically started from the main process, while in the Standalone mode, the agent server process is independent of the main process and developers need to start the agent server process on the corresponding machine.

The above concepts may seem complex, but don't worry, for application developers, you only need to convert your existing agent to its distributed version.

### Step 1: Convert your agent to its distributed version

All agents in AgentScope can automatically convert to its distributed version by calling its `to_dist` method.
But note that your agent must inherit from the `agentscope.agents.AgentBase` class, because the `to_dist` method is provided by the `AgentBase` class.

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

#### Subprocess Mode

To use this mode, you only need to call each agent's `to_dist()` method without any input parameter. AgentScope will automatically start all agent server processes from the main process.

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

#### Standalone Mode

In the Standalone mode, we need to start the agent server process on the target machine first.
For example, start two agent server processes on the two different machines with IP `a.b.c.d` and `e.f.g.h`(called `Machine1` and `Machine2` accrodingly).
You can run the following code on `Machine1`:

```python
# import some packages

agentscope.init(
    ...
)
# Create an agent service process
server = RpcAgentServerLauncher(
    host="a.b.c.d",
    port=12001,  # choose an available port
)

# Start the service
server.launch()
server.wait_until_terminate()
```

And run the following code on `Machine2`:

```python
# import some packages

agentscope.init(
    ...
)
# Create an agent service process
server = RpcAgentServerLauncher(
    host="e.f.g.h",
    port=12002, # choose an available port
)

# Start the service
server.launch()
server.wait_until_terminate()
```

Then, you can connect to the agent servers from the main process with the following code.

```python
a = AgentA(
    name="A",
    # ...
).to_dist(
    host="a.b.c.d",
    port=12001,
    launch_server=False,
)
b = AgentB(
    name="B",
    # ...
).to_dist(
    host="e.f.g.h",
    port=12002,
    launch_server=False,
)
```

The above code will deploy `AgentA` on the agent server process of `Machine1` and `AgentB` on the agent server process of `Machine2`.
And developers just need to write the application flow in a centralized way in the main process.

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
  - `AgentA` in Subprocess mode
  - `AgentB` in Standalone mode

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
    host="e.f.g.h",
    port=12002,
    launch_server=False,
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

Meanwhile, to support centralized application orchestration, AgentScope introduces the concept of Placeholder. A Placeholder is a special message that contains the address and port number of the agent that generated the Placeholder, which is used to indicate that the input message of the Agent is not ready yet.
When the input message of the Agent is ready, the Placeholder will be replaced by the real message, and then the actual `reply` method will be executed.

About more detailed technical implementation solutions, please refer to our [paper](https://arxiv.org/abs/2402.14034).

#### Agent Server

In agentscope, the agent server provides a running platform for various types of agents.
Multiple agents can run in the same agent server and hold independent memory and other local states but they will share the same computation resources.
As long as the code is not modified, an agent server can provide services for multiple main processes.
This means that when running mutliple applications, you only need to start the agent server for the first time, and it can be reused subsequently.

[[Back to the top]](#208-distribute-en)
