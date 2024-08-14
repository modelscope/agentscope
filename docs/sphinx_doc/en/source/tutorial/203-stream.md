(203-stream-en)=

# Streaming

AgentScope supports streaming mode for the following LLM APIs in both **terminal** and **AgentScope Studio**.

| API                | Model Wrapper                                                                                                                   | `model_type` field in model configuration |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| OpenAI Chat API    |  [`OpenAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                 | `"openai_chat"`                           |
| DashScope Chat API |  [`DashScopeChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)           | `"dashscope_chat"`                        |
| Gemini Chat API    |  [`GeminiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)                 | `"gemini_chat"`                           |
| ZhipuAI Chat API   |  [`ZhipuAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)                 | `"zhipuai_chat"`                          |
| ollama Chat API    |  [`OllamaChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                 | `"ollama_chat"`                           |
| LiteLLM Chat API   |  [`LiteLLMChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/litellm_model.py)             | `"litellm_chat"`                          |


## Setup Streaming Mode

AgentScope allows users to set up streaming mode in both model configuration and model calling.

### In Model Configuration

To use streaming mode, set the stream field to `True` in the model configuration.

```python
model_config = {
    "config_name": "xxx",
    "model_type": "xxx",
    "stream": True,
    # ...
}
```

### In Model Calling

Within an agent, you can call the model with the `stream` parameter set to `True`.
Note the `stream` parameter in the model calling will override the `stream` field in the model configuration.

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

## Printing in Streaming Mode

In streaming mode, the `stream` field of a model response will be a generator, and the `text` field will be `None`.
For compatibility with the non-streaming mode, once the `text` field is accessed, the generator in `stream` field will be iterated to generate the full text and store it in the `text` field.
So that even in streaming mode, users can handle the response text in `text` field as usual.

However, if you want to print in streaming mode, just put the generator in `self.speak` to print the streaming text in the terminal and AgentScope Studio.

After printing the streaming response, the full text of the response will be available in the `response.text` field.

```python
    def reply(self, x: Optional[Msg, Sequence[Msg]] = None) -> Msg:
        # ...
        # Use stream=True if you want to set up streaming mode in model calling
        response = self.model(prompt)

        # For now, the response.text is None

        # Print the response in streaming mode in terminal and AgentScope Studio (if available)
        self.speak(response.stream)

        # After printing, the response.text will be the full text of the response, and you can handle it as usual
        msg = Msg(self.name, content=response.text, role="assistant")

        self.memory.add(msg)

        return msg

```

## Advanced Usage

For users who want to handle the streaming response by themselves, they can iterate the generator and handle the response text in their own way.

An example of how to handle the streaming response is in the `speak` function of `AgentBase` as follows.
The `log_stream_msg` function will print the streaming response in the terminal and AgentScope Studio (if registered).

```python
        # ...
        elif isinstance(content, GeneratorType):
            # The streaming message must share the same id for displaying in
            # the agentscope studio.
            msg = Msg(name=self.name, content="", role="assistant")
            for last, text_chunk in content:
                msg.content = text_chunk
                log_stream_msg(msg, last=last)
        else:
        # ...
```

However, they should remember the following points:

1. When iterating the generator, the `response.text` field will include the text that has been iterated automatically.
2. The generator in the `stream` field will generate a tuple of boolean and text. The boolean indicates whether the text is the end of the response, and the text is the response text until now.
3. To print streaming text in AgentScope Studio, the message id should be the same for one response in the `log_stream_msg` function.


```python
    def reply(self, x: Optional[Msg, Sequence[Msg]] = None) -> Msg:
        # ...
        response = self.model(prompt)

        # For now, the response.text is None

        # Iterate the generator and handle the response text by yourself
        for last_chunk, text in response.stream:
            # Handle the text in your way
            # ...


```

[[Return to the top]](#203-stream-en)
