(203-model)=

# Using Different Model Sources with Model API

AgentScope allows for the integration of multi-modal models from various sources. The core step is the initialization process, where once initialized with a certain config, all agent instances globally select the appropriate model APIs based on the model name specified (e.g., `model='gpt-4'`):

```python
import agentscope

agentscope.init(model_configs=PATH_TO_MODEL_CONFIG)
```

where the model configs could be a list of dict:

```json
[
    {
        "config_name": "gpt-4-temperature-0.0",
        "model_type": "openai",
        "model": "gpt-4",
        "api_key": "xxx",
        "organization": "xxx",
        "generate_args": {
            "temperature": 0.0
        }
    },
    {
        "config_name": "dall-e-3-size-1024x1024",
        "model_type": "openai_dall_e",
        "model": "dall-e-3",
        "api_key": "xxx",
        "organization": "xxx",
        "generate_args": {
            "size": "1024x1024"
        }
    },
    // Additional models can be configured here
]
```

This allows users to configure the model once, enabling shared use across all agents within the multi-agent application. Here is a table outlining the supported APIs and the type of arguments required for each:

|   Model Usage               | Type Argument in AgentScope     | Supported APIs                                                         |
| -------------------- | ------------------ | ------------------------------------------------------------ |
| Text generation     | `openai`           | Standard OpenAI chat API, FastChat and vllm                     |
| Image generation   | `openai_dall_e`    | DALL-E API for generating images                             |
| Embedding | `openai_embedding` | API for text embeddings                                      |
| General usages in POST       | `post_api`         | Huggingface/ModelScope Inference API, and customized post API |

## Standard OpenAI API

Our configuration is fully compatible with the Standard OpenAI API. For specific parameter configuration and usage guides, we recommend visiting their official website: [https://platform.openai.com/docs/api-reference/introduction](https://platform.openai.com/docs/api-reference/introduction).

## Self-host Model API

In AgentScope, in addition to OpenAI API, we also support open-source models with post-request API. In this document, we will introduce how to fast set up local model API serving with different inference engines.

### Flask-based Model API Serving

[Flask](https://github.com/pallets/flask) is a lightweight web application framework. It is easy to build a local model API serving with Flask.

Here we provide two Flask examples with Transformers and ModelScope libraries, respectively. You can build your own model API serving with a few modifications.

#### With Transformers Library

##### Install Libraries and Set up Serving

Install Flask and Transformers by following the command.

```bash
pip install Flask, transformers
```

Taking model `meta-llama/Llama-2-7b-chat-hf` and port `8000` as an example, set up the model API serving by running the following command.

```bash
python flask_transformers/setup_hf_service.py
    --model_name_or_path meta-llama/Llama-2-7b-chat-hf
    --device "cuda:0" # or "cpu"
    --port 8000
```

You can replace `meta-llama/Llama-2-7b-chat-hf` with any model card in the huggingface model hub.

##### How to use in AgentScope

In AgentScope, you can load the model with the following model configs: `./flask_transformers/model_config.json`.

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

In this model serving, the messages from post requests should be in **STRING** format. You can use [templates for chat model](https://huggingface.co/docs/transformers/main/chat_templating) from *transformers* with a little modification based on `./flask_transformers/setup_hf_service.py`.

#### With ModelScope Library

##### Install Libraries and Set up Serving

Install Flask and modelscope by following the command.

```bash
pip install Flask, modelscope
```

Taking model `modelscope/Llama-2-7b-ms` and port `8000` as an example, to set up the model API serving, run the following command.

```bash
python flask_modelscope/setup_ms_service.py
    --model_name_or_path modelscope/Llama-2-7b-ms
    --device "cuda:0" # or "cpu"
    --port 8000
```

You can replace `modelscope/Llama-2-7b-ms` with any model card in modelscope model hub.

##### How to use AgentScope

In AgentScope, you can load the model with the following model configs: `flask_modelscope/model_config.json`.

```json
{
    "model_type": "post_api",
    "config_name": "flask_llama2-7b-ms",
    "api_url": "http://127.0.0.1:8000/llm/",
    "json_args": {
        "max_length": 4096,
        "temperature": 0.5
    }
}
```

##### Note

Similar to the example of transformers, the messages from post requests should be in **STRING format**.

### FastChat

[FastChat](https://github.com/lm-sys/FastChat) is an open platform that provides a quick setup for model serving with OpenAI-compatible RESTful APIs.

#### Install Libraries and Set up Serving

To install FastChat, run

```bash
pip install "fastchat[model_worker,webui]"
```

Taking model `meta-llama/Llama-2-7b-chat-hf` and port `8000` as an example, to set up model API serving, run the following command to set up model serving.

```bash
bash fastchat_script/fastchat_setup.sh -m meta-llama/Llama-2-7b-chat-hf -p 8000
```

#### Supported Models

Refer to [supported model list](https://github.com/lm-sys/FastChat/blob/main/docs/model_support.md#supported-models) of FastChat.

#### How to use in AgentScope

Now you can load the model in AgentScope by the following model config: `fastchat_script/model_config.json`.

```json
{
    "config_name": "meta-llama/Llama-2-7b-chat-hf",
    "model_type": "openai",
    "api_key": "EMPTY",
    "client_args": {
        "base_url": "http://127.0.0.1:8000/v1/"
    },
    "generate_args": {
        "temperature": 0.5
    }
}
```

### vllm

[vllm](https://github.com/vllm-project/vllm) is a high-throughput inference and serving engine for LLMs.

#### Install Libraries and Set up Serving

To install vllm, run

```bash
pip install vllm
```

Taking model `meta-llama/Llama-2-7b-chat-hf` and port `8000` as an example, to set up model API serving, run

```bash
bash vllm_script/vllm_setup.sh -m meta-llama/Llama-2-7b-chat-hf -p 8000
```

#### Supported models

Please refer to the [supported models list](https://docs.vllm.ai/en/latest/models/supported_models.html) of vllm.

#### How to use in AgentScope

Now you can load the model in AgentScope by the following model config: `vllm_script/model_config.json`.

```json
{
    "config_name": "meta-llama/Llama-2-7b-chat-hf",
    "model_type": "openai",
    "api_key": "EMPTY",
    "client_args": {
        "base_url": "http://127.0.0.1:8000/v1/"
    },
    "generate_args": {
        "temperature": 0.5
    }
}
```

## Model Inference API

Both [Huggingface](https://huggingface.co/docs/api-inference/index) and [ModelScope](https://www.modelscope.cn) provide model inference API, which can be used with AgentScope post API model wrapper.
Taking `gpt2` in HuggingFace inference API as an example, you can use the following model config in AgentScope.

```json
{
    "config_name": "gpt2",
    "model_type": "post_api",
    "headers": {
        "Authorization": "Bearer {YOUR_API_TOKEN}"
    }
    "api_url": "https://api-inference.huggingface.co/models/gpt2"
}
```

## In-memory Models without API

It is entirely possible to use models without setting up an API service. Here's an example of how to initialize an agent with a local model instance:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model.eval()
# Do remember to re-implement the `reply` method to tokenize *message*!
agent = YourAgent(name='agent', model_config_name=config_name, tokenizer=tokenizer)
```

[[Return to the top]](#using-different-model-sources-with-model-api)
