(103-example)=

# Getting Started with a Simple Example

AgentScope is a versatile platform for building and running multi-agent applications. We provide various pre-built examples that will help you quickly understand how to create and use multi-agent for various applications. In this tutorial, you will learn how to set up a **simple agent-based interaction**.

## Step1: Prepare Model Configs

Agent is the basic composition and communication unit in AgentScope. To initialize a model-based agent, you need to prepare your configs for avaliable models. AgentScope supports a variety of APIs for pre-trained models. Here is a table outlining the supported APIs and the type of arguments required for each:

|   Model Usage               | Model Type Argument in AgentScope | Supported APIs                                                              |
| --------------------------- | --------------------------------- |-----------------------------------------------------------------------------|
| Text generation             | `openai`                          | Standard *OpenAI* chat API, FastChat and vllm                               |
| Image generation            | `openai_dall_e`                   | *DALL-E* API for generating images                                          |
| Embedding                   | `openai_embedding`                | API for text embeddings                                                     |
| General usages in POST      | `post_api`                        | *Huggingface* and *ModelScope* Inference API, and other customized post API |

Each API has its specific configuration requirements. For example, to configure an OpenAI API, you would need to fill out the following fields in the model config in a dict, a yaml file or a json file:

```python
model_config = {
    "config_name": "{config_name}", # A unique name for the model config.
    "model_type": "openai",         # Choose from "openai", "openai_dall_e", or "openai_embedding".
    "model_name": "{model_name}",   # The model identifier used in the OpenAI API, such as "gpt-3.5-turbo", "gpt-4", or "text-embedding-ada-002".
    "api_key": "xxx",               # Your OpenAI API key. If unset, the environment variable OPENAI_API_KEY is used.
    "organization": "xxx",          # Your OpenAI organization ID. If unset, the environment variable OPENAI_ORGANIZATION is used.
}
```

For open-source models, we support integration with various model interfaces such as HuggingFace, ModelScope, FastChat, and vllm. You can find scripts on deploying these services in the `scripts` directory, and we defer the detailed instructions to [[Using Different Model Sources with Model API]](203-model).

You can register your configuration by calling AgentScope's initilization method as follow. Besides, you can also load more than one config by calling init mutliple times.

```python
import agentscope

# init once by passing a list of config dict
openai_cfg_dict = {...dict_filling...}
modelscope_cfg_dict = {...dict_filling...}
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

**NOTE**: Please refer to [[Customizing Your Custom Agent with Agent Pool]](201-agent) for all available agents.

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

For more details about how to utilize pipelines for complex agent interactions, please refer to [[Agent Interactions: Dive deeper into Pipelines and Message Hub]](202-pipeline).

[[Return to the top]](#getting-started-with-a-simple-example)
