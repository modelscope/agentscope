# Conversation with gpt-4o (OpenAI Vision Model)

This example will show
- How to use gpt-4o and other OpenAI vision models in AgentScope

In this example,
- you can have a conversation with OpenAI vision models.
- you can show gpt-4o with your drawings or web ui designs and look for its suggestions.
- you can share your pictures with gpt-4o and ask for its comments,

Just input your image url (both local and web URLs are supported) and talk with gpt-4o.


## Background

In May 13, 2024, OpenAI released their new model, gpt-4o, which is a large multimodal model that can process both text and multimodal data.


## Tested Models

The following models are tested in this example. For other models, some modifications may be needed.
- gpt-4o
- gpt-4-turbo
- gpt-4-vision


## Prerequisites

You need to satisfy the following requirements to run this example.
- Install the latest version of AgentScope by
    ```bash
    git clone https://github.com/modelscope/agentscope.git
    cd agentscope
    pip install -e .
    ```
- Prepare an OpenAI API key

## Running the Example

First fill your OpenAI API key in `conversation_with_gpt-4o.py`, then execute the following command to run the conversation with gpt-4o.

```bash
python conversation_with_gpt-4o.py
```

## A Running Example

- Conversation history with gpt-4o.

<img src="https://img.alicdn.com/imgextra/i4/O1CN01oQHcmy1mHXALklkMe_!!6000000004929-2-tps-5112-1276.png" alt="conversation history"/>

- My picture

<img src="https://img.alicdn.com/imgextra/i3/O1CN01UpQaLN27hjidUipMv_!!6000000007829-0-tps-720-1280.jpg" alt="my picture" width="200" />
