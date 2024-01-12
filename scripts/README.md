# Set up Model API Serving

In AgentScope, in addition to OpenAI API, we also support open-source
models with post request API. In this document, we will introduce how to
fast set up local model API serving with different inference engines.

Table of Contents
=================
* [Local Model API Serving](#local-model-api-serving)
  * [Flask-based Model API Serving](#flask-based-model-api-serving)
    * [With Transformers Library](#with-transformers-library)
      * [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving)
      * [How to use in AgentScope](#how-to-use-in-agentscope)
      * [Note](#note)
    * [With ModelScope Library](#with-modelscope-library)
      * [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving-1)
      * [How to use in AgentScope](#how-to-use-in-agentscope-1)
      * [Note](#note-1)
    * [FastChat](#fastchat)
      * [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving-2)
      * [Supported Models](#supported-models)
      * [How to use in AgentScope](#how-to-use-in-agentscope-2)
    * [vllm](#vllm)
      * [Install Libraries and Set up Serving](#install-libraries-and-set-up-serving-3)
      * [Supported Models](#supported-models-1)
      * [How to use in AgentScope](#how-to-use-in-agentscope-3)
* [Model Inference API](#model-inference-api)




## Local Model API Serving

### Flask-based Model API Serving

[Flask](https://github.com/pallets/flask) is a lightweight web application
framework. It is easy to build a local model API serving with Flask.

Here we provide two Flask examples with Transformers and ModelScope library,
respectively. You can build your own model API serving with few modifications.

#### With Transformers Library

##### Install Libraries and Set up Serving

Install Flask and Transformers by following command.

```bash
pip install Flask, transformers
```

Taking model `meta-llama/Llama-2-7b-chat-hf` and port `8000` as an example,
set up the model API serving by running the following command.
```bash
python flask_transformers/setup_hf_service.py
    --model_name_or_path meta-llama/Llama-2-7b-chat-hf
    --device "cuda:0" # or "cpu"
    --port 8000
```

You can replace `meta-llama/Llama-2-7b-chat-hf` with any model card in
huggingface model hub.

##### How to use in AgentScope

In AgentScope, you can load the model with the following model configs: `./flask_transformers/model_config.json`.

```json
{
    "type": "post_api",
    "name": "flask_llama2-7b-chat",
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
pip install Flask, modelscope
```

Taking model `modelscope/Llama-2-7b-ms` and port `8000` as an example,
to set up the model API serving, run the following command.

```bash
python flask_modelscope/setup_ms_service.py
    --model_name_or_path modelscope/Llama-2-7b-ms
    --device "cuda:0" # or "cpu"
    --port 8000
```

You can replace `modelscope/Llama-2-7b-ms` with any model card in
modelscope model hub.


##### How to use in AgentScope

In AgentScope, you can load the model with the following model configs:
`flask_modelscope/model_config.json`.

```json
{
    "type": "post_api",
    "name": "flask_llama2-7b-ms",
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
pip install "fastchat[model_worker,webui]"
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
    "type": "openai",
    "name": "meta-llama/Llama-2-7b-chat-hf",
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
bash vllm_script/vllm_setup.sh -m meta-llama/Llama-2-7b-chat-hf -p 8000
```

#### Supported models

Please refer to the
[supported models list](https://docs.vllm.ai/en/latest/models/supported_models.html)
of vllm.

#### How to use in AgentScope
Now you can load the model in AgentScope by the following model config: `vllm_script/model_config.json`.

```json
{
    "type": "openai",
    "name": "meta-llama/Llama-2-7b-chat-hf",
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

```bash
{
    "type": "post_api",
    "name": 'gpt2',
    "headers": {
        "Authorization": "Bearer {YOUR_API_TOKEN}"
    }
    "api_url": "https://api-inference.huggingface.co/models/gpt2"
}
```