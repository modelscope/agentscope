(203-model-zh)=

# 关于模型

AgentScope中，模型的部署和调用是通过`ModelWrapper`来解耦开的，开发者可以通过提供模型配置（Model config）的方式指定模型，同时AgentScope也提供脚本支持开发者自定义模型服务。

## 支持模型

目前，AgentScope内置以下模型服务API的支持：

- OpenAI API，包括对话（Chat），图片生成（DALL-E)和文本嵌入（Embedding）。
- DashScope API，包括对话（Chat）和图片生成（Image Sythesis)和文本嵌入（Text Embedding)。
- Gemini API，包括对话（Chat）和嵌入（Embedding）。
- Ollama API，包括对话（Chat），嵌入（Embedding）和生成（Generation）。
- Post请求API，基于Post请求实现的模型推理服务，包括Huggingface/ModelScope
  Inference API和各种符合Post请求格式的API。

## 配置方式

AgentScope中，用户通过`agentscope.init`接口中的`model_configs`参数来指定模型配置。
`model_configs`可以是一个字典，或是一个字典的列表，抑或是一个指向模型配置文件的路径。

```python
import agentscope

agentscope.init(model_configs=MODEL_CONFIG_OR_PATH)
```

其中`model_configs`的一个例子如下：

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
    # 在这里可以配置额外的模型
]
```

### 配置格式

AgentScope中，模型配置是一个字典，用于指定模型的类型以及设定调用参数。
我们将模型配置中的字段分为_基础参数_和_调用参数_两类。
其中，基础参数包括`config_name`和`model_type`两个基本字段，分别用于区分不同的模型配置和具
体的`ModelWrapper`类型。

```python
{
    # 基础参数
    "config_name": "gpt-4-temperature-0.0",     # 模型配置名称
    "model_type": "openai",                     # 对应`ModelWrapper`类型

    # 详细参数
    # ...
}
```

#### 基础参数

基础参数中，`config_name`是模型配置的标识，我们将在初始化智能体时用该字段指定使用的模型服务。

`model_type`对应了`ModelWrapper`的类型，用于指定模型服务的类型。对应源代码中`ModelWrapper
`类的`model_type`字段。

```python
class OpenAIChatWrapper(OpenAIWrapper):
    """The model wrapper for OpenAI's chat API."""

    model_type: str = "openai"
    # ...
