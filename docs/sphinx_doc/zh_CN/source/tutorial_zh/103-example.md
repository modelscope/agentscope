(103-example-zh)=

# 快速开始

AgentScope内置了灵活的通信机制。在本教程中，我们将通过一个简单的独立对话示例介绍AgentScope的基本用法。

## 第一步：准备模型

为了更好的构建多智能体应用，AgentScope将模型的部署与调用解耦开，以API服务调用的方式支持各种不同的模型。

在模型部署方面，用户可以使用第三方模型服务，例如OpenAI API，HuggingFace Inference
API，同时也可以通过仓库中的[脚本](https://github.com/modelscope/agentscope/blob/main/scripts/README.md)快速部署本地开源模型服务，
目前已支持通过Flask配合Transformers（或ModelScope）快速建立基础的模型服务，同时也已经支持通过FastChat和vllm等推理引擎部署本地模型服务。

模型调用方面，AgentScope通过`ModelWrapper`类提供OpenAI API和RESTful Post Request调用的封装。
目前支持的OpenAI API包括了对话（Chat），图片生成（Image generation）和嵌入式（Embedding）。
用户可以通过设定不同的model config来指定模型服务。

| 模型使用         | APIs                                                                   |
|--------------|------------------------------------------------------------------------|
| 文本生成         | *OpenAI* chat API，FastChat和vllm                                        |
| 图片生成         | *DALL-E* API                                                           |
| 文本嵌入         | 文本Embedding                                                            |
| 基于Post请求的API | *Huggingface*/*ModelScope* Inference API，以及用户自定应的基于Post请求的API |

每种API都有其特定的配置要求。例如，要配置OpenAI API，您需要在模型配置中填写以下字段：

```python
model_config = {
    "config_name": "{config_name}", # A unique name for the model config.
    "model_type": "openai",         # Choose from "openai", "openai_dall_e", or "openai_embedding".
    "model_name": "{model_name}",   # The model identifier used in the OpenAI API, such as "gpt-3.5-turbo", "gpt-4", or "text-embedding-ada-002".
    "api_key": "xxx",               # Your OpenAI API key. If unset, the environment variable OPENAI_API_KEY is used.
    "organization": "xxx",          # Your OpenAI organization ID. If unset, the environment variable OPENAI_ORGANIZATION is used.
}
```

对于开源模型，我们支持与HuggingFace、ModelScope、FastChat和vllm等各种模型接口的集成。您可以在`scripts
`目录中找到部署这些服务的脚本，详细说明请见[[模型服务]](203-model).

您可以通过调用AgentScope的初始化方法来注册您的配置。此外，您还可以一次性加载多个模型配置。

```python
import agentscope

# 一次性初始化多个模型配置
openai_cfg_dict = {
    # ...
}
modelscope_cfg_dict = {
    # ...
}
agentscope.init(model_configs=[openai_cfg_dict, modelscope_cfg_dict])
```

## 第二步: 创建智能体

创建智能体在AgentScope中非常简单。在初始化AgentScope时，您可以使用模型配置初始化AgentScope，然后定义每个智能体及其对应的角色和特定模型。

```python
import agentscope
from agentscope.agents import DialogAgent, UserAgent

# 读取模型配置
agentscope.init(model_configs="./model_configs.json")

# 创建一个对话智能体和一个用户智能体
dialogAgent = DialogAgent(name="assistant", model_config_name="gpt-4", sys_prompt="You are a helpful ai assistant")
userAgent = UserAgent()
```

**注意**：请参考[[使用Agent Pool自定义您的自定义智能体]](201-agent)以获取所有可用的智能体以及创建自定义的智能体。

## 第三步：智能体对话

消息（Message）是AgentScope中智能体之间的主要通信手段。
它是一个Python字典，包括了一些基本字段，如消息的`content`和消息发送者的`name`。可选地，消息可以包括一个`url`，指向本地文件（图像、视频或音频）或网站。

```python
from agentscope.message import Msg

# 来自Alice的简单文本消息示例
message_from_alice = Msg("Alice", "Hi!")

# 来自Bob的带有附加图像的消息示例
message_from_bob = Msg("Bob", "What about this picture I took?", url="/path/to/picture.jpg")
```

为了在两个智能体之间开始对话，例如`dialog_agent`和`user_agent`，您可以使用以下循环。对话将持续进行，直到用户输入`"exit"`，这将终止交互。

```python
x = None
while True:
    x = dialogAgent(x)
    x = userAgent(x)

    # 如果用户输入"exit"，则终止对话
    if x.content == "exit":
        print("Exiting the conversation.")
        break
```

进阶的使用中，AgentScope提供了Pipeline来管理智能体之间消息流的选项。
其中`sequentialpipeline`代表顺序对话，每个智能体从上一个智能体接收消息并生成其响应。

```python
from agentscope.pipelines.functional import sequentialpipeline

# 在Pipeline结构中执行对话循环
x = None
while x is None or x.content != "exit":
  x = sequentialpipeline([dialog_agent, user_agent])
```

有关如何使用Pipeline进行复杂的智能体交互的更多细节，请参考[[Agent Interactions: Dive deeper into Pipelines and Message Hub]](202-pipeline)。

[[返回顶部]](#103-example-zh)
