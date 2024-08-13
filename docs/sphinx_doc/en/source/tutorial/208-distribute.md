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
You can run the following code on `Machine1`.Before running, make sure that the machine has access to all models that used in your application, specifically, you need to put your model config file in `model_config_path_a` and set environment variables such as your model API key correctly in `Machine1`. The example model config file instances are located under `examples/model_configs_template`. In addition, your customized agent classes that need to run in the server must be registered in `custom_agent_classes` so that the server can correctly identify these agents. If you only use AgentScope's built-in agents, you can ignore `custom_agent_classes` field.

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
    custom_agent_classes=[AgentA, AgentB] # register your customized agent classes
)

# Start the service
server.launch()
server.wait_until_terminate()
```

For simplicity, you can run the following command in your terminal rather than the above code:

```shell
as_server --host ip_a --port 12001 --model-config-path model_config_path_a  --agent-dir parent_dir_of_agent_a_and_b
```

> Note:
> The `--agent-dir` field is used to specify the directory where your customized agent classes are located.
> Please make sure that all custom Agent classes are located in `--agent-dir`, and that the custom modules they depend on are also located in the directory.
> Additionally, because the above command will load all Python files in the directory, please ensure that the directory does not contain any malicious files to avoid security risks.

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
    custom_agent_classes=[AgentA, AgentB] # register your customized agent classes
)

# Start the service
server.launch()
server.wait_until_terminate()
```

> Similarly, you can run the following command in your terminal to setup the agent server:
>
> ```shell
> as_server --host ip_b --port 12002 --model-config-path model_config_path_b --agent-dir parent_dir_of_agent_a_and_b
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

### Step 2: Orchestrate Distributed Application Flow

> Note:
> Currently, distributed version of Agent only supports `__call__` method call (i.e. `agent(x)`), not support calling other methods or reading/writing properties.

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

### Advanced Usage

#### `to_dist` with lower cost

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

Compared with the original `to_dist()` function call, this method just initializes the agent once in the agent server process, which reduces the cost of initialization.

#### Manage your agent server processes

When running large-scale multi-agent applications, it's common to have multiple Agent Server processes running. To facilitate management of these processes, AgentScope offers management interfaces in the {class}`RpcAgentClient<agentscope.rpc.RpcAgentClient>` class. Here's a brief overview of these methods:

- `is_alive`: This method checks whether the Agent Server process is still running.

    ```python
        client = RpcAgentClient(host=server_host, port=server_port)
        if client.is_alive():
            do_something()
    ```

- `stop`: This method stops the Agent Server process.

    ```python
        client.stop()
        assert(client.is_alive() == False)
    ```

- `get_agent_list`: This method retrieves a list of JSON format thumbnails of all agents currently running within the Agent Server process. The thumbnail is generated by the `__str__` method of the Agent instance.

    ```python
        agent_list = client.get_agent_list()
        print(agent_list)  # [agent1_info, agent2_info, ...]
    ```

- `get_agent_memory`: With this method, you can fetch the memory content of an agent specified by its `agent_id`.

    ```python
        agent_id = my_agent.agent_id
        agent_memory = client.get_agent_memory(agent_id)
        print(agent_memory) # [msg1, msg2, ...]
    ```

- `get_server_info`：This method provides information about the resource utilization of the Agent Server process, including CPU usage, memory consumption.

    ```python
        server_info = client.get_server_info()
        print(server_info)  # { "cpu": xxx, "mem": xxx }
    ```

- `set_model_configs`: This method set the specific model configs into the agent server, the agent created later can directly use these model configs.

    ```python
        agent = MyAgent(  # failed because the model config [my_openai] is not found
            # ...
            model_config_name="my_openai",
            to_dist={
                # ...
            }
        )
        client.set_model_configs([{  # set the model config [my_openai]
            "config_name": "my_openai",
            "model_type": "openai_chat",
            # ...
        }])
        agent = MyAgent(  # success
            # ...
            model_config_name="my_openai",
            to_dist={
                # ...
            }
        )
    ```

- `delete_agent`: This method deletes an agent specified by its `agent_id`.

    ```python
        agent_id = agent.agent_id
        ok = client.delete_agent(agent_id)
    ```

- `delete_all_agent`: This method deletes all agents currently running within the Agent Server process.

    ```python
        ok = client.delete_all_agent()
    ```

#### Connecting to AgentScope Studio

The agent server process can be connected to [AgentScope Studio](#209-gui-en) at startup, allowing the `to_dist` method in subsequent distributed applications to be assigned automatically by Studio without the need for any parameters.

For scenarios where the agent server process is started using Python code, simply fill in the `studio_url` in the initialization parameters of `RpcAgentServerLauncher`. This requires that the URL is correct and accessible over the network, for example, the default URL for the Studio is `http://127.0.0.1:5000`.

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
    custom_agent_classes=[...], # register your customized agent classes
    studio_url="http://studio_ip:studio_port",  # connect to AgentScope Studio
)

