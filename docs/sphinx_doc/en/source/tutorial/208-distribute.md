(208-distribute-en)=

# Distribution

AgentScope implements an Actor-based distributed deployment and parallel optimization, providing the following features:

- **Automatic Parallel Optimization**: Automatically optimize the application for parallelism at runtime without additional optimization costs;
- **Centralized Application Writing**: Easily orchestrate distributed application flow without distributed background knowledge;
- **Zero-Cost Automatic Migration**: Centralized Multi-Agent applications can be easily converted to distributed mode

This tutorial will introduce the implementation and usage of AgentScope distributed in detail.

## Usage

In AgentScope, the process that runs the application flow is called the "main process", and all agents will run in separate processes.
According to the different relationships between the main process and the agent process, AgentScope supports two distributed modes: Master-Slave and Peer-to-Peer mode.
In the Master-Slave mode, developers can start all agent processes from the main process, while in the Peer-to-Peer mode, the agent process is independent of the main process and developers need to start the agent service on the corresponding machine.

The above concepts may seem complex, but don't worry, for application developers, they only have minor differences when creating agents. Below we introduce how to create distributed agents.

### Step 1: Create a Distributed Agent

First, the developer's agent must inherit the `agentscope.agents.AgentBase` class. `AgentBase` provides the `to_dist` method to convert the agent into its distributed version. `to_dist` mainly relies on the following parameters to implement the distributed deployment of the agent:

- `host`: the hostname or IP address of the machine where the agent runs, defaults to `localhost`.
- `port`: the port of this agent's RPC server, defaults to `80`.
- `launch_server`: whether to launch an RPC server locally, defaults to `True`.

Suppose there are two agent classes `AgentA` and `AgentB`, both of which inherit from `AgentBase`.

#### Master-Slave Mode

In the Master-Slave mode, since all agent processes depend on the main process, all processes actually run on the same machine.
We can start all agent processes from the main process, that is, the default parameters `launch_server=True` and `host="localhost"`, and we can omit the `port` parameter. AgentScope will automatically find an available local port for the agent process.

```python
a = AgentA(
    name="A"
    # ...
).to_dist()
```

#### Peer-to-Peer Mode

In the Peer-to-Peer mode, we need to start the service of the corresponding agent on the target machine first. For example, deploy an instance of `AgentA` on the machine with IP `a.b.c.d`, and its corresponding port is 12001. Run the following code on this target machine:

```python
from agentscope.agents import RpcAgentServerLauncher

# Create an agent service process
server_a = RpcAgentServerLauncher(
    agent_class=AgentA,
    agent_kwargs={
        "name": "A"
        ...
    },
    host="a.b.c.d",
    port=12001,
)

# Start the service
server_a.launch()
server_a.wait_until_terminate()
```

Then, we can connect to the agent service in the main process with the following code. At this time, the object `a` created in the main process can be used as a local proxy for the agent, allowing developers to write the application flow in a centralized way in the main process.

```python
a = AgentA(
    name="A",
    # ...
).to_dist(
    host="a.b.c.d",
    port=12001,
    launch_server=False,
)
```

### Step 2: Orchestrate Distributed Application Flow

In AgentScope, the orchestration of distributed application flow is exactly the same as non-distributed programs, and developers can write the entire application flow in a centralized way.
At the same time, AgentScope allows the use of a mixture of locally and distributed deployed agents, and developers do not need to distinguish which agents are local and which are distributed.

The following is the complete code for two agents to communicate with each other in different modes. It can be seen that AgentScope supports zero-cost migration of distributed application flow from centralized to distributed.

- All agents are centralized:

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

- Agents are deployed in a distributed manner (Master-Slave mode):

```python
# Create agent objects
a = AgentA(
    name="A"
    # ...
).to_dist()

b = AgentB(
    name="B",
    # ...
).to_dist()

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

[[Back to the top]](#208-distribute-en)
