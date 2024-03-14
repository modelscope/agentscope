(206-prompt-en)=

# Prompt Engine

**Prompt** is a crucial component in interacting with language models,
especially when seeking to generate specific types of outputs or guide the
model toward desired behaviors.
AgentScope allows developers to customize prompts according to their needs,
and provides the `PromptEngine` class to simplify the process of crafting
prompts for large language models (LLMs).
This tutorial will guide you through the
use of the `PromptEngine` class, which simplifies the process of crafting
prompts for LLMs.

## About `PromptEngine` Class

The `PromptEngine` class provides a structured way to combine different components of a prompt, such as instructions, hints, dialogue history, and user inputs, into a format that is suitable for the underlying language model.

### Key Features of PromptEngine

- **Model Compatibility**: It works with any `ModelWrapperBase` subclass.
- **Prompt Type**: It supports both string and list-style prompts, aligning with the model's preferred input format.

### Initialization

When creating an instance of `PromptEngine`, you can specify the target model and, optionally, the shrinking policy, the maximum length of the prompt, the prompt type, and a summarization model (could be the same as the target model).

```python
model = OpenAIWrapper(...)
engine = PromptEngine(model)
```

### Joining Prompt Components

The `join` method of `PromptEngine` provides a unified interface to handle an arbitrary number of components for constructing the final prompt.

#### Output String Type Prompt

If the model expects a string-type prompt, components are joined with a newline character:

```python
system_prompt = "You're a helpful assistant."
memory = ... # can be dict, list, or string
hint_prompt = "Please respond in JSON format."

prompt = engine.join(system_prompt, memory, hint_prompt)
# the result will be [ "You're a helpful assistant.", {"name": "user", "content": "What's the weather like today?"}]
```

#### Output List Type Prompt

For models that work with list-type prompts,e.g., OpenAI and Huggingface chat models, the components can be converted to Message objects, whose type is list of dict:

```python
system_prompt = "You're a helpful assistant."
user_messages = [{"name": "user", "content": "What's the weather like today?"}]

prompt = engine.join(system_prompt, user_messages)
# the result should be: [{"role": "assistant", "content": "You're a helpful assistant."}, {"name": "user", "content": "What's the weather like today?"}]
```

#### Formatting Prompts in Dynamic Way

The `PromptEngine` supports dynamic prompts using the `format_map` parameter, allowing you to flexibly inject various variables into the prompt components for different scenarios:

```python
variables = {"location": "London"}
hint_prompt = "Find the weather in {location}."

prompt = engine.join(system_prompt, user_input, hint_prompt, format_map=variables)
```

[[Return to the top]](#206-prompt-en)
