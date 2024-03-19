(201-agent-zh)=

# 定制你自己的Agent

本教程帮助你更深入地理解Agent，并引导你通过使用AgentScope定制自己的自定义agent。
我们首先介绍一个称为AgentBase的基本抽象概念，它作为基类维护所有agent的通用行为。然后，我们将探讨AgentPool，这是一个由预构建的、专门化的agent组成的集合，每个agent都设计有特定的目的。最后，我们将演示如何定制你自己的agent，确保它符合你项目的需求。

## 理解 `AgentBase`

`AgentBase`类是AgentScope内所有agent结构的架构基石。作为所有自定义agent的超类，它提供了一个包含基本属性和方法的综合模板，这些属性和方法支撑了任何会话agent的核心功能。

每个AgentBase的派生类由几个关键特性组成：

* `memory`（记忆）：这个属性使agent能够保留和回忆过去的互动，允许它们在持续的对话中保持上下文。关于memory的更多细节，我们会在[记忆和消息管理部分](205-memory)讨论。

* `model`（模型）：模型是agent的计算引擎，负责根据现有的记忆和输入做出响应。关于model的更多细节，我们在[使用模型API与不同模型源部分](203-model)讨论

* `sys_prompt`（系统提示）和`engine`（引擎）：系统提示作为预定义的指令，指导agent在其互动中的行为；而engine用于动态生成合适的提示。关于它们的更多细节，我们会在[提示引擎部分](206-prompt)讨论。

除了这些属性，`AgentBase` 还为agent提供了一些关键方法，如 `observe` 和 `reply`：

* `observe()`：通过这个方法，一个agent可以注意到消息而不立即回复，允许它根据观察到的消息更新它的记忆。
* `reply()`：这是开发者必须实现的主要方法。它定义了agent对于传入消息的响应行为，封装了agent输出的逻辑。

此外，为了统一接口和类型提示，我们引入了另一个基类`Operator`，它通过 `__call__` 函数表示对输入数据执行某些操作。并且我们让 `AgentBase` 成为 `Operator` 的一个子类。

```python
class AgentBase(Operator):
    # ... [code omitted for brevity]

    def __init__(
            self,
            name: str,
            sys_prompt: Optional[str] = None,
            model_config_name: str = None,
            use_memory: bool = True,
            memory_config: Optional[dict] = None,
    ) -> None:

    # ... [code omitted for brevity]
    def observe(self, x: Union[dict, Sequence[dict]]) -> None:
        # An optional method for updating the agent's internal state based on
        # messages it has observed. This method can be used to enrich the
        # agent's understanding and memory without producing an immediate
        # response.
        self.memory.add(x)

    def reply(self, x: dict = None) -> dict:
        # The core method to be implemented by custom agents. It defines the
        # logic for processing an input message and generating a suitable
        # response.
        raise NotImplementedError(
            f"Agent [{type(self).__name__}] is missing the required "
            f'"reply" function.',
        )

    # ... [code omitted for brevity]
```

## 探索AgentPool

在 AgentScope 中的 `AgentPool` 是一个经过精选的，随时可用的，专门化agent集合。这些agent中的每一个都是为了特定的角色量身定做，并配备了处理特定任务的默认行为。`AgentPool` 旨在通过提供各种 Agent 模板来加快开发过程。

以下是一个总结了 AgentPool 中一些关键agent的功能的表格：

| Agent 种类     | 描述                                               | Typical Use Cases |
|--------------|--------------------------------------------------|-------------------|
| `AgentBase`  | 作为所有agent的超类，提供了必要的属性和方法。                        | 构建任何自定义agent的基础。  |
| `DialogAgent` | 通过理解上下文和生成连贯的响应来管理对话。                            | 客户服务机器人，虚拟助手。     |
| `UserAgent`  | 与用户互动以收集输入，生成可能包括URL或基于所需键的额外具体信息的消息。            | 为agent收集用户输入      |
| *更多agent*    | AgentScope 正在不断扩大agent池，加入更多专门化的agent，以适应多样化的应用。 |                   |

## 从Agent池中定制Agent

从 AgentPool 中定制一个agent，使您能够根据您的多agent应用的独特需求来调整其功能。您可以通过调整配置和提示来轻松修改现有agent，或者，对于更广泛的定制，您可以进行二次开发

下面，我们提供了如何配置来自 AgentPool 的各种agent的用法：

### `DialogAgent`

* **回复方法**：`reply` 方法是处理输入消息和生成响应的主要逻辑所在

```python
def reply(self, x: dict = None) -> dict:
    # Additional processing steps can occur here

    if self.memory:
        self.memory.add(x)  # Update the memory with the input

    # Generate a prompt for the language model using the system prompt and memory
    prompt = self.engine.join(
        self.sys_prompt,
        self.memory and self.memory.get_memory(),
    )

    # Invoke the language model with the prepared prompt
    response = self.model(prompt).text

    # Format the response and create a message object
    msg = Msg(self.name, response)

    # Record the message to memory and return it
    if self.memory:
        self.memory.add(msg)
    return msg
```

* **用法**：为了定制一个用于客户服务机器人的 `DialogAgent`：

```python
from agentscope.agents import DialogAgent

# Configuration for the DialogAgent
dialog_agent_config = {
    "name": "ServiceBot",
    "model_config_name": "gpt-3.5",  # Specify the model used for dialogue generation
    "sys_prompt": "Act as AI assistant to interact with the others. Try to "
    "reponse on one line.\n",  # Custom prompt for the agent
    # Other configurations specific to the DialogAgent
}

# Create and configure the DialogAgent
service_bot = DialogAgent(**dialog_agent_config)
```

### `UserAgent`

* **回复方法**：这个方法通过提示内容以及在需要时附加的键和URL来处理用户输入。收集到的数据存储在agent记忆中的一个message对象里，用于记录或稍后使用，并返回该message作为响应。

```python
def reply(
    self,
    x: dict = None,
    required_keys: Optional[Union[list[str], str]] = None,
) -> dict:
    # Check if there is initial data to be added to memory
    if self.memory:
        self.memory.add(x)

    content = input(f"{self.name}: ")  # Prompt the user for input
    kwargs = {}

    # Prompt for additional information based on the required keys
    if required_keys is not None:
        if isinstance(required_keys, str):
            required_keys = [required_keys]
        for key in required_keys:
            kwargs[key] = input(f"{key}: ")

    # Optionally prompt for a URL if required
    url = None
    if self.require_url:
        url = input("URL: ")

    # Create a message object with the collected input and additional details
    msg = Msg(self.name, content=content, url=url, **kwargs)

    # Add the message object to memory
    if self.memory:
        self.memory.add(msg)

    return msg
```

* **用法**：配置一个 UserAgent 用于收集用户输入和URL（文件、图像、视频、音频或网站的URL）：

```python
from agentscope.agents import UserAgent

# Configuration for UserAgent
user_agent_config = {
    "name": "User",
    "require_url": True,  # If true, the agent will require a URL
}

# Create and configure the UserAgent
user_proxy_agent = UserAgent(**user_agent_config)
```

[[返回顶部]](#201-agent-zh)
