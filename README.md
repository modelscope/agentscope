# AgentScope

AgentScope is an innovative multi-agent platform designed to empower developers to build multi-agent applications with ease, reliability, and high performance. It features three high-level capabilities:

- **Easy-to-Use**: Programming in pure Python with various pre-built components for immediate use, suitable for developers or users with varying levels of customization requirements. Detailed documentation and examples are provided to help you get started, see our [Tutorial](https://modelscope.github.io/agentscope/).

- **High Robustness**: Supporting customized fault-tolerance controls and retry mechanisms to enhance application stability.

- **Actor-Based Distribution**: Enabling developers to build distributed multi-agent applications in a centralized programming manner for streamlined development.

Welcome to join our community on

| [Discord](https://discord.gg/eYMpfnkG8h) | DingTalk | WeChat |
|---------|----------|--------|
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i2/O1CN01tuJ5971OmAqNg9cOw_!!6000000001747-0-tps-444-460.jpg" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i3/O1CN01UyfWfx1CYBM3WqlBy_!!6000000000092-2-tps-400-400.png" width="100" height="100"> |

Table of Contents
=================

- [AgentScope](#agentscope)
- [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [From source](#from-source)
    - [Using pip](#using-pip)
  - [Quick Start](#quick-start)
    - [Basic Usage](#basic-usage)
      - [Step 1: Prepare Model Configs](#step-1-prepare-model-configs)
        - [OpenAI API Config](#openai-api-config)
        - [Post Request API Config](#post-request-api-config)
      - [Step 2: Create Agents](#step-2-create-agents)
      - [Step 3: Construct Conversation](#step-3-construct-conversation)
    - [Advanced Usage](#advanced-usage)
      - [**Pipeline** and **MsgHub**](#pipeline-and-msghub)
      - [Customize Your Own Agent](#customize-your-own-agent)
      - [Built-in Resources](#built-in-resources)
        - [Agent Pool](#agent-pool)
        - [Services](#services)
        - [Example Applications](#example-applications)
  - [License](#license)
  - [Contributing](#contributing)
  - [References](#references)

## Installation

To install AgentScope, you need to have Python 3.9 or higher installed.

**_Note: This project is currently in active development, it's recommended to install AgentScope from source._**

### From source

- Run the following commands to install AgentScope in editable mode.

```bash
# Pull the source code from github
git clone https://github.com/modelscope/agentscope.git

# Install the package in editable mode
cd AgentScope
pip install -e .
```

- Building a distributed multi-agent application relies on [gRPC](https://github.com/grpc/grpc) libraries, and you can install the required dependencies as follows.

```bash
# On windows
pip install -e .[distribute]
# On mac
pip install -e .\[distribute\]
```

### Using pip

- Use the following command to install the latest released AgentScope.

```bash
pip install AgentScope
```

## Quick Start

### Basic Usage

Taking a multi-agent application with user and assistant agent as an example, you need to take the following steps:

- [Step 1: Prepare Model Configs](#step-1-prepare-model-configs)
- [Step 2: Create Agents](#step-2-create-agents)
- [Step 3: Construct Conversation](#step-3-construct-conversation)

#### Step 1: Prepare Model Configs

AgentScope supports the following model API services:

- OpenAI Python APIs, including
  - OpenAI Chat, DALL-E and Embedding API
  - OpenAI-Compatible platforms, e.g. [FastChat](https://github.com/lm-sys/FastChat) and [vllm](https://github.com/vllm-project/vllm)
- Post request APIs, including
  - [HuggingFace](https://huggingface.co/docs/api-inference/index) and [ModelScope](https://www.modelscope.cn/docs/%E9%AD%94%E6%90%ADv1.5%E7%89%88%E6%9C%AC%20Release%20Note%20(20230428)) inference APIs
  - Customized model APIs

|                      | Model Type Argument | Support APIs                                                   |
|----------------------|---------------------|----------------------------------------------------------------|
| OpenAI Chat API      | `openai`            | Standard OpenAI Chat API, FastChat and vllm                    |
| OpenAI DALL-E API    | `openai_dall_e`     | Standard DALL-E API                                            |
| OpenAI Embedding API | `openai_embedding`  | OpenAI embedding API                                           |
| Post API             | `post_api`          | Huggingface/ModelScope inference API, and customized post API  |

##### OpenAI API Config

For OpenAI APIs, you need to prepare a dict of model config with the following fields:

```
{
    "config_name": "{config name}",             # The name to identify the config
    "model_type": "openai" | "openai_dall_e" | "openai_embedding",
    "model_name": "{model name, e.g. gpt-4}",   # The model in openai API

    # Optional
    "api_key": "xxx",                           # The API key for OpenAI API. If not set, env
                                                # variable OPENAI_API_KEY will be used.
    "organization": "xxx",                      # The organization for OpenAI API. If not set, env
                                                # variable OPENAI_ORGANIZATION will be used.
}
```

##### Post Request API Config

For post requests APIs, the config contains the following fields.

```
{
    "config_name": "{config name}",   # The name to identify the config
    "model_type": "post_api",
    "api_url": "https://xxx",         # The target url
    "headers": {                      # Required headers
      ...
    },
}
```

AgentScope provides fruitful scripts to fast deploy model services in [Scripts](./scripts/README.md).
For more details of model services, refer to our [Tutorial](https://modelscope.github.io/agentscope/index.html#welcome-to-agentscope-tutorial-hub) and [API Document](https://modelscope.github.io/agentscope/index.html#indices-and-tables).

#### Step 2: Create Agents

Create built-in user and assistant agents as follows.

```python
from agentscope.agents import DialogAgent, UserAgent
import agentscope

# Load model configs
agentscope.init(model_configs="./model_configs.json")

# Create a dialog agent and a user agent
dialog_agent = DialogAgent(name="assistant", model_config_name="your_config_name")
user_agent = UserAgent()
```

#### Step 3: Construct Conversation

In AgentScope, **message** is the bridge among agents, which is a
**dict** that contains two necessary fields `name` and `content` and an
optional field `url` to local files (image, video or audio) or website.

```python
from agentscope.message import Msg
x = Msg(name="Alice", content="Hi!")
x = Msg("Bob", "What about this picture I took?", url="/path/to/picture.jpg")
```

Start a conversation between two agents (e.g. dialog_agent and user_agent)
with the following code:

```python
x = None
while True:
  x = dialog_agent(x)
  x = user_agent(x)
  if x.content == "exit": # user input "exit" to exit the conversation
    break
```

### Advanced Usage

#### **Pipeline** and **MsgHub**

To simplify the construction of agents communication, AgentScope provides two helpful tools: **Pipeline** and **MsgHub**.

- **Pipeline**: It allows users to program a communication among agents easily. Taking a sequential pipeline as an example, the following two codes are equivalent, but pipeline is more convenient and elegant.

  - Passing message throught agent1, agent2 and agent3 **WITHOUT** pipeline:

    ```python
    x1 = agent1(input_msg)
    x2 = agent2(x1)
    x3 = agent3(x2)
    ```

  - **WITH** object-level pipeline:

    ```python
    from agentscope.pipelines import SequentialPipeline

    pipe = SequentialPipeline([agent1, agent2, agent3])
    x3 = pipe(input_msg)
    ```

  - **WITH** functional-level pipeline:

    ```python
    from agentscope.pipelines.functional import sequentialpipeline

    x3 = sequentialpipeline([agent1, agent2, agent3], x=input_msg)
    ```

- **MsgHub**: To achieve a group conversation, AgentScope provides message hub.

  - Achieving group conversation **WITHOUT** `msghub`:

    ```python
    x1 = agent1(x)
    agent2.observe(x1)  # The message x1 should be broadcast to other agents
    agent3.observe(x1)

    x2 = agent2(x1)
    agent1.observe(x2)
    agent3.observe(x2)
    ```

  - **With** `msghub`: In a message hub, the messages from participants will be broadcast to all other participants automatically. In such case, participated agents even don't need input and output messages explicitly. All we need to do is to decide the order of speaking. Besides, `msghub` also supports dynamic control of participants as follows.

    ```python
    from agentscope import msghub

    with msghub(participants=[agent1, agent2, agent3]) as hub:
        agent1() # `x = agent1(x)` is also okay
        agent2()

        # Broadcast a message to all participants
        hub.broadcast(Msg("Host", "Welcome to join the group conversation!"))

        # Add or delete participants dynamically
        hub.delete(agent1)
        hub.add(agent4)
    ```

#### Customize Your Own Agent

To implement your own agent, you need to inherit the `AgentBase` class and implement the `reply` function.

```python
from agentscope.agents import AgentBase

class MyAgent(AgentBase):
    def reply(self, x):
        # Do something here, e.g. calling your model and get the raw field as your agent's response
        response = self.model(x).raw
        return response
```

#### Built-in Resources

AgentScope provides built-in resources for developers to build their own applications easily. More built-in agents, services and examples are coming soon!

##### Agent Pool

- UserAgent
- DialogAgent
- DictDialogAgent
- RpcDialogAgent
- ...

##### Services

- Web Search Service
- Code Execution Service
- Retrieval Service
- Database Service
- File Service
- ...

##### Example Applications

- Example of Conversation: [examples/Conversation](examples/conversation/README.md)
- Example of Werewolf: [examples/Werewolf](examples/werewolf/README.md)
- Example of Distributed Agents: [examples/Distributed Agents](examples/distributed/README.md)
- ...

More built-in resources are coming soon!

## License

AgentScope is released under Apache License 2.0.

## Contributing

Contributions are always welcomed!

We provide a developer version with additional pre-commit hooks to perform checks compared to the official version:

```bash
# For windows
pip install -e .[dev]
# For mac
pip install -e .\[dev\]

# Install pre-commit hooks
pre-commit install
```

Please refer to our [Contribution Guide](https://modelscope.github.io/agentscope/tutorial/contribute.html) for more details.

## References

If you find our work helpful, please consider citing [our paper](https://arxiv.org/abs/2402.14034):

```
@article{agentscope,
  author  = {Dawei Gao and 
             Zitao Li and 
             Weirui Kuang and 
             Xuchen Pan and 
             Daoyuan Chen and 
             Zhijian Ma and 
             Bingchen Qian and 
             Liuyi Yao and  
             Lin Zhu and 
             Chen Cheng and 
             Hongzhu Shi and 
             Yaliang Li and 
             Bolin Ding and 
             Jingren Zhou},
  title   = {AgentScope: A Flexible yet Robust Multi-Agent Platform},
  journal = {CoRR},
  volume  = {abs/2402.14034},
  year    = {2024},
}
```
