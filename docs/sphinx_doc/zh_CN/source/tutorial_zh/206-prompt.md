(206-prompt-zh)=

# 提示工程

**提示(prompt)** 是与语言模型互动时的关键组件，尤其是当寻求生成特定类型的输出或指导模型朝
向期望行为时。
AgentScope中允许开发者按照自己的需求定制提示，同时提供了`PromptEngine`类用以简化为大语言
模型（LLMs）制作提示的过程。
本教程将主要介绍如何使用`PromptEngine`类构建大模型的提示。

## 关于`PromptEngine`类

`PromptEngine`类提供了一种结构化的方式来合并不同的提示组件，比如指令、提示、对话历史和用户输入，以适合底层语言模型的格式。

### 提示工程的关键特性

- **模型兼容性**：可以与任何 `ModelWrapperBase` 的子类一起工作。
- **提示类型**：支持字符串和列表风格的提示，与模型首选的输入格式保持一致。

### 初始化

当创建 `PromptEngine` 的实例时，您可以指定目标模型，以及（可选的）缩减原则、提示的最大长度、提示类型和总结模型（可以与目标模型相同）。

```python
model = OpenAIWrapper(...)
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
