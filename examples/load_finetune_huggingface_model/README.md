# Multi-Agent Conversation in AgentScope with Loading/Fune-tuning Custom Model Functionality
This is a demo of how to load (and/or fine-tune) Hugging Face model in a multi-agent conversation setting in AgentScope.
Complete code is in `load_finetune_huggingface_model.py`, which set up a user agent and an assistant agent to have a conversation. When user input "exit", the
conversation ends. You can modify the `sys_prompt` to change the role of assistant agent. 

In addition to the basic functionalities of conversation_basic, you can use
`dialog_agent.load_model(model_id, local_model_path)` to either load a model from the Hugging Face Model Hub or from a local path for an exisiting agent, and can use `dialog_agent.fine_tune(data_path)` to fine-tune the backbone model of the agent. When initializing an agent, since you are loading an acutal model as opposed to calling a model API, there are a few additional arguments to be specified:
model_id: model_id (str): An identifier for the model on Huggingface;
local_model_path (str): The file path to the model to be loaded (if loading from a local path; if not specified in `model_configs` will by default load model from huggingface based on `model_id`);
data_path (str): The file path to the training data (if not specified in `model_configs` will by default not do fine-tuning);
device (str): The device on which the model is to be loaded. If not specified will set to 'cuda' by default if cuda is available, otherwise will set to 'cpu' by default;
huggingface_token (str in an .env file): Your huggingface token for downloading models that require authentication.

```bash
# Note: Set your huggingface token in .env file first
python load_finetune_huggingface_model.py
```

The hyperparameters for (SFT) fine-tuning need to be specified in `huggingface_model.py`.

Additional packages neeeded: transformers, peft, python-dotenv, pytorch, datasets, trl.