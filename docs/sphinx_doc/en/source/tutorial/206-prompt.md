(206-prompt-en)=

# Prompt Engineering

Prompt engineering is critical in LLM-empowered applications. However,
crafting prompts for large language models (LLMs) can be challenging,
especially with different requirements from various model APIs.

To ease the process of adapting prompt to different model APIs, AgentScope
provides a structured way to organize different data types (e.g. instruction,
hints, dialogue history) into the desired format.

Note there is no **one-size-fits-all** solution for prompt crafting.
**The goal of built-in strategies is to enable beginners to smoothly invoke
the model API, rather than achieve the best performance**.
For advanced users, we highly recommend developers to customize prompts
according to their needs and model API requirements.

## Challenges in Prompt Construction

In multi-agent applications, LLM often plays different roles in a
conversation. When using third-party chat APIs, it has the following
challenges:

1. Most third-party chat APIs are designed for chatbot scenario, and the
   `role` field only supports `"user"` and `"assistant"`.

2. Some model APIs require `"user"` and `"assistant"` must speak alternatively,
   and `"user"` must speak in the beginning and end of the input messages list.
   Such requirements make it difficult to build a multi-agent conversation
   when the agent may act as many different roles and speak continuously.

To help beginners to quickly start with AgentScope, we provide the
following built-in strategies for most chat and generation related model APIs.

## Built-in Prompt Strategies

In AgentScope, we provide built-in strategies for the following chat and
generation model APIs.