# Start the service
server.launch()
server.wait_until_terminate()
```

For scenarios using the command `as_server` in your command line, simply fill in the `--studio-url` parameter.

```shell
as_server --host ip_a --port 12001 --model-config-path model_config_path_a --agent-dir parent_dir_of_agent_a_and_b --studio-url http://studio_ip:studio_port
```

After executing the above code or command, you can enter the Server Manager page of AgentScope Studio to check if the connection is successful. If the connection is successful, the agent server process will be displayed in the page table, and you can observe the running status and resource occupation of the process in the page, then you can use the advanced functions brought by AgentScope Studio. This section will focus on the impact of `to_dist` method brought by AgentScope Studio, and please refer to [AgentScope Studio](#209-gui-en) for the specific usage of the page.

After the agent server process successfully connects to Studio, you only need to pass the `studio_url` of this Studio in the `agentscope.init` method, and then the `to_dist` method no longer needs to fill in the `host` and `port` fields, but automatically select an agent server process that has been connected to Studio.

```python
# import some packages

agentscope.init(
    model_configs=model_config_path_a,
    studio_url="http://studio_ip:studio_port",
)

a = AgentA(
    name="A"
    # ...
).to_dist() # automatically select an agent server

# your application code
```

> Note:
>
> - The Agent used in this method must be registered at the start of the agent server process through `custom_agent_classes` or `--agent-dir`.
> - When using this method, make sure that the agent server process connected to Studio is still running normally.

After the application starts running, you can observe in the Server Manager page of Studio which agent server process this Agent is specifically running on, and after the application is completed, you can also delete this Agent through the Server Manager page.

## Implementation

### Actor Model

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

Specifically, `B` and `C` can start execution simultaneously after receiving the message from `A`, and `E` can run immediately without waiting for `A`, `B`, `C`, and `D`.
By implementing each Agent as an Actor, an Agent will automatically wait for its input `Msg` before starting to execute the `reply` method, and multiple Agents can also automatically execute `reply` at the same time if their input messages are ready, which avoids complex parallel control and makes things simple.

### PlaceHolder

Meanwhile, to support centralized application orchestration, AgentScope introduces the concept of {class}`Placeholder<agentscope.message.PlaceholderMessage>`.
A Placeholder is a special message that contains the address and port number of the agent that generated the placeholder, which is used to indicate that the output message of the Agent is not ready yet.
When calling the `reply` method of a distributed agent, a placeholder is returned immediately without blocking the main process.
The interface of placeholder is exactly the same as the message, so that the orchestration flow can be written in a centralized way.
When getting values from a placeholder, the placeholder will send a request to get the real values from the source agent.
A placeholder itself is also a message, and it can be sent to other agents, and let other agents to get the real values, which can avoid sending the real values multiple times.

About more detailed technical implementation solutions, please refer to our [paper](https://arxiv.org/abs/2402.14034).

### Agent Server

In agentscope, the agent server provides a running platform for various types of agents.
Multiple agents can run in the same agent server and hold independent memory and other local states but they will share the same computation resources.

After installing the distributed version of AgentScope, you can use the `as_server` command to start the agent server, and the detailed startup arguments can be found in the documentation of the {func}`as_server<agentscope.server.launcher.as_server>` function.

As long as the code is not modified, an agent server can provide services for multiple main processes.
This means that when running mutliple applications, you only need to start the agent server for the first time, and it can be reused subsequently.

[[Back to the top]](#208-distribute-en)
