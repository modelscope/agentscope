English | [**中文**](README_ZH.md)

# AgentScope

Start building LLM-empowered multi-agent applications in an easier way.

[![](https://img.shields.io/badge/cs.MA-2402.14034-B31C1C?logo=arxiv&logoColor=B31C1C)](https://arxiv.org/abs/2402.14034)
[![](https://img.shields.io/badge/python-3.9+-blue)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/pypi-v0.0.2-blue?logo=pypi)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/Docs-English%7C%E4%B8%AD%E6%96%87-blue?logo=markdown)](https://modelscope.github.io/agentscope/#welcome-to-agentscope-tutorial-hub)
[![](https://img.shields.io/badge/Docs-API_Reference-blue?logo=markdown)](https://modelscope.github.io/agentscope/)
[![](https://img.shields.io/badge/ModelScope-Demos-4e29ff.svg?logo=data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMjI0IDEyMS4zMyIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KCTxwYXRoIGQ9Im0wIDQ3Ljg0aDI1LjY1djI1LjY1aC0yNS42NXoiIGZpbGw9IiM2MjRhZmYiIC8+Cgk8cGF0aCBkPSJtOTkuMTQgNzMuNDloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzYyNGFmZiIgLz4KCTxwYXRoIGQ9Im0xNzYuMDkgOTkuMTRoLTI1LjY1djIyLjE5aDQ3Ljg0di00Ny44NGgtMjIuMTl6IiBmaWxsPSIjNjI0YWZmIiAvPgoJPHBhdGggZD0ibTEyNC43OSA0Ny44NGgyNS42NXYyNS42NWgtMjUuNjV6IiBmaWxsPSIjMzZjZmQxIiAvPgoJPHBhdGggZD0ibTAgMjIuMTloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzM2Y2ZkMSIgLz4KCTxwYXRoIGQ9Im0xOTguMjggNDcuODRoMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzYyNGFmZiIgLz4KCTxwYXRoIGQ9Im0xOTguMjggMjIuMTloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzM2Y2ZkMSIgLz4KCTxwYXRoIGQ9Im0xNTAuNDQgMHYyMi4xOWgyNS42NXYyNS42NWgyMi4xOXYtNDcuODR6IiBmaWxsPSIjNjI0YWZmIiAvPgoJPHBhdGggZD0ibTczLjQ5IDQ3Ljg0aDI1LjY1djI1LjY1aC0yNS42NXoiIGZpbGw9IiMzNmNmZDEiIC8+Cgk8cGF0aCBkPSJtNDcuODQgMjIuMTloMjUuNjV2LTIyLjE5aC00Ny44NHY0Ny44NGgyMi4xOXoiIGZpbGw9IiM2MjRhZmYiIC8+Cgk8cGF0aCBkPSJtNDcuODQgNzMuNDloLTIyLjE5djQ3Ljg0aDQ3Ljg0di0yMi4xOWgtMjUuNjV6IiBmaWxsPSIjNjI0YWZmIiAvPgo8L3N2Zz4K)](https://modelscope.cn/studios?name=agentscope&page=1&sort=latest)

[![](https://img.shields.io/badge/license-Apache--2.0-black)](./LICENSE)
[![](https://img.shields.io/badge/Contribute-Welcome-green)](https://modelscope.github.io/agentscope/tutorial/contribute.html)

If you find our work helpful, please kindly
cite [our paper](https://arxiv.org/abs/2402.14034).

Welcome to join our community on

| [Discord](https://discord.gg/eYMpfnkG8h)                                                                                         | DingTalk                                                                                                                          | WeChat                                                                                                                            |
|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i2/O1CN01tuJ5971OmAqNg9cOw_!!6000000001747-0-tps-444-460.jpg" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i3/O1CN01UyfWfx1CYBM3WqlBy_!!6000000000092-2-tps-400-400.png" width="100" height="100"> |

----

## News

- ![new](https://img.alicdn.com/imgextra/i4/O1CN01kUiDtl1HVxN6G56vN_!!6000000000764-2-tps-43-19.png)
[2024-03-19] We release **AgentScope** v0.0.2 now! In this new version,
AgentScope supports [ollama](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models)(A local CPU inference engine), [DashScope](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models) and Google [Gemini](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models) APIs.

- ![new](https://img.alicdn.com/imgextra/i4/O1CN01kUiDtl1HVxN6G56vN_!!6000000000764-2-tps-43-19.png)
[2024-03-19] New examples ["Autonomous Conversation with Mentions"](./examples/conversation_with_mentions) and ["Basic Conversation with LangChain library"](./examples/conversation_with_langchain) are available now!

- ![new](https://img.alicdn.com/imgextra/i4/O1CN01kUiDtl1HVxN6G56vN_!!6000000000764-2-tps-43-19.png)
[2024-03-19] The [Chinese tutorial](https://modelscope.github.io/agentscope/zh_CN/index.html) of AgentScope is online now!

- [2024-02-27] We release **AgentScope v0.0.1** now, which is also
available in [PyPI](https://pypi.org/project/agentscope/)!
- [2024-02-14] We release our paper "AgentScope: A Flexible yet Robust
Multi-Agent Platform" in [arXiv](https://arxiv.org/abs/2402.14034) now!

---

## What's AgentScope?

AgentScope is an innovative multi-agent platform designed to empower developers
to build multi-agent applications with large-scale models.
It features three high-level capabilities:

- 🤝 **Easy-to-Use**: Designed for developers, with [fruitful components](https://modelscope.github.io/agentscope/en/tutorial/204-service.html#),
[comprehensive documentation](https://modelscope.github.io/agentscope/en/index.html), and broad compatibility.

- ✅ **High Robustness**: Supporting customized fault-tolerance controls and
retry mechanisms to enhance application stability.

- 🚀 **Actor-Based Distribution**: Building distributed multi-agent
applications in a centralized programming manner for streamlined development.

**Supported Model Libraries**

AgentScope provides a list of `ModelWrapper` to support both local model
services and third-party model APIs.

| API                    | Task            | Model Wrapper                                                                                                                   |
|------------------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------|
| OpenAI API             | Chat            | [`OpenAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                 |
|                        | Embedding       | [`OpenAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)            |
|                        | DALL·E          | [`OpenAIDALLEWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                |
| DashScope API          | Chat            | [`DashScopeChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)           |
|                        | Image Synthesis | [`DashScopeImageSynthesisWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py) |
|                        | Text Embedding  | [`DashScopeTextEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)  |
| Gemini API             | Chat            | [`GeminiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)                 |
|                        | Embedding       | [`GeminiEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)            |
| ollama                 | Chat            | [`OllamaChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                 |
|                        | Embedding       | [`OllamaEmbedding`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                   |
|                        | Generation      | [`OllamaGenerationWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)           |
| Post Request based API | -               | [`PostAPIModelWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)                 |

**Supported Local Model Deployment**

AgentScope enables developers to rapidly deploy local model services using
the following libraries.

- [ollama (CPU inference)](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#ollama)
- [Flask + Transformers](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#with-transformers-library)
- [Flask + ModelScope](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#with-modelscope-library)
- [FastChat](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#fastchat)
- [vllm](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#vllm)

**Supported Services**

- Web Search
- Data Query
- Retrieval
- Code Execution
- File Operation
- Text Processing

**Example Applications**

- Conversation
  - [Basic Conversation](./examples/conversation_basic)
  - [Autonomous Conversation with Mentions](./examples/conversation_with_mentions)
  - [Self-Organizing Conversation](./examples/conversation_self_organizing)
  - [Basic Conversation with LangChain library](./examples/conversation_with_langchain)

- Game
  - [Werewolf](./examples/game_werewolf)

- Distribution
  - [Distributed Conversation](./examples/distribution_conversation)
  - [Distributed Debate](./examples/distribution_debate)

More models, services and examples are coming soon!

## Installation

AgentScope requires **Python 3.9** or higher.

**_Note: This project is currently in active development, it's recommended to
install AgentScope from source._**

### From source

- Install AgentScope in editable mode:

```bash
# Pull the source code from GitHub
git clone https://github.com/modelscope/agentscope.git

# Install the package in editable mode
cd AgentScope
pip install -e .
```

- To build distributed multi-agent applications:

```bash
# On windows
pip install -e .[distribute]
# On mac
pip install -e .\[distribute\]
```

### Using pip

- Install AgentScope from pip:

```bash
pip install agentscope
```

## Quick Start

### Configuration

In AgentScope, the model deployment and invocation are decoupled by
`ModelWrapper`.

To use these model wrappers, you need to prepare a model config file as
follows.

```python
model_config = {
    # The identifies of your config and used model wrapper
    "config_name": "{your_config_name}",          # The name to identify the config
    "model_type": "{model_type}",                 # The type to identify the model wrapper

    # Detailed parameters into initialize the model wrapper
    # ...
}
```

Taking OpenAI Chat API as an example, the model configuration is as follows:

```python
openai_model_config = {
    "config_name": "my_openai_config",             # The name to identify the config
    "model_type": "openai",                        # The type to identify the model wrapper

    # Detailed parameters into initialize the model wrapper
    "model_name": "gpt-4",                         # The used model in openai API, e.g. gpt-4, gpt-3.5-turbo, etc.
    "api_key": "xxx",                              # The API key for OpenAI API. If not set, env
                                                   # variable OPENAI_API_KEY will be used.
    "organization": "xxx",                         # The organization for OpenAI API. If not set, env
                                                   # variable OPENAI_ORGANIZATION will be used.
}
```

More details about how to set up local model services and prepare model
configurations is in our
[tutorial](https://modelscope.github.io/agentscope/index.html#welcome-to-agentscope-tutorial-hub).

### Create Agents

Create built-in user and assistant agents as follows.

```python
from agentscope.agents import DialogAgent, UserAgent
import agentscope

# Load model configs
agentscope.init(model_configs="./model_configs.json")

# Create a dialog agent and a user agent
dialog_agent = DialogAgent(name="assistant",
                           model_config_name="my_openai_config")
user_agent = UserAgent()
```

### Construct Conversation

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
    if x.content == "exit":  # user input "exit" to exit the conversation_basic
        break
```

## Tutorial

- [Getting Started](https://modelscope.github.io/agentscope/en/tutorial/quick_start.html)
  - [About AgentScope](https://modelscope.github.io/agentscope/en/tutorial/101-agentscope.html)
  - [Installation](https://modelscope.github.io/agentscope/en/tutorial/102-installation.html)
  - [Quick Start](https://modelscope.github.io/agentscope/en/tutorial/103-example.html)
  - [Crafting Your First Application](https://modelscope.github.io/agentscope/en/tutorial/104-usecase.html)
  - [Logging and WebUI](https://modelscope.github.io/agentscope/en/tutorial/105-logging.html#)
- [Advanced Exploration](https://modelscope.github.io/agentscope/en/tutorial/advance.html)
  - [Customize Your Own Agent](https://modelscope.github.io/agentscope/en/tutorial/201-agent.html)
  - [Pipeline and MsgHub](https://modelscope.github.io/agentscope/en/tutorial/202-pipeline.html)
  - [Model](https://modelscope.github.io/agentscope/en/tutorial/203-model.html)
  - [Service](https://modelscope.github.io/agentscope/en/tutorial/204-service.html)
  - [Memory](https://modelscope.github.io/agentscope/en/tutorial/205-memory.html)
  - [Prompt Engine](https://modelscope.github.io/agentscope/en/tutorial/206-prompt.html)
  - [Monitor](https://modelscope.github.io/agentscope/en/tutorial/207-monitor.html)
  - [Distribution](https://modelscope.github.io/agentscope/en/tutorial/208-distribute.html)
- [Get Involved](https://modelscope.github.io/agentscope/en/tutorial/contribute.html)
  - [Join AgentScope Community](https://modelscope.github.io/agentscope/en/tutorial/301-community.html)
  - [Contribute to AgentScope](https://modelscope.github.io/agentscope/en/tutorial/302-contribute.html)

## License

AgentScope is released under Apache License 2.0.

## Contributing

Contributions are always welcomed!

We provide a developer version with additional pre-commit hooks to perform
checks compared to the official version:

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

If you find our work helpful for your research or application, please
cite [our paper](https://arxiv.org/abs/2402.14034):

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
