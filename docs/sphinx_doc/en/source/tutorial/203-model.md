(203-model-en)=

# Model

In AgentScope, the model deployment and invocation are decoupled by `ModelWrapper`.
Developers can specify their own model by providing model configurations,
and AgentScope also provides scripts to support developers to customize
model services.

## Supported Models

Currently, AgentScope supports the following model service APIs:

- OpenAI API, including chat, image generation (DALL-E), and Embedding.
- DashScope API, including chat, image sythesis and text embedding.
- Gemini API, including chat and embedding.
- ZhipuAI API, including chat and embedding.
- Ollama API, including chat, embedding and generation.
- LiteLLM API, including chat, with various model APIs.
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
    "model_type": "openai_chat",             # Correspond to `ModelWrapper` type

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
class OpenAIChatWrapper(OpenAIWrapperBase):
    """The model wrapper for OpenAI's chat API."""

    model_type: str = "openai_chat"
    # ...
```

In the current AgentScope, the supported `model_type` types, the corresponding
`ModelWrapper` classes, and the supported APIs are as follows:

| API                    | Task            | Model Wrapper                                                                                                                   | `model_type`                  | Some Supported Models                            |
|------------------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------|-------------------------------|--------------------------------------------------|
| OpenAI API             | Chat            | [`OpenAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                 | `"openai_chat"`                    | gpt-4, gpt-3.5-turbo, ...                        |
|                        | Embedding       | [`OpenAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)            | `"openai_embedding"`          | text-embedding-ada-002, ...                      |
|                        | DALL·E          | [`OpenAIDALLEWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                | `"openai_dall_e"`             | dall-e-2, dall-e-3                               |
| DashScope API          | Chat            | [`DashScopeChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)           | `"dashscope_chat"`            | qwen-plus, qwen-max, ...                         |
|                        | Image Synthesis | [`DashScopeImageSynthesisWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py) | `"dashscope_image_synthesis"` | wanx-v1                                          |
|                        | Text Embedding  | [`DashScopeTextEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)  | `"dashscope_text_embedding"`  | text-embedding-v1, text-embedding-v2, ...        |
|                        | Multimodal      | [`DashScopeMultiModalWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)     | `"dashscope_multimodal"`      | qwen-vl-plus, qwen-vl-max, qwen-audio-turbo, ... |
| Gemini API             | Chat            | [`GeminiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)                 | `"gemini_chat"`               | gemini-pro, ...                                  |
|                        | Embedding       | [`GeminiEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)            | `"gemini_embedding"`          | models/embedding-001, ...                        |
| ZhipuAI API             | Chat            | [`ZhipuAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)                 | `"zhipuai_chat"`               | glm4, ...                                  |
|                        | Embedding       | [`ZhipuAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)            | `"zhipuai_embedding"`          | embedding-2, ...                        |
| ollama                 | Chat            | [`OllamaChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                 | `"ollama_chat"`               | llama2, ...                                      |
|                        | Embedding       | [`OllamaEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)            | `"ollama_embedding"`          | llama2, ...                                      |
|                        | Generation      | [`OllamaGenerationWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)           | `"ollama_generate"`           | llama2, ...                                      |
| LiteLLM API | Chat               | [`LiteLLMChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/litellm_model.py)             | `"litellm_chat"`                  | -                                                |
| Post Request based API | -               | [`PostAPIModelWrapperBase`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)             | `"post_api"`                  | -                                                |
|                        | Chat            | [`PostAPIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)                  | `"post_api_chat"`             | meta-llama/Meta-Llama-3-8B-Instruct, ...         |
|                        | Image Synthesis | [`PostAPIDALLEWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)                 | `post_api_dall_e`             | -                                                |                                                  |
|                        | Embedding       | [`PostAPIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)             | `post_api_embedding`          | -                                                |

#### Detailed Parameters

In AgentScope, the detailed parameters are different according to the different `ModelWrapper` classes.
To specify the detailed parameters, you need to refer to the specific `ModelWrapper` class and its constructor.
Here we provide example configurations for different model wrappers.

##### OpenAI API

<details>
<summary>OpenAI Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py">agents.models.OpenAIChatWrapper</a></code>)</summary>

```python
{
    "config_name": "{your_config_name}",
    "model_type": "openai_chat",

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

<br/>

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

<details>
<summary>DashScope Multimodal Conversation API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py">agentscope.models.DashScopeMultiModalWrapper</a></code>)</summary>

```python
{
    "config_name": "my_dashscope_multimodal_config",
    "model_type": "dashscope_multimodal",

    # Required parameters
    "model_name": "{model_name}",              # The model name in DashScope Multimodal Conversation API, e.g. qwen-vl-plus

    # Optional parameters
    "api_key": "{your_api_key}",
    "generate_args": {
        # ...
    },
}
```

</details>

<br/>

#### Gemini API

<details>
<summary>Gemini Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py">agentscope.models.GeminiChatWrapper</a></code>)</summary>

```python
{
    "config_name": "my_gemini_chat_config",
    "model_type": "gemini_chat",

    # Required parameters
    "model_name": "{model_name}",               # The model name in Gemini API, e.g. gemini-pro

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
    "model_name": "{model_name}",               # The model name in Gemini API, e.g. models/embedding-001

    # Optional parameters
    "api_key": "{your_api_key}",                # If not provided, the API key will be read from the environment variable GEMINI_API_KEY
}
```

</details>

<br/>


#### ZhipuAI API

<details>
<summary>ZhipuAI Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py">agentscope.models.ZhipuAIChatWrapper</a></code>)</summary>

```python
{
    "config_name": "my_zhipuai_chat_config",
    "model_type": "zhipuai_chat",

    # Required parameters
    "model_name": "{model_name}",               # The model name in ZhipuAI API, e.g. glm-4

    # Optional parameters
    "api_key": "{your_api_key}"
}
```

</details>

<details>
<summary>ZhipuAI Embedding API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py">agentscope.models.ZhipuAIEmbeddingWrapper</a></code>)</summary>

```python
{
    "config_name": "my_zhipuai_embedding_config",
    "model_type": "zhipuai_embedding",

    # Required parameters
    "model_name": "{model_name}",               # The model name in ZhipuAI API, e.g. embedding-2

    # Optional parameters
    "api_key": "{your_api_key}",
}
```

</details>

<br/>


#### Ollama API

<details>
<summary>Ollama Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py">agentscope.models.OllamaChatWrapper</a></code>)</summary>

```python
{
    "config_name": "my_ollama_chat_config",
    "model_type": "ollama_chat",

    # Required parameters
    "model_name": "{model_name}",               # The model name used in ollama API, e.g. llama2

    # Optional parameters
    "options": {                                # Parameters passed to the model when calling
        # e.g. "temperature": 0., "seed": 123,
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
    "model_name": "{model_name}",               # The model name used in ollama API, e.g. llama2

    # Optional parameters
    "options": {                                # Parameters passed to the model when calling
        # "temperature": 0., "seed": 123,
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
    "model_name": "{model_name}",               # The model name used in ollama API, e.g. llama2

    # Optional parameters
    "options": {                                # Parameters passed to the model when calling
        # "temperature": 0., "seed": 123,
    },
    "keep_alive": "5m",                         # Controls how long the model will stay loaded into memory
}
```

</details>

<br/>

#### LiteLLM Chat API

<details>
<summary>LiteLLM Chat API (<code><a href="https://github.
com/modelscope/agentscope/blob/main/src/agentscope/models/litellm_model.py">agentscope.models.LiteLLMChatModelWrapper</a></code>)</summary>

```python
{
    "config_name": "lite_llm_openai_chat_gpt-3.5-turbo",
    "model_type": "litellm_chat",
    "model_name": "gpt-3.5-turbo" # You should note that for different models, you should set the corresponding environment variables, such as OPENAI_API_KEY, etc. You may refer to https://docs.litellm.ai/docs/ for this.
},
```

</details>

<br/>

#### Post Request API

<details>
<summary>Post Request Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py">agentscope.models.PostAPIChatWrapper</a></code>)</summary>

```python
{
    "config_name": "my_postapichatwrapper_config",
    "model_type": "post_api_chat",

    # Required parameters
    "api_url": "https://xxx.xxx",
    "headers": {
        # e.g. "Authorization": "Bearer xxx",
    },

    # Optional parameters
    "messages_key": "messages",
}
```
> ⚠️ The Post Request Chat model wrapper (`PostAPIChatWrapper`) has the following properties:
> 1) The `.format()` function makes sure the input messages become a list of dicts.
> 2) The `._parse_response()` function assumes the generated text will be in `response["data"]["response"]["choices"][0]["message"]["content"]`

</details>



<details>
<summary>Post Request Image Synthesis API  (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py">agentscope.models.PostAPIDALLEWrapper</a></code>)</summary>

```python
{
    "config_name": "my_postapiwrapper_config",
    "model_type": "post_api_dall_e",

    # Required parameters
    "api_url": "https://xxx.xxx",
    "headers": {
        # e.g. "Authorization": "Bearer xxx",
    },

    # Optional parameters
    "messages_key": "messages",
}
```
> ⚠️ The Post Request Image Synthesis model wrapper (`PostAPIDALLEWrapper`) has the following properties:
> 1) The `._parse_response()` function assumes the generated image will be presented as urls in `response["data"]["response"]["data"][i]["url"]`

</details>


<details>
<summary>Post Request Embedding API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py">agentscope.models.PostAPIEmbeddingWrapper</a></code>)</summary>

```python
{
    "config_name": "my_postapiwrapper_config",
    "model_type": "post_api_embedding",

    # Required parameters
    "api_url": "https://xxx.xxx",
    "headers": {
        # e.g. "Authorization": "Bearer xxx",
    },

    # Optional parameters
    "messages_key": "messages",
}
```
> ⚠️ The Post Request Embedding model wrapper (`PostAPIEmbeddingWrapper`) has the following properties:
> 1) The `._parse_response()` function assumes the generated embeddings will be in `response["data"]["response"]["data"][i]["embedding"]`

</details>


<details>
<summary>Post Request API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py">agentscope.models.PostAPIModelWrapperBase</a></code>)</summary>

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
> ⚠️ Post Request model wrapper (`PostAPIModelWrapperBase`) returns raw HTTP responses from the API in ModelResponse, and the `.format()` is not implemented. It is recommended to use `Post Request Chat API` when running examples with chats.
> `PostAPIModelWrapperBase` can be used when
> 1) only the raw HTTP response is wanted and `.format()` is not called;
> 2) Or, the developers want to overwrite the `.format()` and/or `._parse_response()` functions.

