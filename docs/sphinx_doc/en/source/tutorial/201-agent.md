(201-agent-en)=

# Customizing Your Own Agent

This tutorial helps you to understand the `Agent` in more depth and navigate through the process of crafting your own custom agent with AgentScope. We start by introducing the fundamental abstraction called `AgentBase`, which serves as the base class to maintain the general behaviors of all agents. Then, we will go through the *AgentPool*, an ensemble of pre-built, specialized agents, each designed with a specific purpose in mind. Finally, we will demonstrate how to customize your own agent, ensuring it fits the needs of your project.

## Understanding `AgentBase`

The `AgentBase` class is the architectural cornerstone for all agent constructs within the AgentScope. As the superclass of all custom agents, it provides a comprehensive template consisting of essential attributes and methods that underpin the core functionalities of any conversational agent.

Each AgentBase derivative is composed of several key characteristics:

* `memory`: This attribute enables agents to retain and recall past interactions, allowing them to maintain context in ongoing conversations. For more details about `memory`, we defer to [Memory and Message Management](205-memory).

* `model`: The model is the computational engine of the agent, responsible for making a response given existing memory and input. For more details about `model`, we defer to [Using Different Model Sources with Model API](#203-model).

* `sys_prompt` & `engine`: The system prompt acts as predefined instructions that guide the agent in its interactions; and the `engine` is used to dynamically generate a suitable prompt. For more details about them, we defer to [Prompt Engine](206-prompt).

In addition to these attributes, `AgentBase` endows agents with pivotal methods such as `observe` and `reply`:

* `observe()`: Through this method, an agent can take note of *message* without immediately replying, allowing it to update its memory based on the observed *message*.
* `reply()`: This is the primary method that developers must implement. It defines the agent's behavior in response to an incoming *message*, encapsulating the logic that results in the agent's output.

Besides, for unified interfaces and type hints, we introduce another base class `Operator`, which indicates performing some operation on input data by the `__call__` function. And we make `AgentBase` a subclass of `Operator`.

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

## Exploring the AgentPool

The *AgentPool* within AgentScope is a curated ensemble of ready-to-use, specialized agents. Each of these agents is tailored for a distinct role and comes equipped with default behaviors that address specific tasks. The *AgentPool* is designed to expedite the development process by providing various templates of `Agent`.

Below is a table summarizing the functionality of some of the key agents available in the Agent Pool:

| Agent Type     | Description                                                  | Typical Use Cases                                            |
| -------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `AgentBase`    | Serves as the superclass for all agents, providing essential attributes and methods. | The foundation for building any custom agent.                |
| `DialogAgent`  | Manages dialogues by understanding context and generating coherent responses. | Customer service bots, virtual assistants.                   |
| `UserAgent`    | Interacts with the user to collect input, generating messages that may include URLs or additional specifics based on required keys. | Collecting user input for agents                             |
| *More to Come* | AgentScope is continuously expanding its pool with more specialized agents for diverse applications. |                                                              |

## Customizing Agents from the AgentPool

Customizing an agent from AgentPool enables you to tailor its functionality to meet the unique demands of your multi-agent application. You have the flexibility to modify existing agents with minimal effort by **adjusting configurations** and prompts or, for more extensive customization, you can engage in secondary development.

Below, we provide usages of how to configure various agents from the AgentPool:

### `DialogAgent`

* **Reply Method**: The `reply` method is where the main logic for processing input *message* and generating responses.

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
    self.memory.add(msg)
    return msg
```

* **Usages:** To tailor a `DialogAgent` for a customer service bot:

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

* **Reply Method**: This method processes user input by prompting for content and if needed, additional keys and a URL. The gathered data is stored in a *message* object in the agent's memory for logging or later use and returns the message as a response.

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

* **Usages:** To configure a `UserAgent` for collecting user input and URLs (of file, image, video, audio , or website):

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

[[Return to the top]](#201-agent-en)
