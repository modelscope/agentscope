(208-distribute)=

# Make Your Applications Distributed

AgentScope is designed to be fully distributed, agent instances in one application can be deployed on different machines and run in parallel. This tutorial will introduce the features of AgentScope distributed and the distributed deployment method.

## Features

### Every agent is an "Actor"

[The actor model](https://en.wikipedia.org/wiki/Actor_model) is a popular concept in concurrent programming and adopted by AgentScope. Every agent is an actor and interacts with other agents through messages. The flow of messages implies the execution order of the agent. Each agent has a `reply` method that consumes a message and generates another message, and the generated message can be sent to other agents. For example, the figure below shows the workflow of multiple agents. `A` to `F` are all agents, and the arrows represent messages.

```{mermaid}
graph LR;
A-->B
A-->C
B-->D
C-->D
E-->F
D-->F
```

Among them, `B` and `C` can start execution simultaneously after receiving the message from `A`, and `E` can run immediately without waiting for `A`, `B`, `C,` and `D`.
By implementing each agent as an actor, an agent will automatically wait for its input `Msg` before starting to execute the reply method, and multiple agents can also automatically execute `reply` at the same time if their input messages are ready, which avoids complex parallel control and makes things simple.

### Write centrally, run distributedly

In AgentScope, agents can be started as separate processes on the same or different machines. However, application developers do not need to pay attention to where these agents are running; you only need to write application code in the main process using the procedural programming paradigm. AgentScope will help you convert the task into a distributed version. The following is a piece of application code: `A`, `B`, and `C` are running on different machines.

```
x = A()
y = B(x)
z = C(x)
```

Although this code appears to be executed completely sequentially, AgentScope will **automatically detect potential parallelism** in your code as shown in the flow graph below, which means `C` will not wait for `B` to complete before starting execution.

```{mermaid}
graph LR;
A-->B
A-->C
```

## Easy Distributed Deployment

Please follow the steps below to deploy your application distributedly.

### Convert your agents

`AgentBase` provided the `to_dist` method to convert the agent into a distributed version.
`to_dist` requires several parameters.

- `host`: the hostname or IP address of the machine where the agent runs, defaults to `localhost`.
- `port`: the port of this agent's RPC server, defaults to `80`.
- `launch_server`: whether to launch an RPC server locally, defaults to `True`.
- `local_mode`: set to `True` if all agents run on the same machine, defaults to `True`.
- `lazy_launch`:  if set to `True`, only launch the server when the agent is called.

> The `to_dist` method is implemented based on [gRPC](https://grpc.io/). When 'launch_server' is set to `True`, it will start a gRPC server process, and the original agent will be transferred to the new process to run.

### Run in multi-process mode

AgentScope supports deployment in multi-process mode, where each agent is a sub-process of the application's main process, and all agents run on the same machine.
The usage is exactly the same as single process mode, and you only need to call the `to_dist` method after initialization.

Suppose you have classes `A` and `B`, both of which inherit from `AgentBase`.

```python
# import packages

a = A(
    name="A",
    ...,
).to_dist()
b = B(
    name="B",
    ...,
).to_dist()

x = None
while x is None or x.content != 'exit':
    x = a(x)
    x = b(x)
```

### Run on multiple machines

AgentScope also supports to run agents on multiple machines. In this case, you need to start agents separately. For example, you can use the following code to start agent `A` on the machine with IP address `ip_a`.

```python
# import packages

server_a = RpcAgentServerLauncher(
    agent_class=A,
    agent_kwargs={
        "name": "A"
        ...
    },
    host=ip_a,
    port=12001,
)
server_a.launch()
server_a.wait_until_terminate()
```

Similarly, you can start agent `B` on the machine with IP address `ip_b`.
Please make sure that the two machines can access each other using the IP addresses.

```python
# import packages

server_b = RpcAgentServerLauncher(
    agent_class=B,
    agent_kwargs={
        "name": "B",
        ...
    },
    host=ip_b,
    port=12001,
)
server_b.launch()
server_b.wait_until_terminate()
```

Then, you can run the application's main process on any machine that can access `ip_a` and `ip_b`.

```python
# import packages

a = A(
    name="A",
    ...
).to_dist(
    host=ip_a,
    port=12001,
    launch_server=False,
)
b = B(
    name="B",
    ...
).to_dist(
    host=ip_b,
    port=12002,
    launch_server=False,
)

x = None
while x is None or x.content != 'exit':
    x = a(x)
    x = b(x)
```

[[Return to the top]](#make-your-applications-distributed)
