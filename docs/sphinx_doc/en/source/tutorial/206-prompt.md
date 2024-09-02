(206-prompt-en)=

# Prompt Engineering

Prompt engineering is critical in LLM-empowered applications. However,
crafting prompts for large language models (LLMs) can be challenging,
especially with different requirements from various model APIs.

To ease the process of adapting prompt to different model APIs, AgentScope
provides a structured way to organize different data types (e.g. instruction,
hints, conversation history) into the desired format.

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

- [OpenAIChatWrapper](#openaichatwrapper)
- [DashScopeChatWrapper](#dashscopechatwrapper)
- [DashScopeMultiModalWrapper](#dashscopemultimodalwrapper)
- [OllamaChatWrapper](#ollamachatwrapper)
- [OllamaGenerationWrapper](#ollamagenerationwrapper)
- [GeminiChatWrapper](#geminichatwrapper)
- [ZhipuAIChatWrapper](#zhipuaichatwrapper)

These strategies are implemented in the `format` functions of the model
wrapper classes.
It accepts `Msg` objects, a list of `Msg` objects, or their mixture as input.
However, `format` function will first reorganize them into a list of `Msg`
objects, so for simplicity in the following sections we treat the input as a
list of `Msg` objects.

### OpenAIChatWrapper

`OpenAIChatWrapper` encapsulates the OpenAI chat API, it takes a list of
dictionaries as input, where the dictionary must obey the following rules
(updated in 2024/03/22):

- Require `role` and `content` fields, and an optional `name` field.
- The `role` field must be either `"system"`, `"user"`, or `"assistant"`.

#### Prompt Strategy

##### Non-Vision Models

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

##### Vision Models

For vision models (gpt-4-turbo, gpt-4o, ...), if the input message contains image urls, the generated `content` field will be a list of dicts, which contains text and image urls.

Specifically, the web image urls will be pass to OpenAI Chat API directly, while the local image urls will be converted to base64 format. More details please refer to the [official guidance](https://platform.openai.com/docs/guides/vision).

Note the invalid image urls (e.g. `/Users/xxx/test.mp3`) will be ignored.

```python
from agentscope.models import OpenAIChatWrapper
from agentscope.message import Msg

model = OpenAIChatWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="gpt-4o",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg object
   [                                                             # a list of Msg objects
      Msg(name="user", content="Describe this image", role="user", url="https://xxx.png"),
      Msg(name="user", content="And these images", role="user", url=["/Users/xxx/test.png", "/Users/xxx/test.mp3"]),
   ],
)
print(prompt)
```

```python
[
    {
        "role": "system",
        "name": "system",
        "content": "You are a helpful assistant"
    },
    {
        "role": "user",
        "name": "user",
        "content": [
            {
                "type": "text",
                "text": "Describe this image"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://xxx.png"
                }
            },
        ]
    },
    {
        "role": "user",
        "name": "user",
        "content": [
            {
                "type": "text",
                "text": "And these images"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64,YWJjZGVm..." # for /Users/xxx/test.png
                }
            },
        ]
    },
]
```

### DashScopeChatWrapper

`DashScopeChatWrapper` encapsulates the DashScope chat API, which takes a list of messages as input. The message must obey the following rules (updated in 2024/03/22):

- Require `role` and `content` fields, and `role` must be either `"user"`
  `"system"` or `"assistant"`.
- If `role` is `"system"`, this message must and can only be the first
  message in the list.
- The `user` and `assistant` must speak alternatively.
- The `user` must speak in the beginning and end of the input messages list.

#### Prompt Strategy

If the role field of the first message is `"system"`, it will be converted into a single message with the `role` field as `"system"` and the `content` field as the system message. The rest of the messages will be converted into a message with the `role` field as `"user"` and the `content` field as the conversation history.

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

```python
prompt = [
    {
        "role": "user",
        "content": (
            "You are a helpful assistant\n"
            "\n"
            "## Conversation History\n"
            "Bob: Hi!\n"
            "Alice: Nice to meet you!"
        )
   },
]
```

### DashScopeMultiModalWrapper

`DashScopeMultiModalWrapper` encapsulates the DashScope multimodal conversation API, which takes a list of messages as input. The message must obey the following rules (updated in 2024/04/04):

- Each message is a dictionary with `role` and `content` fields.
  - The `role` field must be either `"user"`, `"system"`, or `"assistant"`.
  - The `content` field must be a list of dictionaries, where
    - Each dictionary only contains one key-value pair, whose key must be `text`, `image` or `audio`.
    - `text` field is a string, representing the text content.
    - `image` field is a string, representing the image url.
    - `audio` field is a string, representing the audio url.
    - The `content` field can contain multiple dictionaries with the key `image` or multiple dictionaries with the key `audio` at the same time. For example:

```python
[
    {
        "role": "user",
        "content": [
            {"text": "What's the difference between these two pictures?"},
            {"image": "https://xxx1.png"},
            {"image": "https://xxx2.png"}
        ]
    },
    {
        "role": "assistant",
        "content": [{"text": "The first picture is a cat, and the second picture is a dog."}]
    },
    {
        "role": "user",
        "content": [{"text": "I see, thanks!"}]
    }
]
```

- The message with the `role` field as `"system"` must and can only be the first message in the list.
- The last message must have the `role` field as `"user"`.
- The `user` and `assistant` messages must alternate.

#### Prompt Strategy

Based on the above rules, the `format` function in `DashScopeMultiModalWrapper` will parse the input messages as follows:

- If the first message in the input message list has a `role` field with the value `"system"`, it will be converted into a system message with the `role` field as `"system"` and the `content` field as the system message. If the `url` field in the input `Msg` object is not `None`, a dictionary with the key `"image"` or `"audio"` will be added to the `content` based on its type.
- The rest of the messages will be converted into a message with the `role` field as `"user"` and the `content` field as the conversation history. For each message, if their `url` field is not `None`, it will add a dictionary with the key `"image"` or `"audio"` to the `content` based on the file type that the `url` points to.

An example:

```python
from agentscope.models import DashScopeMultiModalWrapper
from agentscope.message import Msg

model = DashScopeMultiModalWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="qwen-vl-plus",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system", url="url_to_png1"),   # Msg object
   [                                                                                # a list of Msg objects
      Msg(name="Bob", content="Hi!", role="assistant", url="url_to_png2"),
      Msg(name="Alice", content="Nice to meet you!", role="assistant", url="url_to_png3"),
   ],
)
print(prompt)
```

```bash
[
  {
    "role": "system",
    "content": [
      {"text": "You are a helpful assistant"},
      {"image": "url_to_png1"}
    ]
  },
  {
    "role": "user",
    "content": [
      {"text": "## Conversation History\nBob: Hi!\nAlice: Nice to meet you!"},
      {"image": "url_to_png2"},
      {"image": "url_to_png3"},
    ]
  }
]
```


### LiteLLMChatWrapper

`LiteLLMChatWrapper` encapsulates the litellm chat API, which takes a list of
messages as input. The litellm supports different types of models, and each model
might need to obey different formats. To simplify the usage, we provide a format
that could be compatible with most models. If more specific formats are needed,
you can refer to the specific model you use as well as the
[litellm](https://github.com/BerriAI/litellm) documentation to customize your
own format function for your model.


- format all the messages in the chat history, into a single message with `"user"` as `role`

#### Prompt Strategy

- Messages will consist conversation history in the `user` message prefixed by the system message and "## Conversation History".

```python
from agentscope.models import LiteLLMChatWrapper
from agentscope.message import Msg

model = LiteLLMChatWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="gpt-3.5-turbo",
)

prompt = model.format(
  Msg("system", "You are a helpful assistant", role="system"),
  [
      Msg("user", "What is the weather today?", role="user"),
      Msg("assistant", "It is sunny today", role="assistant"),
  ],
)

print(prompt)
```

```bash
[
    {
        "role": "user",
        "content": (
            "You are a helpful assistant\n"
            "\n"
            "## Conversation History\n"
            "user: What is the weather today?\n"
            "assistant: It is sunny today"
        ),
    },
]
```

### OllamaChatWrapper

`OllamaChatWrapper` encapsulates the Ollama chat API, which takes a list of
messages as input. The message must obey the following rules (updated in
2024/03/22):

- Require `role` and `content` fields, and `role` must be either `"user"`,
  `"system"`, or `"assistant"`.
- An optional `images` field can be added to the message

#### Prompt Strategy

- If the role field of the first input message is `"system"`,
it will be treated as system prompt and the other messages will consist
conversation history in the system message prefixed by "## Conversation History".
- If the `url` attribute of messages is not `None`, we will gather all urls in
the `"images"` field in the returned dictionary.

```python
from agentscope.models import OllamaChatWrapper
from agentscope.message import Msg

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

```python
[
    {
        "role": "system",
        "content": (
            "You are a helpful assistant\n"
            "\n"
            "## Conversation History\n"
            "Bob: Hi.\n"
            "Alice: Nice to meet you!",
        ),
        "images": ["https://example.com/image.jpg"]
    },
]
```

### OllamaGenerationWrapper

`OllamaGenerationWrapper` encapsulates the Ollama generation API, which
takes a string prompt as input without any constraints (updated to 2024/03/22).

#### Prompt Strategy

If the role field of the first message is `"system"`, a system prompt will be created. The rest of the messages will be combined into conversation history in string format.

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

## Conversation History
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

If the role field of the first message is `"system"`, a system prompt will be added in the beginning. The other messages will be combined into conversation history.

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

```python
[
    {
        "role": "user",
        "parts": [
            "You are a helpful assistant\n"
            "## Conversation History\n"
            "Bob: Hi!\n"
            "Alice: Nice to meet you!"
        ]
    }
]
```

### `ZhipuAIChatWrapper`

`ZhipuAIChatWrapper` encapsulates the ZhipuAI chat API, which takes a list of messages as input. The message must obey the following rules:

- Require `role` and `content` fields, and `role` must be either `"user"`
  `"system"` or `"assistant"`.
- There must be at least one `user` message.

#### Prompt Strategy

If the role field of the first message is `"system"`, it will be converted into a single message with the `role` field as `"system"` and the `content` field as the system message. The rest of the messages will be converted into a message with the `role` field as `"user"` and the `content` field as the conversation history.

An example is shown below:

```python
from agentscope.models import ZhipuAIChatWrapper
from agentscope.message import Msg

model = ZhipuAIChatWrapper(
    config_name="", # empty since we directly initialize the model wrapper
    model_name="glm-4",
    api_key="your api key",
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
  {"role": "user", "content": "## Conversation History\nBob: Hi!\nAlice: Nice to meet you!"},
]
```

[[Return to the top]](#206-prompt-en)