- [`OpenAIChatWrapper`](#openaichatwrapper)
- [`DashScopeChatWrapper`](#dashscopechatwrapper)
- [`OllamaChatWrapper`](#ollamachatwrapper)
- [`OllamaGenerationWrapper`](ollamagenerationwrapper)
- [`GeminiChatWrapper`](#geminiwrapper)

These strategies are implemented in the `format` functions of the model
wrapper classes.
It accepts `Msg` objects, a list of `Msg` objects, or their mixture as input.

### `OpenAIChatWrapper`

`OpenAIChatWrapper` encapsulates the OpenAI chat API, it takes a list of
dictionaries as input, where the dictionary must obey the following rules
(updated in 2024/03/22):

- Require `role` and `content` fields, and an optional `name` field.
- The `role` field must be either `"system"`, `"user"`, or `"assistant"`.

#### Prompt Strategy

In OpenAI Chat API, the `name` field enables the model to distinguish
different speakers in the conversation. Therefore, the strategy of `format`
function in `OpenAIChatWrapper` is simple:

- `Msg`: Pass a dictionary with `role`, `content`, and `name` fields directly.
- `List`: Parse each element in the list according to the above rules.

An example is shown below:

```python
from agentscope.models import OpenAIChatWrapper
from agentscope.message import Msg

model = OpenAIChatWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="gpt-4",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg object
   [                                                             # a list of Msg objects
      Msg(name="Bob", content="Hi.", role="assistant"),
      Msg(name="Alice", content="Nice to meet you!", role="assistant"),
   ],
)
print(prompt)
```

```bash
[
  {"role": "system", "name": "system", "content": "You are a helpful assistant"},
  {"role": "assistant", "name": "Bob", "content": "Hi."},
  {"role": "assistant", "name": "Alice", "content": "Nice to meet you!"),
]
```

### `DashScopeChatWrapper`

`DashScopeChatWrapper` encapsulates the DashScope chat API, which takes a list of messages as input. The message must obey the following rules (updated in 2024/03/22):

- Require `role` and `content` fields, and `role` must be either `"user"`
  `"system"` or `"assistant"`.
- If `role` is `"system"`, this message must and can only be the first
  message in the list.
- The `user` and `assistant` must speak alternatively.
- The `user` must speak in the beginning and end of the input messages list.

#### Prompt Strategy

If the role field of the first message is `"system"`, it will be converted into a single message with the `role` field as `"system"` and the `content` field as the system message. The rest of the messages will be converted into a message with the `role` field as `"user"` and the `content` field as the dialogue history.

An example is shown below:

```python
from agentscope.models import DashScopeChatWrapper
from agentscope.message import Msg

model = DashScopeChatWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="qwen-max",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg object
   [                                                             # a list of Msg objects
      Msg(name="Bob", content="Hi!", role="assistant"),
      Msg(name="Alice", content="Nice to meet you!", role="assistant"),
   ],
)
print(prompt)
```

```bash
[
  {"role": "system", "content": "You are a helpful assistant"},
  {"role": "user", "content": "## Dialogue History\nBob: Hi!\nAlice: Nice to meet you!"},
]
```

### `OllamaChatWrapper`

`OllamaChatWrapper` encapsulates the Ollama chat API, which takes a list of
messages as input. The message must obey the following rules (updated in
2024/03/22):

- Require `role` and `content` fields, and `role` must be either `"user"`,
  `"system"`, or `"assistant"`.
- An optional `images` field can be added to the message

#### Prompt Strategy

Given a list of messages, we will parse each message as follows:

- `Msg`:  Fill the `role` and `content` fields directly. If it has an `url`
  field, which refers to an image, we will add it to the message.
- `List`: Parse each element in the list according to the above rules.

```python
from agentscope.models import OllamaChatWrapper

model = OllamaChatWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="llama2",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg object
   [                                                             # a list of Msg objects
      Msg(name="Bob", content="Hi.", role="assistant"),
      Msg(name="Alice", content="Nice to meet you!", role="assistant", url="https://example.com/image.jpg"),
   ],
)

print(prompt)
```

```bash
[
  {"role": "system", "content": "You are a helpful assistant"},
  {"role": "assistant", "content": "Hi."},
  {"role": "assistant", "content": "Nice to meet you!", "images": ["https://example.com/image.jpg"]},
]
```

### `OllamaGenerationWrapper`

`OllamaGenerationWrapper` encapsulates the Ollama generation API, which
takes a string prompt as input without any constraints (updated to 2024/03/22).

#### Prompt Strategy

If the role field of the first message is `"system"`, a system prompt will be created. The rest of the messages will be combined into dialogue history in string format.

```python
from agentscope.models import OllamaGenerationWrapper
from agentscope.message import Msg

model = OllamaGenerationWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="llama2",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg object
   [                                                             # a list of Msg objects
      Msg(name="Bob", content="Hi.", role="assistant"),
      Msg(name="Alice", content="Nice to meet you!", role="assistant"),
   ],
)

print(prompt)
```

```bash
You are a helpful assistant

## Dialogue History
Bob: Hi.
Alice: Nice to meet you!
```

### `GeminiChatWrapper`

`GeminiChatWrapper` encapsulates the Gemini chat API, which takes a list of
messages or a string prompt as input. Similar to DashScope Chat API, if we
pass a list of messages, it must obey the following rules:

- Require `role` and `parts` fields. `role` must be either `"user"`
  or `"model"`, and `parts` must be a list of strings.
- The `user` and `model` must speak alternatively.
- The `user` must speak in the beginning and end of the input messages list.

Such requirements make it difficult to build a multi-agent conversation when
an agent may act as many different roles and speak continuously.
Therefore, we decide to convert the list of messages into a user message
in our built-in `format` function.

#### Prompt Strategy

If the role field of the first message is `"system"`, a system prompt will be added in the beginning. The other messages will be combined into dialogue history.

**Note** sometimes the `parts` field may contain image urls, which is not
supported in `format` function. We recommend developers to customize the
prompt according to their needs.

```python
from agentscope.models import GeminiChatWrapper
from agentscope.message import Msg

model = GeminiChatWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="gemini-pro",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg object
   [                                                             # a list of Msg objects
      Msg(name="Bob", content="Hi!", role="assistant"),
      Msg(name="Alice", content="Nice to meet you!", role="assistant"),
   ],
)

print(prompt)
```

```bash
[
  {
    "role": "user",
    "parts": [
      "You are a helpful assistant\n## Dialogue History\nBob: Hi!\nAlice: Nice to meet you!"
    ]
  }
]
```

## Prompt Engine (Will be deprecated in the future)

AgentScope provides the `PromptEngine` class to simplify the process of crafting
prompts for large language models (LLMs).

## About `PromptEngine` Class

The `PromptEngine` class provides a structured way to combine different components of a prompt, such as instructions, hints, dialogue history, and user inputs, into a format that is suitable for the underlying language model.

### Key Features of PromptEngine

- **Model Compatibility**: It works with any `ModelWrapperBase` subclass.
- **Prompt Type**: It supports both string and list-style prompts, aligning with the model's preferred input format.

### Initialization

When creating an instance of `PromptEngine`, you can specify the target model and, optionally, the shrinking policy, the maximum length of the prompt, the prompt type, and a summarization model (could be the same as the target model).

```python
model = OpenAIChatWrapper(...)
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
