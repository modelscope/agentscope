(203-model-zh)=

# 关于模型

AgentScope中，模型的部署和调用是通过`ModelWrapper`来解耦开的，开发者可以通过提供模型配置（Model config）的方式指定模型，同时AgentScope也提供脚本支持开发者自定义模型服务。

## 支持模型

目前，AgentScope内置以下模型服务API的支持：

- OpenAI API，包括对话（Chat），图片生成（DALL-E)和文本嵌入（Embedding）。
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

| 任务     | model_type         | ModelWrapper             | 支持的 API                                                    |
|--------|--------------------|--------------------------|------------------------------------------------------------|
| 文本生成   | `openai`           | `OpenAIChatWrapper`      | 标准 OpenAI 聊天 API，FastChat 和 vllm                           |
| 图像生成   | `openai_dall_e`    | `OpenAIDALLEWrapper`     | 用于生成图像的 DALL-E API                                         |
| 文本嵌入   | `openai_embedding` | `OpenAIEmbeddingWrapper` | 用于文本嵌入的 API                                                |
| POST请求 | `post_api`         | `PostAPIModelWrapperBase` | Huggingface/ModelScope inference API 和自定义的post request API |

#### 详细参数

根据`ModelWrapper`的不同，详细参数中所包含的参数不同。
但是所有的详细参数都会用于初始化`ModelWrapper`类的实例，因此，更详细的参数说明可以根据`ModelWrapper`类的构造函数来查看。

- OpenAI的API，包括文本生成，图像生成，文本嵌入，其模型配置参数如下

```python
{
    # 基础参数
    "config_name": "gpt-4_temperature-0.0",
    "model_type": "openai",

    # 详细参数
    # 必要参数
    "model_name": "gpt-4",          # OpenAI模型名称

    # 可选参数
    "api_key": "xxx",               # OpenAI API Key，如果没有提供则会从环境变量中读取
    "organization": "xxx",          # 组织名称，如果没有提供则会从环境变量中读取
    "client_args": {                # 初始化OpenAI API Client的参数
        "max_retries": 3,
    },
    "generate_args": {              # 调用模型时传入的参数
        "temperature": 0.0
    },
    "budget": 100.0                 # API费用预算
}
```

- Post request API，其模型配置参数如下

```python
{
    # 基础参数
    "config_name": "gpt-4_temperature-0.0",
    "model_type": "post_api",

    # 详细参数
    "api_url": "http://xxx.png",
    "headers": {
        # e.g. "Authorization": "Bearer xxx",
    },

    # 可选参数，需要根据Post请求API的要求进行配置
    "json_args": {
        # e.g. "temperature": 0.0
    }
    # ...
}
```

## 从零搭建模型服务

针对需要自己搭建模型服务的开发者，AgentScope提供了一些脚本来帮助开发者快速搭建模型服务。您可以在[scripts]
(<https://github.com/modelscope/agentscope/tree/main/scripts)目录下找到这些脚本以及说明。>

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
