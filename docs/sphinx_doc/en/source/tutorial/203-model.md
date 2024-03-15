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

An example of `model_configs` is as follows:

```python
model_configs = [
    {
        "config_name": "gpt-4-temperature-0.0",
        "model_type": "openai",
        "model_name": "gpt-4",
        "api_key": "xxx",
        "organization": "xxx",
        "generate_args": {
            "temperature": 0.0
        }
    },
    {
        "config_name": "dall-e-3-size-1024x1024",
        "model_type": "openai_dall_e",
        "model_name": "dall-e-3",
        "api_key": "xxx",
        "organization": "xxx",
        "generate_args": {
            "size": "1024x1024"
        }
    },
    # Additional models can be configured here
]
```

### Configuration Format

In AgentScope, the model configuration is a dictionary used to specify the type of model and set the call parameters.
We divide the fields in the model configuration into two categories: _basic parameters_ and _detailed parameters_.
Among them, the basic parameters include `config_name` and `model_type`, which are used to distinguish different model configurations and specific `ModelWrapper` types.

```python
{
    # Basic parameters
    "config_name": "gpt-4-temperature-0.0",     # Model configuration name
    "model_type": "openai",                     # Correspond to `ModelWrapper` type

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


| API                    | Task            | Model Wrapper                    | `model_type`                |
|------------------------|-----------------|----------------------------------|-----------------------------|
| OpenAI API             | Chat            | `OpenAIChatWrapper`              | "openai"                    |
|                        | Embedding       | `OpenAIEmbeddingWrapper`         | "openai_embedding"          |
|                        | DALL·E          | `OpenAIDALLEWrapper`             | "openai_dall_e"             |
| DashScope API          | Chat            | `DashScopeChatWrapper`           | "dashscope_chat"            |
|                        | Image Synthesis | `DashScopeImageSynthesisWrapper` | "dashscope_image_synthesis" |
|                        | Text Embedding  | `DashScopeTextEmbeddingWrapper`  | "dashscope_text_embedding"  |
| Gemini API             | Chat            | `GeminiChatWrapper`              | "gemini_chat"               |
|                        | Embedding       | `GeminiEmbeddingWrapper`         | "gemini_embedding"          |
| ollama                 | Chat            | `OllamaChatWrapper`              | "ollama_chat"               |
|                        | Embedding       | `OllamaEmbedding`                | "ollama_embedding"          |
|                        | Generation      | `OllamaGenerationWrapper`        | "ollama_generate"           |
| Post Request based API | -               | `PostAPIModelWrapper`            | "post_api“                  |
|                        | Chat            | `PostAPIChatWrapper`             | "post_api_chat"             |

#### Detailed Parameters

According to the different `ModelWrapper`, the parameters contained in the
detailed parameters are different. However, all detailed parameters will be
used to initialize the instance of the `ModelWrapper` class. Therefore, more
detailed parameter descriptions can be viewed according to the constructor of
their `ModelWrapper` classes.

- For OpenAI APIs including text generation, image generation, and text embedding, the model configuration parameters are as follows:

```python
{
    # basic parameters
    "config_name": "gpt-4_temperature-0.0",
    "model_type": "openai",

    # detailed parameters
    # required parameters
    "model_name": "gpt-4",          # OpenAI model name

    # optional
    "api_key": "xxx",               # OpenAI API Key, if not provided, it will be read from the environment variable
    "organization": "xxx",          # Organization name, if not provided, it will be read from the environment variable
    "client_args": {                # Parameters for initializing the OpenAI API Client
        # e.g. "max_retries": 3,
    },
    "generate_args": {              # Parameters passed to the model when calling
        # e.g. "temperature": 0.0
    },
    "budget": 100.0                 # API budget
}
```

- For DashScope API, the model configuration parameters are as follows:
```python
{
    # basic parameters
    "config_name": "my_qwen_config",               # The name to identify the config.
    "model_type": "dashscope_chat" ,               # can also be "dashscope_text_embedding" for embedding and  "dashscope_image_synthesis" for text-to-image.

    # detailed parameters
    # required parameters
    "model_name": "qwen-max",                      # The model in dashscope API.

    # optional
    "api_key": "xxx",                              # The API key for DashScope API. If not provided, will try to read from the environment variable.

    "generate_args": {                              # Parameters passed to the model when calling.
        # e.g. "temperature": 0.0, "seed": 123
    },
}
```


- For Gemini API, the model configuration parameters are as follows:
```python
{
    # basic parameters
    "config_name": "my_gemini_chat",            # The name to identify the config.
    "model_type": "gemini_chat",                # can also be "gemini_embedding" for embedding

    # detailed parameters
    # required parameters
    "model_name": "gemini-pro",

    # optional
    "api_key": "xxx",                          # The API key
    "generation_config": {                     # Parameters passed to the model when calling.
          # "temperature": 0.2,
    }
}
```

- For ollama API, the model configuration parameters are as follows:

```python
{
    # basic parameters
    "config_name": "my_ollama_chat",                    # The name to identify the config.
    "model_type": "ollama_chat",                        # can also be "ollama_embedding" for embedding and "ollama_generate" for generation

    "model": "llama2",                                  # the model name used in ollama API.

    "options": {                                        # Parameters passed to the model when calling.
        # e.g. "temperature": 0.0
    },
    "keep_alive": "5m",                                 # Controls how long the model will stay loaded into memory
}
```

- For post request API, the model configuration parameters are as follows:

```python
{
    # basic parameters
    "config_name": "gpt-4_temperature-0.0",
    "model_type": "post_api",

    # detailed parameters
    "api_url": "http://xxx",
    "headers": {
        # e.g. "Authorization": "Bearer xxx",
    },

    # Optional parameters, need to be configured according to the requirements of the Post request API
    "json_args": {
        # e.g. "temperature": 0.0
    }
    # ...
}
```

## Build Model Service from Scratch

For developers who need to build their own model services, AgentScope
provides some scripts to help developers quickly build model services.
You can find these scripts and instructions in the [scripts](https://github.com/modelscope/agentscope/tree/main/scripts)
directory.

Specifically, AgentScope provides the following model service scripts:

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
