# Multi-Agent Conversation with Custom Model Loading and Fine-Tuning in AgentScope

This example demonstrates how to load and optionally fine-tune a Hugging Face model within a multi-agent conversation setup using AgentScope. The complete code is provided in `agentscope/examples/conversation_with_agent_with_finetuned_model`.

## Functionality Overview

Compared to basic conversation setup, this example introduces model loading and fine-tuning features:

- Use `dialog_agent.load_model(model_id, local_model_path)` to load a model either from the Hugging Face Model Hub or a local directory.
- Apply `dialog_agent.fine_tune(data_path)` to fine-tune the model based on your dataset.

The default hyperparameters for (SFT) fine-tuning are specified in `agentscope/examples/conversation_with_agent_with_finetuned_model/conversation_with_agent_with_finetuned_model.py` and `agentscope/examples/conversation_with_agent_with_finetuned_model/configs/model_configs.json`. For customized hyperparameters, specify them in `model_configs` if the model needs to be fine-tuned at initialization, or specify through `fine_tune_config` in `Finetune_DialogAgent`'s `fine_tune` method after initialization, as shown in the example script `conversation_with_agent_with_finetuned_model.py`.

## Agent Initialization

When initializing an agent, the following parameters need specification:

- `model_id` (str): Identifier for the model on Hugging Face.
- `local_model_path` (str): Local path to the model (defaults to loading from Hugging Face if not provided).
- `data_path` (str): Path to training data (fine-tuning is skipped if not provided).
- `device` (str): The device (e.g., 'cuda', 'cpu') for model operation, defaulting to 'cuda' if available.
- `fine_tune_config` (dict, Optional): A configuration dictionary for fine-tuning the model. It allows specifying hyperparameters and other training options that will be passed to the fine-tuning method. If not provided, default settings will be used. This allows for customization of the fine-tuning process to optimize model performance based on specific requirements.
- `huggingface_token` (from .env file): Token required for models needing authentication from Hugging Face.

## Example Ouputs
### Before Fine-tuning:
User:

Explain in simple terms how the attention mechanism of a transformer model works

Assistant:

1. a person who helps another person or group of people. 2. a person who helps another person or group of people.

### After Fine-tuning (with the default configuration in `model_configs`):
User:

Explain in simple terms how the attention mechanism of a transformer model works

Assistant:

The attention mechanism of a transformer model works by allowing the model to focus on different parts of the input sequence at different times. This is done by using a combination of self-attention and position-wise attention.

The self-attention mechanism allows the model to focus on different parts of the input sequence at different times. This is done by using a combination of self-attention and position-wise attention.

The position-wise attention mechanism allows the model to focus on different parts of the input sequence at different times. This is done by using a combination of self-attention and position-wise attention.

The self


## Tested Models

The example is tested using specific Hugging Face model `openlm-research/open_llama_3b_v2` on dataset `databricks/databricks-dolly-15k`. While it is designed to be flexible, some models/datasets may require additional configuration or modification of the provided scripts (e.g., pre-processing of the datasets).

## Prerequisites

Before running this example, ensure you have installed the following packages:

- `transformers`
- `peft`
- `python-dotenv`
- `datasets`
- `trl`

Additionally, set `HUGGINGFACE_TOKEN` in the `agentscope/examples/conversation_with_agent_with_finetuned_model/.env`.

```bash
python conversation_with_agent_with_finetuned_model.py