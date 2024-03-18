(203-model-en)=

# Model Service

In AgentScope, the model deployment and invocation are decoupled by `ModelWrapper`.
Developers can specify their own model by providing model configurations,
and AgentScope also provides scripts to support developers to customize
model services.

## Supported Models

Currently, AgentScope supports the following model service APIs:

- OpenAI API, including chat, image generation (DALL-E), and Embedding.
- DashScope API, including chat, image sythesis and text embedding.
- Gemini API, including chat and embedding.
- Ollama API, including chat, embedding and generation.
- Post Request API, model inference services based on Post
  requests, including Huggingface/ModelScope Inference API and various
  post request based model APIs.

## Configuration

In AgentScope, users specify the model configuration through the
`model_configs` parameter in the `agentscope.init` interface.
`model_configs` can be a **dictionary**, **a list of dictionaries**, or a
**path** to model configuration file.

```python
import agentscope

agentscope.init(model_configs=MODEL_CONFIG_OR_PATH)
```

### Configuration Format

In AgentScope, the model configuration is a dictionary used to specify the type of model and set the call parameters.
We divide the fields in the model configuration into two categories: _basic parameters_ and _detailed parameters_.

Among them, the basic parameters include `config_name` and `model_type`, which are used to distinguish different model configurations and specific `ModelWrapper` types.
The detailed parameters will be fed into the corresponding model class's constructor to initialize the model instance.

```python
{
    # Basic parameters
    "config_name": "gpt-4-temperature-0.0",  # Model configuration name
    "model_type": "openai",  # Correspond to `ModelWrapper` type

    # Detailed parameters
    # ...
}
```

#### Basic Parameters

In basic parameters, `config_name` is the identifier of the model configuration,
which we will use to specify the model service when initializing an agent.

`model_type` corresponds to the type of `ModelWrapper` and is used to specify the type of model service.
It corresponds to the `model_type` field in the `ModelWrapper` class in the source code.

```python
class OpenAIChatWrapper(OpenAIWrapper):
    """The model wrapper for OpenAI's chat API."""

    model_type: str = "openai"
    # ...
```

In the current AgentScope, the supported `model_type` types, the corresponding
`ModelWrapper` classes, and the supported APIs are as follows:

