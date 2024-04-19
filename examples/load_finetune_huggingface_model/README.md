# Multi-Agent Conversation with Custom Model Loading and Fine-Tuning in AgentScope

This example demonstrates how to load and optionally fine-tune a Hugging Face model within a multi-agent conversation setup using AgentScope. The complete code is provided in `load_finetune_huggingface_model.py`.

## Background

In the context of AgentScope, agents are designed to mimic user and assistant roles in a conversation. This setup allows for the integration and testing of different models from the Hugging Face Hub, enhancing their capabilities through fine-tuning with custom datasets.

## Functionality Overview

This example allows you to:

- Set up a user agent and an assistant agent for interactive conversations.
- Modify the `sys_prompt` to customize the assistant agent's role.
- Terminate the conversation by entering "exit".

## Advanced Features

Beyond basic conversation setup, the example introduces advanced functionalities:

- Use `dialog_agent.load_model(model_id, local_model_path)` to load a model either from the Hugging Face Model Hub or a local directory.
- Apply `dialog_agent.fine_tune(data_path)` to fine-tune the model based on your dataset.

## Agent Initialization

When initializing an agent, the following parameters need specification:

- `model_id` (str): Identifier for the model on Hugging Face.
- `local_model_path` (str): Local path to the model (defaults to loading from Hugging Face if not provided).
- `data_path` (str): Path to training data (fine-tuning is skipped if not provided).
- `device` (str): The device (e.g., 'cuda', 'cpu') for model operation, defaulting to 'cuda' if available.
- `huggingface_token` (from .env file): Token required for models needing authentication from Hugging Face.

## Tested Models

The example is tested using specific Hugging Face models. While it is designed to be flexible, some models may require additional configuration or modification of the provided scripts.

## Prerequisites

Before running this example, ensure you have installed the following packages:

- `transformers`
- `peft`
- `python-dotenv`
- `pytorch`
- `datasets`
- `trl`

Additionally, set your Hugging Face token in the `.env` file:

```bash
python load_finetune_huggingface_model.py
