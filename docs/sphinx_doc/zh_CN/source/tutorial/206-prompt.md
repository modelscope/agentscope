(206-prompt-zh)=

# 提示工程

提示工程是与大型语言模型（LLMs）相关的应用中至关重要的组件。然而，为大型语言模型（LLMs）制作提示可能具有挑战性，尤其是在面对来自不同模型API的不同需求时。

为了帮助开发者更好地适应不同模型API的需求，AgentScope提供了一种结构化的方式来组织不同数据类型（例如指令、提示、对话历史）到所需的格式。

请注意这里不存在一个“**适用于所有模型API**”的提示构建方案。
AgentScope内置策略的目标是**使初学者能够顺利调用模型API ，而不是使应用达到最佳效果**。对于进阶用户，我们强烈建议开发者根据自己的需求和模型API的要求自定义提示。

## 构建提示面临的挑战

在多智能体应用中，LLM通常在对话中扮演不同的角色。当使用模型的Chat API时，时长会面临以下挑战：

1. 大多数Chat类型的模型API是为聊天机器人场景设计的，`role`字段只支持`"user"`和`"assistant"`，不支持`name`字段，即API本身不支持角色扮演。

2. 一些模型API要求`"user"`和`"assistant"`必须交替发言，而`"user"`必须在输入消息列表的开头和结尾发言。这样的要求使得在一个代理可能扮演多个不同角色并连续发言时，构建多智能体对话变得困难。

为了帮助初学者快速开始使用AgentScope，我们为大多数与聊天和生成相关的模型API提供了以下内置策略。

## 内置提示策略

AgentScope为以下的模型API提供了内置的提示构建策略。

