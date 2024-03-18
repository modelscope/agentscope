(103-start-en)=

# Quick Start

AgentScope is designed with a flexible communication mechanism.
In this tutorial, we will introduce the basic usage of AgentScope via a
simple standalone conversation between two agents (e.g. user and assistant
agents).

## Step1: Prepare Model

AgentScope decouples the deployment and invocation of models to better build multi-agent applications.

In terms of model deployment, users can use third-party model services such
as OpenAI API, Google Gemini API, HuggingFace/ModelScope Inference API, or
quickly deploy local open-source model services through the [scripts](https://github.com/modelscope/agentscope/blob/main/scripts/README.md) in
the repository.

While for model invocation, users should prepare a model configuration to specify the model service. Taking OpenAI Chat API as an example, the model configuration is like this:

```python
model_config = {
    "config_name": "{config_name}", # A unique name for the model config.
    "model_type": "openai",         # Choose from "openai", "openai_dall_e", or "openai_embedding".

    "model_name": "{model_name}",   # The model identifier used in the OpenAI API, such as "gpt-3.5-turbo", "gpt-4", or "text-embedding-ada-002".
    "api_key": "xxx",               # Your OpenAI API key. If unset, the environment variable OPENAI_API_KEY is used.
    "organization": "xxx",          # Your OpenAI organization ID. If unset, the environment variable OPENAI_ORGANIZATION is used.
}
```

More details about model invocation, deployment and open-source models please refer to [Model](203-model-en) section.

After preparing the model configuration, you can register your configuration by calling the `init` method of AgentScope. Additionally, you can load multiple model configurations at once.

```python
import agentscope

# init once by passing a list of config dict
openai_cfg_dict = {
    # ...
}
modelscope_cfg_dict = {
    # ...
}
agentscope.init(model_configs=[openai_cfg_dict, modelscope_cfg_dict])
```

## Step2: Create Agents

Creating agents is straightforward in AgentScope. After initializing AgentScope with your model configurations (Step 1 above), you can then define each agent with its corresponding role and specific model.

```python
import agentscope
from agentscope.agents import DialogAgent, UserAgent

# read model configs
agentscope.init(model_configs="./openai_model_configs.json")

# Create a dialog agent and a user agent
dialogAgent = DialogAgent(name="assistant", model_config_name="gpt-4", sys_prompt="You are a helpful ai assistant")
userAgent = UserAgent()
```

**NOTE**: Please refer to [Customizing Your Own Agent](201-agent-en) for all available agents.

## Step3: Agent Conversation

"Message" is the primary means of communication between agents in AgentScope. They are Python dictionaries comprising essential fields like the actual `content` of this message and the sender's `name`. Optionally, a message can include a `url` to either a local file (image, video or audio) or website.

```python
from agentscope.message import Msg

# Example of a simple text message from Alice
message_from_alice = Msg("Alice", "Hi!")

# Example of a message from Bob with an attached image
message_from_bob = Msg("Bob", "What about this picture I took?", url="/path/to/picture.jpg")
```

To start a conversation between two agents, such as `dialog_agent` and `user_agent`, you can use the following loop. The conversation continues until the user inputs `"exit"` which terminates the interaction.

```python
x = None
while True:
    x = dialogAgent(x)
    x = userAgent(x)

    # Terminate the conversation if the user types "exit"
    if x.content == "exit":
        print("Exiting the conversation.")
        break
```

For a more advanced approach, AgentScope offers the option of using pipelines to manage the flow of messages between agents. The `sequentialpipeline` stands for sequential speech, where each agent receive message from last agent and generate its response accordingly.

```python
from agentscope.pipelines.functional import sequentialpipeline

# Execute the conversation loop within a pipeline structure
x = None
while x is None or x.content != "exit":
  x = sequentialpipeline([dialog_agent, user_agent])
```

For more details about how to utilize pipelines for complex agent interactions, please refer to [Pipeline and MsgHub](202-pipeline-en).

[[Return to the top]](#103-start-en)