```

在目前的AgentScope中，所支持的`model_type`类型，对应的`ModelWrapper`类，以及支持的
API如下：

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

#### 详细参数

根据`ModelWrapper`的不同，详细参数中所包含的参数不同。
但是所有的详细参数都会用于初始化`ModelWrapper`类的实例，因此，更详细的参数说明可以根据`ModelWrapper`类的构造函数来查看。
下面展示了不同`ModelWrapper`对应的模型配置样例，用户可以修改这些样例以适应自己的需求。

##### OpenAI API

<details>
<summary>OpenAI Chat API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py">agents.models.OpenAIChatWrapper</a></code>)</summary>

```python
openai_chat_config = {
    "config_name": "{your_config_name}",
    "model_type": "openai",

    # 必要参数
    "model_name": "gpt-4",

    # 可选参数
    "api_key": "{your_api_key}",                # OpenAI API Key，如果没有提供，将从环境变量中读取
    "organization": "{your_organization}",      # Organization name，如果没有提供，将从环境变量中读取
    "client_args": {                            # 用于初始化OpenAI API Client的参数
        # 例如："max_retries": 3,
    },
    "generate_args": {                          # 模型API接口被调用时传入的参数
        # 例如："temperature": 0.0
    },
    "budget": 100                               # API费用预算
}
```

</details>

<details>
<summary>OpenAI DALL·E API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py">agentscope.models.OpenAIDALLEWrapper</a></code>)</summary>

```python
{
    "config_name": "{your_config_name}",
    "model_type": "openai_dall_e",

    # 必要参数
    "model_name": "{model_name}",               # OpenAI model name, 例如：dall-e-2, dall-e-3

    # 可选参数
    "api_key": "{your_api_key}",                # OpenAI API Key，如果没有提供，将从环境变量中读取
    "organization": "{your_organization}",      # Organization name，如果没有提供，将从环境变量中读取
    "client_args": {                            # 用于初始化OpenAI API Client的参数
        # 例如："max_retries": 3,
    },
    "generate_args": {                          # 模型API接口被调用时传入的参数
        # 例如："n": 1, "size": "512x512"
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

    # 必要参数
    "model_name": "{model_name}",               # OpenAI model name, 例如：text-embedding-ada-002, text-embedding-3-small

    # 可选参数
    "api_key": "{your_api_key}",                # OpenAI API Key，如果没有提供，将从环境变量中读取
    "organization": "{your_organization}",      # Organization name，如果没有提供，将从环境变量中读取
    "client_args": {                            # 用于初始化OpenAI API Client的参数
        # 例如："max_retries": 3,
    },
    "generate_args": {                          # 模型API接口被调用时传入的参数
        # 例如："encoding_format": "float"
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

    # 必要参数
    "model_name": "{model_name}",               # DashScope Chat API中的模型名， 例如：qwen-max

    # 可选参数
    "api_key": "{your_api_key}",                # DashScope API Key，如果没有提供，将从环境变量中读取
    "generate_args": {
        # 例如："temperature": 0.5
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

    # 必要参数
    "model_name": "{model_name}",               # DashScope Image Synthesis API中的模型名， 例如：wanx-v1

    # 可选参数
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

    # 必要参数
    "model_name": "{model_name}",               # DashScope Text Embedding API中的模型名, 例如：text-embedding-v1

    # 可选参数
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

    # 必要参数
    "model_name": "{model_name}",               # Gemini Chat API中的模型名，例如：gemini-prp

    # 可选参数
    "api_key": "{your_api_key}",                # 如果没有提供，将从环境变量GEMINI_API_KEY中读取
}
```

</details>

<details>
<summary>Gemini Embedding API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py">agentscope.models.GeminiEmbeddingWrapper</a></code>)</summary>

```python
{
    "config_name": "my_gemini_embedding_config",
    "model_type": "gemini_embedding",

    # 必要参数
    "model_name": "{model_name}",               # Gemini Embedding API中的模型名，例如：gemini-prp

    # 可选参数
    "api_key": "{your_api_key}",                # 如果没有提供，将从环境变量GEMINI_API_KEY中读取
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

    # 必要参数
    "model": "{model_name}",                    # ollama Chat API中的模型名, 例如：llama2

    # 可选参数
    "options": {                                # 模型API接口被调用时传入的参数
        # 例如："temperature": 0., "seed": "123",
    },
    "keep_alive": "5m",                         # 控制一次调用后模型在内存中的存活时间
}
```

</details>

<details>
<summary>Ollama Generation API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py">agentscope.models.OllamaGenerationWrapper</a></code>)</summary>

```python
{
    "config_name": "my_ollama_generate_config",
    "model_type": "ollama_generate",

    # 必要参数
    "model": "{model_name}",                    # ollama Generate API, 例如：llama2

    # 可选参数
    "options": {                                # 模型API接口被调用时传入的参数
        # "temperature": 0., "seed": "123",
    },
    "keep_alive": "5m",                         # 控制一次调用后模型在内存中的存活时间
}
```

</details>

<details>
<summary>Ollama Embedding API (<code><a href="https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py">agentscope.models.OllamaEmbeddingWrapper</a></code>)</summary>

```python
{
    "config_name": "my_ollama_embedding_config",
    "model_type": "ollama_embedding",

    # 必要参数
    "model": "{model_name}",                    # ollama Embedding API, 例如：llama2

    # 可选参数
    "options": {                                # 模型API接口被调用时传入的参数
        # "temperature": 0., "seed": "123",
    },
    "keep_alive": "5m",                         # 控制一次调用后模型在内存中的存活时间
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

    # 必要参数
    "api_url": "https://xxx.xxx",
    "headers": {
        # 例如："Authorization": "Bearer xxx",
    },

    # 可选参数
    "messages_key": "messages",
}
```

</details>

## 从零搭建模型服务

针对需要自己搭建模型服务的开发者，AgentScope提供了一些脚本来帮助开发者快速搭建模型服务。您可以在[scripts](https://github.com/modelscope/agentscope/tree/main/scripts)目录下找到这些脚本以及说明。

具体而言，AgentScope提供了以下模型服务的脚本：

- 基于Flask + HuggingFace的模型服务
- 基于Flask + ModelScope的模型服务
- FastChat推理引擎
- vllm推理引擎

下面我们以Flask + hugingface的模型服务为例，介绍如何使用AgentScope的模型服务脚本。
更多的模型服务脚本可以在[scripts](https://github.com/modelscope/agentscope/blob/main/scripts/)中查看。

### 基于Flask 的模型 API 服务

[Flask](https://github.com/pallets/flask)是一个轻量级的Web应用框架。利用Flask可以很容易地搭建本地模型API服务。

#### 使用transformers库

##### 安装transformers并配置服务

按照以下命令安装 Flask 和 Transformers：

```bash
pip install Flask transformers
```

以模型 `meta-llama/Llama-2-7b-chat-hf` 和端口 `8000` 为例，通过运行以下命令来设置模型 API 服务。

```bash
python flask_transformers/setup_hf_service.py
    --model_name_or_path meta-llama/Llama-2-7b-chat-hf
    --device "cuda:0" # or "cpu"
    --port 8000
```

您可以将 `meta-llama/Llama-2-7b-chat-hf` 替换为 huggingface 模型中心的任何模型卡片。

##### 在AgentScope中调用

在 AgentScope 中，您可以使用以下模型配置加载型：[./flask_transformers/model_config.json](https://github.com/modelscope/agentscope/blob/main/scripts/flask_transformers/model_config.json)。

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

##### 注意

在这种模型服务中，来自 post 请求的消息应该是 **STRING** 格式。您可以使用来自 *transformers* 的[聊天模型模板](https://huggingface.co/docs/transformers/main/chat_templating)，只需在[`./flask_transformers/setup_hf_service.py`](https://github.com/modelscope/agentscope/blob/main/scripts/flask_transformers/setup_hf_service.py)做一点修改即可。

[[返回顶部]](#203-model-zh)