- [OpenAIChatWrapper](#openaichatwrapper)
- [DashScopeChatWrapper](#dashscopechatwrapper)
- [DashScopeMultiModalWrapper](#dashscopemultimodalwrapper)
- [OllamaChatWrapper](#ollamachatwrapper)
- [OllamaGenerationWrapper](#ollamagenerationwrapper)
- [GeminiChatWrapper](#geminichatwrapper)
- [ZhipuAIChatWrapper](#zhipuaichatwrapper)

这些策略是在对应Model Wrapper类的`format`函数中实现的。它接受`Msg`对象，`Msg`对象的列表或它们的混合作为输入。在`format`函数将会把输入重新组织成一个`Msg`对象的列表，因此为了方便解释，我们在下面的章节中认为`format`函数的输入是`Msg`对象的列表。

### `OpenAIChatWrapper`

`OpenAIChatWrapper`封装了OpenAI聊天API，它以字典列表作为输入，其中字典必须遵循以下规则（更新于2024/03/22）：

- 需要`role`和`content`字段，以及一个可选的`name`字段。
- `role`字段必须是`"system"`、`"user"`或`"assistant"`之一。

#### 提示的构建策略

在OpenAI Chat API中，`name`字段使模型能够区分对话中的不同发言者。因此，`OpenAIChatWrapper`中`format`函数的策略很简单：

- `Msg`: 直接将带有`role`、`content`和`name`字段的字典传递给API。
- `List`: 根据上述规则解析列表中的每个元素。

样例如下：

```python
from agentscope.models import OpenAIChatWrapper
from agentscope.message import Msg

model = OpenAIChatWrapper(
    config_name="", # 我们直接初始化model wrapper，因此不需要填入config_name
    model_name="gpt-4",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg对象
   [                                                             # Msg对象的列表
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

`DashScopeChatWrapper`封装了DashScope聊天API，它接受消息列表作为输入。消息必须遵守以下规则：

- 需要`role`和`content`字段，以及一个可选的`name`字段。
- `role`字段必须是`"user"`，`"system"`或`"assistant"`之一。
- 如果一条信息的`role`字段是`"system"`，那么这条信息必须也只能出现在消息列表的开头。
- `user`和`assistant`必须交替发言。

#### 提示的构建策略

如果第一条消息的`role`字段是`"system"`，它将被转换为一条消息，其中`role`字段为`"system"`，`content`字段为系统消息。其余的消息将被转换为一条消息，其中`role`字段为`"user"`，`content`字段为对话历史。

样例如下：

```python
from agentscope.models import DashScopeChatWrapper
from agentscope.message import Msg

model = DashScopeChatWrapper(
    config_name="", # 我们直接初始化model wrapper，因此不需要填入config_name
    model_name="qwen-max",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg对象
   [                                                             # Msg对象的列表
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

### `DashScopeMultiModalWrapper`

`DashScopeMultiModalWrapper`封装了多模态模型的API，它接受消息列表作为输入，并且必须遵循以下的规则(更新于2024/04/04):

- 每个消息是一个字段，并且包含`role`和`content`字段。
  - 其中`role`字段取值必须是`"user"`，`"system"`，`"assistant"`之一。
  - `content`字段对应的值必须是字典的列表
    - 每个字典只包含`text`，`image`或`audio`中的一个键值对
    - `text`域对应的值是一个字符串，表示文本内容
    - `image`域对应的值是一个字符串，表示图片的url
    - `audio`域对应的值是一个字符串，表示音频的url
    - `content`中可以同时包含多个key为`image`的字典或者多个key为`audio`的字典。例如
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
- 如果一条信息的`role`字段是`"system"`，那么这条信息必须也只能出现在消息列表的开头。
- 消息列表中最后一条消息的`role`字段必须是`"user"`。
- 消息列表中`user`和`assistant`必须交替发言。

#### 提示的构建策略

基于上述API的限制，构建策略如下：
- 如果输入的消息列表中第一条消息的`role`字段的值是`"system"`，它将被转换为一条系统消息，其中`role`字段为`"system"`，`content`字段为系统消息，如果输入`Msg`对象中`url`属性不为`None`，则根据其类型在`content`中增加一个键值为`"image"`或者`"audio"`的字典。
- 其余的消息将被转换为一条消息，其中`role`字段为`"user"`，`content`字段为对话历史。并且所有`Msg`对象中`url`属性不为`None`的消息，都会根据`url`指向的文件类型在`content`中增加一个键值为`"image"`或者`"audio"`的字典。

样例如下：

```python
from agentscope.models import DashScopeMultiModalWrapper
from agentscope.message import Msg

model = DashScopeMultiModalWrapper(
    config_name="", # 我们直接初始化model wrapper，因此不需要填入config_name
    model_name="qwen-vl-plus",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system", url="url_to_png1"),   # Msg对象
   [                                                                                # Msg对象的列表
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
      {"text": "## Dialogue History\nBob: Hi!\nAlice: Nice to meet you!"},
      {"image": "url_to_png2"},
      {"image": "url_to_png3"},
    ]
  }
]
```

### `OllamaChatWrapper`

`OllamaChatWrapper`封装了Ollama聊天API，它接受消息列表作为输入。消息必须遵守以下规则(更新于2024/03/22)：

- 需要`role`和`content`字段，并且`role`必须是`"user"`、`"system"`或`"assistant"`之一。
- 可以添加一个可选的`images`字段到消息中。

#### 提示的构建策略

给定一个消息列表，我们将按照以下规则解析每个消息：

- `Msg`：直接填充`role`和`content`字段。如果它有一个`url`字段，指向一个图片，我们将把它添加到消息中。
- `List`：根据上述规则解析列表中的每个元素。

```python
from agentscope.models import OllamaChatWrapper

model = OllamaChatWrapper(
    config_name="", # 我们直接初始化model wrapper，因此不需要填入config_name
    model_name="llama2",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg对象
   [                                                             # Msg对象的列表
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

`OllamaGenerationWrapper`封装了Ollama生成API，它接受字符串提示作为输入，没有任何约束(更新于2024/03/22)。

#### 提示的构建策略

如果第一条消息的`role`字段是`"system"`，那么它将会被转化成一条系统提示。其余消息会被拼接成对话历史。

```python
from agentscope.models import OllamaGenerationWrapper
from agentscope.message import Msg

model = OllamaGenerationWrapper(
    config_name="", # 我们直接初始化model wrapper，因此不需要填入config_name
    model_name="llama2",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg对象
   [                                                             # Msg对象的列表
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

`GeminiChatWrapper`封装了Gemini聊天API，它接受消息列表或字符串提示作为输入。与DashScope聊天API类似，如果我们传递消息列表，它必须遵守以下规则：

- 需要`role`和`parts`字段。`role`必须是`"user"`或`"model"`之一，`parts`必须是字符串列表。
- `user`和`model`必须交替发言。
- `user`必须在输入消息列表的开头和结尾发言。

当代理可能扮演多种不同角色并连续发言时，这些要求使得构建多代理对话变得困难。
因此，我们决定在内置的`format`函数中将消息列表转换为字符串提示，并且封装在一条user信息中。

#### 提示的构建策略

如果第一条消息的`role`字段是`"system"`，那么它将会被转化成一条系统提示。其余消息会被拼接成对话历史。

**注意**Gemini Chat API中`parts`字段可以包含图片的url，由于我们将消息转换成字符串格式
的输入，因此图片url在目前的`format`函数中是不支持的。
我们推荐开发者可以根据需求动手定制化自己的提示。

```python
from agentscope.models import GeminiChatWrapper
from agentscope.message import Msg

model = GeminiChatWrapper(
    config_name="", # 我们直接初始化model wrapper，因此不需要填入config_name
    model_name="gemini-pro",
)

prompt = model.format(
   Msg("system", "You're a helpful assistant", role="system"),   # Msg对象
   [                                                             # Msg对象的列表
      Msg(name="Bob", content="Hi.", role="model"),
      Msg(name="Alice", content="Nice to meet you!", role="model"),
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


### `ZhipuAIChatWrapper`

`ZhipuAIChatWrapper`封装了ZhipuAi聊天API，它接受消息列表或字符串提示作为输入。与DashScope聊天API类似，如果我们传递消息列表，它必须遵守以下规则：

- 必须有 role 和 content 字段，且 role 必须是 "user"、"system" 或 "assistant" 中的一个。
- 至少有一个 user 消息。

当代理可能扮演多种不同角色并连续发言时，这些要求使得构建多代理对话变得困难。
因此，我们决定在内置的`format`函数中将消息列表转换为字符串提示，并且封装在一条user信息中。

#### 提示的构建策略

如果第一条消息的 role 字段是 "system"，它将被转换为带有 role 字段为 "system" 和 content 字段为系统消息的单个消息。其余的消息会被转化为带有 role 字段为 "user" 和 content 字段为对话历史的消息。
下面展示了一个示例：

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
  {"role": "user", "content": "## Dialogue History\nBob: Hi!\nAlice: Nice to meet you!"},
]
```

## 关于`PromptEngine`类 （将会在未来版本弃用）

`PromptEngine`类提供了一种结构化的方式来合并不同的提示组件，比如指令、提示、对话历史和用户输入，以适合底层语言模型的格式。

### 提示工程的关键特性

- **模型兼容性**：可以与任何 `ModelWrapperBase` 的子类一起工作。
- **提示类型**：支持字符串和列表风格的提示，与模型首选的输入格式保持一致。

### 初始化

当创建 `PromptEngine` 的实例时，您可以指定目标模型，以及（可选的）缩减原则、提示的最大长度、提示类型和总结模型（可以与目标模型相同）。

```python
model = OpenAIChatWrapper(...)
engine = PromptEngine(model)
```

### 合并提示组件

`PromptEngine` 的 `join` 方法提供了一个统一的接口来处理任意数量的组件，以构建最终的提示。

#### 输出字符串类型提示

如果模型期望的是字符串类型的提示，组件会通过换行符连接：

```python
system_prompt = "You're a helpful assistant."
memory = ... # 可以是字典、列表或字符串
hint_prompt = "Please respond in JSON format."

prompt = engine.join(system_prompt, memory, hint_prompt)
# 结果将会是 ["You're a helpful assistant.", {"name": "user", "content": "What's the weather like today?"}]
```

#### 输出列表类型提示

对于使用列表类型提示的模型，比如 OpenAI 和 Huggingface 聊天模型，组件可以转换为 `Message` 对象，其类型是字典列表：

```python
system_prompt = "You're a helpful assistant."
user_messages = [{"name": "user", "content": "What's the weather like today?"}]

prompt = engine.join(system_prompt, user_messages)
# 结果将会是: [{"role": "assistant", "content": "You're a helpful assistant."}, {"name": "user", "content": "What's the weather like today?"}]
```

#### 动态格式化提示

`PromptEngine` 支持使用 `format_map` 参数动态提示，允许您灵活地将各种变量注入到不同场景的提示组件中：

```python
variables = {"location": "London"}
hint_prompt = "Find the weather in {location}."

prompt = engine.join(system_prompt, user_input, hint_prompt, format_map=variables)
```

[[返回顶端]](#206-prompt-zh)
