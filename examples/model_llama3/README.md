# Llama3 in AgentScope

AgentScope supports Llama3 now! You can

- 🚀 Set up Llama3 model service in AgentScope! Both CPU and GPU inference are supported!
- 🔧 Test Llama3 in AgentScope built-in examples!
- 🖋 Use Llama3 to build your own multi-agent applications!

Set up llama3 model service according to your hardware.

## Contents

- [Llama3 in AgentScope](#llama3-in-agentscope)
  - [Contents](#contents)
  - [CPU Inference](#cpu-inference)
    - [Setup Llama3 Service](#setup-llama3-service)
    - [Use Llama3 in AgentScope](#use-llama3-in-agentscope)
  - [GPU Inference](#gpu-inference)
    - [Setup Llama3 Service](#setup-llama3-service-1)
    - [Use Llama3 in AgentScope](#use-llama3-in-agentscope-1)

## CPU Inference

### Setup Llama3 Service

AgentScope supports Llama3 CPU inference with the help of ollama.

1. download ollama from [here](https://ollama.com/).

2. start ollama service

   ```bash
   ollama serve
   ```

3. pull the llama model

   ```bash
   # llama3 8b model
   ollama pull llama3

   # llama3 70b model
   ollama pull llama3:70b
   ```

### Use Llama3 in AgentScope

Use llama3 model by the following model configuration

```python
llama3_8b_ollama_model_configuration = {
   "config_name": "ollama_llama3_8b",
   "model_type": "ollama_chat",
   "model_name": "llama3",
   "options": {
       "temperature": 0.5,
       "seed": 123
   },
   "keep_alive": "5m"
}

llama3_70b_ollama_model_configuration = {
   "config_name": "ollama_llama3_70b",
   "model_type": "ollama_chat",
   "model_name": "llama3:70b",
   "options": {
       "temperature": 0.5,
       "seed": 123
   },
   "keep_alive": "5m"
}
```

## GPU Inference

### Setup Llama3 Service

If you have a GPU, you can set up llama3 model service with the help of Flask and Transformers quickly.

1. Install Flask and Transformers

```bash
pip install flask transformers torch
```

2. Run flask server by the following command  

```bash
python flask_llama3_server.py
```

### Use Llama3 in AgentScope

In AgentScope, use the following model configurations

```python
llama3_8b_flask_model_configuration = {
    
}

llama3_70b_flask_model_configuration = {
    
}
```