</details>


<br/>

## Build Model Service from Scratch

For developers who need to build their own model services, AgentScope
provides some scripts to help developers quickly build model services.
You can find these scripts and instructions in the [scripts](https://github.com/modelscope/agentscope/tree/main/scripts)
directory.

Specifically, AgentScope provides the following model service scripts:

- [CPU inference engine **ollama**](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#ollama)
- [Model service based on **Flask + Transformers**](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#with-transformers-library)
- [Model service based on **Flask + ModelScope**](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#with-modelscope-library)
- [**FastChat** inference engine](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#fastchat)
- [**vllm** inference engine](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#vllm)

About how to quickly start these model services, users can refer to the [README.md](https://github.com/modelscope/agentscope/blob/main/scripts/README.md) file under the [scripts](https://github.com/modelscope/agentscope/blob/main/scripts/) directory.

## Creat Your Own Model Wrapper

AgentScope allows developers to customize their own model wrappers.
The new model wrapper class should

- inherit from `ModelWrapperBase` class,
- provide a `model_type` field to identify this model wrapper in the model configuration, and
- implement its `__init__` and `__call__` functions.

The following is an example for creating a new model wrapper class.

```python
from agentscope.models import ModelWrapperBase

class MyModelWrapper(ModelWrapperBase):

    model_type: str = "my_model"

    def __init__(self, config_name, my_arg1, my_arg2, **kwargs):
        # Initialize the model instance
        super().__init__(config_name=config_name)
        # ...

    def __call__(self, input, **kwargs) -> str:
        # Call the model instance
        # ...
```

After creating the new model wrapper class, the model wrapper will be registered into AgentScope automatically.
You can use it in the model configuration directly.

```python
my_model_config = {
    # Basic parameters
    "config_name": "my_model_config",
    "model_type": "my_model",

    # Detailed parameters
    "my_arg1": "xxx",
    "my_arg2": "yyy",
    # ...
}
```

[[Return to Top]](#203-model-en)
