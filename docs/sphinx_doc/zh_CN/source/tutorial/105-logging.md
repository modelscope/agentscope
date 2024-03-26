(105-logging-zh)=

# 日志和WebUI

本节教程主要是关于AgentScope的日志记录（logging）功能。我们会介绍如何能美观地将这些日志可视化。这个模块会帮助您更方便、清晰、有组织地跟踪智能体之间的互动和各种系统消息。

## Logging

日志功能首先包含的是一个基于Python内置 `logging`的根据多智体场景可定制化的`loguru.logger`模块。其包含下面的一些特性：

- **调整输出字体颜色**：为了增加日志的可读性，该模块为不同的在对话中发言智能体提供不同颜色的字体高亮。
- **重定向错误输出(stderr)**： 该模块自动抓取报错信息，在日志中用`ERROR`层级记录。
- **客制化日志记录等级**： 该模块增加了一个日志记录等级`CHAT`，用来记录智能体之间的对话和互动。
- **定制格式**：格式化日志包含了时间戳、记录等级、function名字和行号。智能体之间的对话会用不同的格式显示。

### 设置日志记录（Logger）

我们推荐通过`agentscope.init`来设置logger，包括设定记录等级：

```python
import agentscope

LOG_LEVEL = Literal[
    "CHAT",
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
]

agentscope.init(..., logger_level="INFO")
```

### Logging a Chat Message

### 记录对话消息

开发者可以通过记录`message`来追踪智能体之间的对话。下面是一些简单的如何记录`message`的例子例子:

```python
# Log a simple string message.
logger.chat("Hello World!")

# Log a `msg` representing dialogue with a speaker and content.
logger.chat({"name": "User", "content": "Hello, how are you?"})
logger.chat({"name": "Agent", "content": "I'm fine, thank you!"})
```

### 记录系统信息

系统日志对于跟踪应用程序的状态和识别问题至关重要。以下是记录不同级别系统信息的方法：

```python
# Log general information useful for understanding the flow of the application.
logger.info("The dialogue agent has started successfully.")

# Log a warning message indicating a potential issue that isn't immediately problematic.
logger.warning("The agent is running slower than expected.")

# Log an error message when something has gone wrong.
logger.error("The agent encountered an unexpected error while processing a request.")
```

## 将日志与WebUI集成

为了可视化这些日志和运行细节，AgentScope提供了一个简单的网络界面。

### 快速运行

你可以用以下Python代码中运行WebUI：

```python
import agentscope

agentscope.web.init(
    path_save="YOUR_SAVE_PATH"
)
```

通过这种方式，你可以在 `http://127.0.0.1:5000` 中看到所有运行中的实例和项目，如下所示

![webui](https://img.alicdn.com/imgextra/i3/O1CN01kpHFkn1HpeYEkn60I_!!6000000000807-0-tps-3104-1849.jpg)

通过点击一个运行中的实例，我们可以观察到更多细节。

![The running details](https://img.alicdn.com/imgextra/i2/O1CN01AZtsf31MIHm4FmjjO_!!6000000001411-0-tps-3104-1849.jpg)

### 注意

WebUI仍在开发中。我们将在未来提供更多功能和更好的用户体验。

[[返回顶部]](#105-logging-zh)
