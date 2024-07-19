(203-stream-zh)=

# 流式输出

AgentScope 支持在**终端**和 **AgentScope Studio** 中使用以下大模型 API 的流式输出模式。

| API                | Model Wrapper                                                                                                                   | 对应的 `model_type` 域 |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------|--------------------|
| OpenAI Chat API    |  [`OpenAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                 | `"openai_chat"`    |
| DashScope Chat API |  [`DashScopeChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)           | `"dashscope_chat"` |
| Gemini Chat API    |  [`GeminiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)                 | `"gemini_chat"`    |
| ZhipuAI Chat API   |  [`ZhipuAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)                 | `"zhipuai_chat"`   |
| ollama Chat API    |  [`OllamaChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                 | `"ollama_chat"`    |
| LiteLLM Chat API   |  [`LiteLLMChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/litellm_model.py)             | `"litellm_chat"`   |


## 设置流式输出

AgentScope 允许用户在模型配置和模型调用中设置流式输出模式。

### 模型配置

在模型配置中将 `stream` 字段设置为 `True` 以使用流式输出模式。

```python
model_config = {
    "config_name": "xxx",
    "model_type": "xxx",
    "stream": True,
    # ...
}
```

### 模型调用

在智能体中，可以在调用模型时将 `stream` 参数设置为 `True`。注意，模型调用中的 `stream` 参数将覆盖模型配置中的 `stream` 字段。

```python
class MyAgent(AgentBase):
    # ...
    def reply(self, x: Optional[Msg, Sequence[Msg]] = None) -> Msg:
        # ...
        response = self.model(
            prompt,
            stream=True,
        )
        # ...
```

## 流式打印

在流式输出模式下，模型响应的 `stream` 字段将是一个生成器，而 `text` 字段将是 `None`。
为了与非流式兼容，用户一旦在迭代生成器前访问 `text` 字段，`stream` 中的生成器将被迭代以生成完整的文本，并将其存储在 `text` 字段中。
因此，即使在流式输出模式下，用户也可以像往常一样在 `text` 字段中处理响应文本而无需任何改变。

但是，如果用户需要流式的输出，只需要将生成器放在 `self.speak` 函数中，以在终端和 AgentScope Studio 中流式打印文本。

```python
    def reply(self, x: Optional[Msg, Sequence[Msg]] = None) -> Msg:
        # ...
        # 如果想在调用时使用流式打印，在这里调用时使用 stream=True
        response = self.model(prompt)

        # 程序运行到这里时，response.text 为 None

        # 在 terminal 和 AgentScope Studio 中流式打印文本
        self.speak(response.stream)

        # 生成器被迭代时，产生的文本将自动被存储在 response.text 中，因此用户可以直接使用 response.text 处理响应文本
        msg = Msg(self.name, content=response.text, role="assistant")

        self.memory.add(msg)

        return msg

```

## 进阶用法

如果用户想要自己处理流式输出，可以通过迭代生成器来实时获得流式的响应文本。

An example of how to handle the streaming response is in the `speak` function of `AgentBase` as follows.
关于如何处理流式输出，可以参考 `AgentBase` 中的 `speak` 函数。
The `log_stream_msg` function will print the streaming response in the terminal and AgentScope Studio (if registered).
其中 `log_stream_msg` 函数将在终端和 AgentScope Studio 中实时地流式打印文本。

```python
        # ...
        elif isinstance(content, GeneratorType):
            # 流式消息必须共享相同的 id 才能在 AgentScope Studio 中显示，因此这里通过同一条消息切换 content 字段来实现
            msg = Msg(name=self.name, content="", role="assistant")
            for last, text_chunk in content:
                msg.content = text_chunk
                log_stream_msg(msg, last=last)
        else:
        # ...
```

在处理生成器的时候，用户应该记住以下几点：

1. 在迭代生成器时，`response.text` 字段将自动包含已迭代的文本。
2. `stream` 字段中的生成器将生成一个布尔值和字符串的二元组。布尔值表示当前是否是最后一段文本，而字符串则是到目前为止的响应文本。
3. AgentScope Studio 依据 `log_stream_msg` 函数中输入的 `Msg` 对象的 id 判断文本是否属于同一条流式响应，若 id 不同，则会被视为不同的响应。


```python
    def reply(self, x: Optional[Msg, Sequence[Msg]] = None) -> Msg:
        # ...
        response = self.model(prompt)

        # 程序运行到这里时，response.text 为 None

        # 迭代生成器，自己处理响应文本
        for last_chunk, text in response.stream:
            # 按照自己的需求处理响应文本
            # ...


```

[[Return to the top]](#203-stream-zh)
