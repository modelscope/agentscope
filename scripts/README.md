# Set up Local Model API Serving

AgentScope supports developers to build their local model API serving with different inference engines/libraries.
This document will introduce how to fast build their local API serving with provided scripts.

Table of Contents
=================

- [Local Model API Serving](#local-model-api-serving)
  - [ollama](#ollama)
    - [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving)
    - [How to use in AgentScope](#how-to-use-in-agentscope)
  - [Flask-based Model API Serving](#flask-based-model-api-serving)
    - [With Transformers Library](#with-transformers-library)
      - [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving)
      - [How to use in AgentScope](#how-to-use-in-agentscope-1)
      - [Note](#note)
    - [With ModelScope Library](#with-modelscope-library)
      - [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving-1)
      - [How to use in AgentScope](#how-to-use-in-agentscope-2)
      - [Note](#note-1)
  - [FastChat](#fastchat)
    - [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving-2)
    - [Supported Models](#supported-models)
    - [How to use in AgentScope](#how-to-use-in-agentscope-3)
  - [vllm](#vllm)
    - [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving-3)
    - [Supported models](#supported-models-1)
    - [How to use in AgentScope](#how-to-use-in-agentscope-4)
- [Model Inference API](#model-inference-api)

## Local Model API Serving

### ollama

[ollama](https://github.com/ollama/ollama) is a CPU inference engine for LLMs. With ollama, developers can build their local model API serving without GPU requirements.

#### Install Libraries and Set up Serving

- First, install ollama in its [official repository](https://github.com/ollama/ollama) based on your system (e.g. macOS, windows or linux).

- Follow ollama's [guidance](https://github.com/ollama/ollama) to pull or create a model and start its serving. Taking llama2 as an example, you can run the following command to pull the model files.

```bash
ollama pull llama2
```

#### How to use in AgentScope

In AgentScope, you can use the following model configurations to load the model.

- For ollama Chat API:

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

- For ollama generate API:

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

- For ollama embedding API:

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

### Flask-based Model API Serving

[Flask](https://github.com/pallets/flask) is a lightweight web application
framework. It is easy to build a local model API serving with Flask.

Here we provide two Flask examples with Transformers and ModelScope library,
respectively. You can build your own model API serving with few modifications.

#### With Transformers Library

##### Install Libraries and Set up Serving

Install Flask and Transformers by following command.

```bash
pip install flask torch transformers accelerate
```

Taking model `meta-llama/Llama-2-7b-chat-hf` and port `8000` as an example,
set up the model API serving by running the following command.

```shell
python flask_transformers/setup_hf_service.py \
    --model_name_or_path meta-llama/Llama-2-7b-chat-hf \
    --device "cuda:0" \
    --port 8000
```

You can replace `meta-llama/Llama-2-7b-chat-hf` with any model card in
huggingface model hub.

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

In this model serving, the messages from post requests should be in **STRING
format**. You can use [templates for chat model](https://huggingface.co/docs/transformers/main/chat_templating) in
transformers with a little modification in `./flask_transformers/setup_hf_service.py`.

#### With ModelScope Library

##### Install Libraries and Set up Serving

Install Flask and modelscope by following command.

```bash
pip install flask torch modelscope
```

Taking model `modelscope/Llama-2-7b-ms` and port `8000` as an example,
to set up the model API serving, run the following command.

```bash
python flask_modelscope/setup_ms_service.py \
    --model_name_or_path modelscope/Llama-2-7b-ms \
    --device "cuda:0" \
    --port 8000
```

You can replace `modelscope/Llama-2-7b-ms` with any model card in
modelscope model hub.

##### How to use in AgentScope

In AgentScope, you can load the model with the following model configs:
`flask_modelscope/model_config.json`.

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

Similar with the example of transformers, the messages from post requests
should be in **STRING format**.

### FastChat

[FastChat](https://github.com/lm-sys/FastChat) is an open platform that
provides quick setup for model serving with OpenAI-compatible RESTful APIs.

#### Install Libraries and Set up Serving

To install FastChat, run

```bash
pip install "fschat[model_worker,webui]"
```

Taking model `meta-llama/Llama-2-7b-chat-hf` and port `8000` as an example,
to set up model API serving, run the following command to set up model serving.

```bash
bash fastchat_script/fastchat_setup.sh -m meta-llama/Llama-2-7b-chat-hf -p 8000
```

#### Supported Models

Refer to
[supported model list](https://github.com/lm-sys/FastChat/blob/main/docs/model_support.md#supported-models)
of FastChat.

#### How to use in AgentScope

Now you can load the model in AgentScope by the following model config: `fastchat_script/model_config.json`.

```json
{
    "model_type": "openai",
    "config_name": "meta-llama/Llama-2-7b-chat-hf",
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

[vllm](https://github.com/vllm-project/vllm) is a high-throughput inference
and serving engine for LLMs.

#### Install Libraries and Set up Serving

To install vllm, run

```bash
pip install vllm
```

Taking model `meta-llama/Llama-2-7b-chat-hf` and port `8000` as an example,
to set up model API serving, run

```bash
./vllm_script/vllm_setup.sh -m meta-llama/Llama-2-7b-chat-hf -p 8000
```

#### Supported models

Please refer to the
[supported models list](https://docs.vllm.ai/en/latest/models/supported_models.html)
of vllm.

#### How to use in AgentScope

Now you can load the model in AgentScope by the following model config: `vllm_script/model_config.json`.

```json
{
    "model_type": "openai",
    "config_name": "meta-llama/Llama-2-7b-chat-hf",
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

Both [Huggingface](https://huggingface.co/docs/api-inference/index) and
[ModelScope](https://www.modelscope.cn) provide model inference API,
which can be used with AgentScope post api model wrapper.
Taking `gpt2` in HuggingFace inference API as an example, you can use the
following model config in AgentScope.

```json
{
    "model_type": "post_api",
    "config_name": "gpt2",
    "headers": {
        "Authorization": "Bearer {YOUR_API_TOKEN}"
    },
    "api_url": "https://api-inference.huggingface.co/models/gpt2"
}
```