| API                    | Task            | Model Wrapper                                                                                                                   | `model_type`                  |
|------------------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------|-------------------------------|
| OpenAI API             | Chat            | [`OpenAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                 | `"openai"`                    |
|                        | Embedding       | [`OpenAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)            | `"openai_embedding"`          |
|                        | DALL·E          | [`OpenAIDALLEWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                | `"openai_dall_e"`             |
| DashScope API          | Chat            | [`DashScopeChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)           | `"dashscope_chat"`            |
|                        | Image Synthesis | [`DashScopeImageSynthesisWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py) | `"dashscope_image_synthesis"` |
|                        | Text Embedding  | [`DashScopeTextEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)  | `"dashscope_text_embedding"`  |
| Gemini API             | Chat            | [`GeminiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)                 | `"gemini_chat"`               |
|                        | Embedding       | [`GeminiEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)            | `"gemini_embedding"`          |
| ollama                 | Chat            | [`OllamaChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                 | `"ollama_chat"`               |
|                        | Embedding       | [`OllamaEmbedding`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                   | `"ollama_embedding"`          |
|                        | Generation      | [`OllamaGenerationWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)           | `"ollama_generate"`           |
| Post Request based API | -               | [`PostAPIModelWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)                 | `"post_api"`                  |

#### Detailed Parameters

In AgentScope, the detailed parameters are different according to the different `ModelWrapper` classes.
To specify the detailed parameters, you need to refer to the specific `ModelWrapper` class and its constructor.
Here we provide example configurations for different model wrappers.

##### OpenAI API

<details>
<summary>OpenAI Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py">agents.models.OpenAIChatWrapper</a></code>)</summary>

```python
openai_chat_config = {
    "config_name": "{your_config_name}",
    "model_type": "openai",

    # Required parameters
    "model_name": "gpt-4",

    # Optional parameters
    "api_key": "{your_api_key}",                # OpenAI API Key, if not provided, it will be read from the environment variable
    "organization": "{your_organization}",      # Organization name, if not provided, it will be read from the environment variable
    "client_args": {                            # Parameters for initializing the OpenAI API Client
        # e.g. "max_retries": 3,
    },
    "generate_args": {                          # Parameters passed to the model when calling
        # e.g. "temperature": 0.0
    },
    "budget": 100                               # API budget
}
```

</details>

<details>
<summary>OpenAI DALL·E API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py">agentscope.models.OpenAIDALLEWrapper</a></code>)</summary>

```python
{
    "config_name": "{your_config_name}",
    "model_type": "openai_dall_e",

    # Required parameters
    "model_name": "{model_name}",               # OpenAI model name, e.g. dall-e-2, dall-e-3

    # Optional parameters
    "api_key": "{your_api_key}",                # OpenAI API Key, if not provided, it will be read from the environment variable
    "organization": "{your_organization}",      # Organization name, if not provided, it will be read from the environment variable
    "client_args": {                            # Parameters for initializing the OpenAI API Client
        # e.g. "max_retries": 3,
    },
    "generate_args": {                          # Parameters passed to the model when calling
        # e.g. "n": 1, "size": "512x512"
    }
}
```

</details>

<details>
<summary>OpenAI Embedding API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py">agentscope.models.OpenAIEmbeddingWrapper</a></code>)</summary>

```python
{
    "config_name": "{your_config_name}",
    "model_type": "openai_embedding",

    # Required parameters
    "model_name": "{model_name}",               # OpenAI model name, e.g. text-embedding-ada-002, text-embedding-3-small

    # Optional parameters
    "api_key": "{your_api_key}",                # OpenAI API Key, if not provided, it will be read from the environment variable
    "organization": "{your_organization}",      # Organization name, if not provided, it will be read from the environment variable
    "client_args": {                            # Parameters for initializing the OpenAI API Client
        # e.g. "max_retries": 3,
    },
    "generate_args": {                          # Parameters passed to the model when calling
        # e.g. "encoding_format": "float"
    }
}
```

</details>

#### DashScope API

<details>
<summary>DashScope Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py">agentscope.models.DashScopeChatWrapper</a></code>)</summary>

```python
{
    "config_name": "my_dashscope_chat_config",
    "model_type": "dashscope_chat",

    # Required parameters
    "model_name": "{model_name}",               # The model name in DashScope API, e.g. qwen-max

    # Optional parameters
    "api_key": "{your_api_key}",                # DashScope API Key, if not provided, it will be read from the environment variable
    "generate_args": {
        # e.g. "temperature": 0.5
    },
}
```

</details>

<details>
<summary>DashScope Image Synthesis API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py">agentscope.models.DashScopeImageSynthesisWrapper</a></code>)</summary>

```python
{
    "config_name": "my_dashscope_image_synthesis_config",
    "model_type": "dashscope_image_synthesis",

    # Required parameters
    "model_name": "{model_name}",               # The model name in DashScope Image Synthesis API, e.g. wanx-v1

    # Optional parameters
    "api_key": "{your_api_key}",
    "generate_args": {
        "negative_prompt": "xxx",
        "n": 1,
        # ...
    }
}
```

</details>

<details>
<summary>DashScope Text Embedding API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py">agentscope.models.DashScopeTextEmbeddingWrapper</a></code>)</summary>

```python
{
    "config_name": "my_dashscope_text_embedding_config",
    "model_type": "dashscope_text_embedding",

    # Required parameters
    "model_name": "{model_name}",               # The model name in DashScope Text Embedding API, e.g. text-embedding-v1

    # Optional parameters
    "api_key": "{your_api_key}",
    "generate_args": {
        # ...
    },
}
```

</details>

#### Gemini API

<details>
<summary>Gemini Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py">agentscope.models.GeminiChatWrapper</a></code>)</summary>

```python
{
    "config_name": "my_gemini_chat_config",
    "model_type": "gemini_chat",

    # Required parameters
    "model_name": "{model_name}",               # The model name in Gemini API, e.g. gemini-prp

    # Optional parameters
    "api_key": "{your_api_key}",                # If not provided, the API key will be read from the environment variable GEMINI_API_KEY
}
```

</details>

<details>
<summary>Gemini Embedding API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py">agentscope.models.GeminiEmbeddingWrapper</a></code>)</summary>

```python
{
    "config_name": "my_gemini_embedding_config",
    "model_type": "gemini_embedding",

    # Required parameters
    "model_name": "{model_name}",               # The model name in Gemini API, e.g. gemini-prp

    # Optional parameters
    "api_key": "{your_api_key}",                # If not provided, the API key will be read from the environment variable GEMINI_API_KEY
}
```

</details>

#### Ollama API

<details>
<summary>Ollama Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py">agentscope.models.OllamaChatWrapper</a></code>)</summary>

```python
{
    "config_name": "my_ollama_chat_config",
    "model_type": "ollama_chat",

    # Required parameters
    "model": "{model_name}",                    # The model name used in ollama API, e.g. llama2

    # Optional parameters
    "options": {                                # Parameters passed to the model when calling
        # e.g. "temperature": 0., "seed": "123",
    },
    "keep_alive": "5m",                         # Controls how long the model will stay loaded into memory
}
```

</details>

<details>
<summary>Ollama Generation API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py">agentscope.models.OllamaGenerationWrapper</a></code>)</summary>

```python
{
    "config_name": "my_ollama_generate_config",
    "model_type": "ollama_generate",

    # Required parameters
    "model": "{model_name}",                    # The model name used in ollama API, e.g. llama2

    # Optional parameters
    "options": {                                # Parameters passed to the model when calling
        # "temperature": 0., "seed": "123",
    },
    "keep_alive": "5m",                         # Controls how long the model will stay loaded into memory
}
```

</details>

<details>
<summary>Ollama Embedding API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py">agentscope.models.OllamaEmbeddingWrapper</a></code>)</summary>

```python
{
    "config_name": "my_ollama_embedding_config",
    "model_type": "ollama_embedding",

    # Required parameters
    "model": "{model_name}",                    # The model name used in ollama API, e.g. llama2

    # Optional parameters
    "options": {                                # Parameters passed to the model when calling
        # "temperature": 0., "seed": "123",
    },
    "keep_alive": "5m",                         # Controls how long the model will stay loaded into memory
}
```

</details>

#### Post Request API

<details>
<summary>Post request API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py">agentscope.models.PostAPIModelWrapperBase</a></code>)</summary>

```python
{
    "config_name": "my_postapiwrapper_config",
    "model_type": "post_api",

    # Required parameters
    "api_url": "https://xxx.xxx",
    "headers": {
        # e.g. "Authorization": "Bearer xxx",
    },

    # Optional parameters
    "messages_key": "messages",
}
```

</details>

## Build Model Service from Scratch

For developers who need to build their own model services, AgentScope
provides some scripts to help developers quickly build model services.
You can find these scripts and instructions in the [scripts](https://github.com/modelscope/agentscope/tree/main/scripts)
directory.

Specifically, AgentScope provides the following model service scripts:

- CPU inference engine **ollama**
- Model service based on **Flask + HuggingFace**
- Model service based on **Flask + ModelScope**
- **FastChat** inference engine
- **vllm** inference engine

Taking the Flask + Huggingface model service as an example, we will introduce how to use the model service script of AgentScope.
More model service scripts can be found in [scripts](https://github.com/modelscope/agentscope/blob/main/scripts/) directory.

### Flask-based Model API Serving

[Flask](https://github.com/pallets/flask) is a lightweight web application framework. It is easy to build a local model API service with Flask.

#### Using transformers library

##### Install Libraries and Set up Serving

Install Flask and Transformers by following the command.

```bash
pip install Flask transformers
```

Taking model `meta-llama/Llama-2-7b-chat-hf` and port `8000` as an example, set up the model API service by running the following command.

```bash
python flask_transformers/setup_hf_service.py
    --model_name_or_path meta-llama/Llama-2-7b-chat-hf
    --device "cuda:0" # or "cpu"
    --port 8000
```

You can replace `meta-llama/Llama-2-7b-chat-hf` with any model card in the huggingface model hub.

##### Use in AgentScope

In AgentScope, you can load the model with the following model configs: [./flask_transformers/model_config.json](https://github.com/modelscope/agentscope/blob/main/scripts/flask_transformers/model_config.json).

```json
{
    "model_type": "post_api",
    "config_name": "flask_llama2-7b-chat",
    "api_url": "http://127.0.0.1:8000/llm/",
    "json_args": {
        "max_length": 4096,
        "temperature": 0.5
    }
}
```

##### Note

In this model serving, the messages from post requests should be in **STRING** format. You can use [templates for chat model](https://huggingface.co/docs/transformers/main/chat_templating) from _transformers_ with a little modification based on [`./flask_transformers/setup_hf_service.py`](https://github.com/modelscope/agentscope/blob/main/scripts/flask_transformers/setup_hf_service.py).

[[Return to Top]](#203-model-en)
