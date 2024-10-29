# Distributed Conversation

This example will show
- How to set up and run a distributed conversation.
- How to configure and use different language models in the system.

## Background

This example demonstrates a distributed dialog system leveraging various language models. The system is designed to handle conversational AI tasks in a distributed manner, allowing for scalable and efficient dialog management.

## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- Ollama Chat (llama3_8b)
- Dashscope Chat (qwen-Max)
- Gemini Chat (gemini-pro)

## Prerequisites

Before running the example, please install the distributed version of Agentscope, fill in your model configuration correctly in `configs/model_configs.json`, and modify the `model_config_name` field in `distributed_dialog.py` accordingly.

## Running the Example
Use the following command to start the assistant agent:

```
cd examples/distributed_conversation
python distributed_dialog.py --role assistant --assistant-host localhost --assistant-port 12010
# Please make sure the port is available.
# If the assistant agent and the user agent are started on different machines,
# please fill in the ip address of the assistant agent in the host field
```

Then, run the user agent:

```
python distributed_dialog.py --role user --assistant-host localhost --assistant-port 12010
# If the assistant agent is started on another machine,
# please fill in the ip address of the assistant agent in the host field
```

Now, you can chat with the assistant agent using the command line.