# Llama3 in AgentScope!

AgentScope supports Llama3 now! You can
- 🚀 Set up Llama3 model service in AgentScope! Both CPU and GPU inference are supported!
- 🔧 Test Llama3 in AgentScope built-in examples!
- 🖋 Use Llama3 to build your own multi-agent applications!

Set up llama3 model service according to your hardware.

## Contents
- [CPU Inference](#cpu-inference)
  - [Setup Llama3 Service](#setup-llama3-service)
  - [Use Llama3 in AgentScope](#use-llama3-in-agentscope)
- [GPU Inference](#gpu-inference)
  - [Setup Llama3 Service](#setup-llama3-service-1)
  - [Use Llama3 in AgentScope](#use-llama3-in-agentscope-1)

## CPU Inference

### Setup Llama3 Service

AgentScope supports Llama3 CPU inference with the help of ollama.

1. download ollama from [here]().

2. pull the llama model
```bash

```
### Use Llama3 in AgentScope

Use llama3 model by the following model configuration

```python
llama3_8b_ollama_model_configuration = {

}

llama3_70b_ollama_model_configuration = {

}
```

## GPU Inference

### Setup Llama3 Service

If you have a GPU, you can set up llama3 model service with the help of Flask and Transformers quickly.

1. Install Flask and Transformers

```bash
pip install flask transformers torch
```

2. Run flask server by the following command in scripts directory:
```bash
# 8B model
python flask_transformers/setup_hf_service.py --model_name_or_path meta-llama/Meta-Llama-3-8B-Instruct --port 8000

# 70B model
python flask_transformers/setup_hf_service.py --model_name_or_path meta-llama/Meta-Llama-3-70B-Instruct --port 8000
```

### Use Llama3 in AgentScope

In AgentScope, use the following model configurations

```python
llama3_flask_model_configuration = {
  "model_type": "post_api_chat",
  "config_name": "llama-3",
  "api_url": "http://127.0.0.1:8000/llm/",
  "json_args": {
    "max_length": 4096,
    "temperature": 0.5
  }
}
```