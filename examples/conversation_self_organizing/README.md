# Self-Organizing Conversation Example

This example will show
- How to set up a self-organizing conversation using the `DialogAgent` and `agent_builder`
- How to extract the discussion scenario and participant agents from the `agent_builder`'s response
- How to conduct a multi-round discussion among the participant agents


## Background

In this example, we demonstrate how to create a self-organizing conversation where the `agent_builder` automatically sets up the agents participating in the discussion based on a given question. The `agent_builder` provides the discussion scenario and the characteristics of the participant agents. The participant agents then engage in a multi-round discussion to solve the given question.


## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- `dashscope_chat` with `qwen-turbo`
- `ollama_chat` with `llama3_8b`
- `gemini_chat` with `models/gemini-1.0-pro-latest`


## Prerequisites

Fill the next cell to meet the following requirements
- Set up the `model_configs` with the appropriate API keys and endpoints
- Provide the path to the `agent_builder_instruct.txt` file in the `load_txt` function
- Set the desired `max_round` for the discussion
- Provide the `query` or question for the discussion
- [Optional] Adjust the `generate_args` such as `temperature` for the `openai_chat` model