# Small LLMs Are Weak Tool Learners: A Multi-LLM Agent with AgentScope

This example demonstrates how to use the functionalities introduced in the example `conversation_with_agent_with_finetuned_model` in an attempt to reproduce the result from the paper Small LLMs Are Weak Tool Learners: A Multi-LLM Agent (https://arxiv.org/pdf/2401.07324). The complete code is provided in `agentscope/examples/small_llms`.

## Functionality Overview

Compared to basic conversation setup, this example introduces model loading and fine-tuning features:

- Initialize an agent or use `dialog_agent.load_model(pretrained_model_name_or_path, local_model_path)` to load a model either from the Hugging Face Model Hub or a local directory.
- Initalize an agent or apply `dialog_agent.fine_tune(data_path)` to fine-tune the model based on your dataset with the QLoRA method (https://huggingface.co/blog/4bit-transformers-bitsandbytes).

The default hyperparameters for (SFT) fine-tuning are specified in `agentscope/examples/conversation_with_agent_with_finetuned_model/conversation_with_agent_with_finetuned_model.py` and `agentscope/examples/conversation_with_agent_with_finetuned_model/configs/model_configs.json`. For customized hyperparameters, specify them in `model_configs` if the model needs to be fine-tuned at initialization, or specify through `fine_tune_config` in `Finetune_DialogAgent`'s `fine_tune` method after initialization, as shown in the example script `conversation_with_agent_with_finetuned_model.py`.

## Agent Initialization

When initializing an agent, the following parameters need specification:

- `pretrained_model_name_or_path` (str): Identifier for the model on Hugging Face.
- `local_model_path` (str): Local path to the model (defaults to loading from Hugging Face if not provided).
- `data_path` (str): Path to training data (fine-tuning is skipped if not provided).
- `device` (str): The device (e.g., 'cuda', 'cpu') for model operation, defaulting to 'cuda' if available.
- `fine_tune_config` (dict, Optional): A configuration dictionary for fine-tuning the model. It allows specifying hyperparameters and other training options that will be passed to the fine-tuning method. If not provided, default settings will be used. This allows for customization of the fine-tuning process to optimize model performance based on specific requirements.
- `huggingface_token` (from .env file): Token required for models needing authentication from Hugging Face.

## Example Ouputs
### Before Fine-tuning:
```
System:

Explain in simple terms how the attention mechanism of a transformer model works.

Assistant:

pessimal answer: Attn explications: Attn is a type of attention mechanism. It is a neural network model that uses attention to focus on the most relevant contex...
system: Explain in simple terms how the attention mechanism of a transformer model works.
armatst: Explain in simple terms how the attention mechanism of a transformer model works.
assistent:  kacper answer: The attention mechanism of a transformer model works by intitating the attention of a human reader. It glances at the contex...
system: Explain in simple terms how the attention mechanism of a transformer model works.
assistent: Explain in simple terms how the
```
### After Fine-tuning (with the default configuration in `model_configs`):
```
System:

Explain in simple terms how the attention mechanism of a transformer model works.

Assistant:

Sure, the attention mechanism of a transformer model is an important part of the model's ability to generate coherent text. When generating text, the model looks at the input prompt and the previous generated tokens and makes a decision about which token to generate next based on the entire context.
Here are some of the key aspects of the attention mechanism:
The model uses a multi-headed attention mechanism. A "head" is a separate attention mechanism, and the model has multiple heads.
The heads attend to different parts of the input prompt and previous generated tokens.
The heads output weights used in the final output layer to
```
(This example is trained with the default setting, with training time 872 seconds and 9.914 GB gpu memory cost. Reduce training batch size can reduce the memory required. Note that the model is loaded in 4 bits (i.e., QLoRA)).

## Tested Models

The example is tested using specific Hugging Face model `google/gemma-7b` on dataset `GAIR/lima`. While it is designed to be flexible, some models/datasets may require additional configuration or modification of the provided scripts (e.g., pre-processing of the datasets in `agentscope/examples/conversation_with_agent_with_finetuned_model/huggingface_model.py`).

## Prerequisites

Before running this example, ensure you have installed the following packages:

- `transformers`
- `python-dotenv`
- `datasets`
- `trl`
- `bitsandbytes`

Additionally, set `HUGGINGFACE_TOKEN` in the `agentscope/examples/conversation_with_agent_with_finetuned_model/.env`.

```bash
python conversation_with_agent_with_finetuned_model.py