(105-logging-en)=

# Logging and WebUI

Welcome to the tutorial on logging in multi-agent applications with AgentScope. We'll also touch on how you can visualize these logs using a simple web interface. This guide will help you track the agent's interactions and system information in a clearer and more organized way.

## Logging

The logging utilities consist of a custom setup for the `loguru.logger`, which is an enhancement over Python's built-in `logging` module. We provide custom features:

- **Colored Output**: Assigns different colors to different speakers in a chat to enhance readability.
- **Redirecting Standard Error (stderr)**: Captures error messages and logs them with the `ERROR` level.
- **Custom Log Levels**: Adds a custom level called `CHAT` that is specifically designed for logging dialogue interactions.
- **Special Formatting**: Format logs with timestamps, levels, function names, and line numbers. Chat messages are formatted differently to stand out.

### Setting Up the Logger

We recommend setting up the logger via `agentscope.init`, and you can set the log level:

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

Logging chat messages helps keep a record of the conversation between agents. Here's how you can do it:

```python
# Log a simple string message.
logger.chat("Hello World!")

# Log a `msg` representing dialogue with a speaker and content.
logger.chat({"name": "User", "content": "Hello, how are you?"})
logger.chat({"name": "Agent", "content": "I'm fine, thank you!"})
```

### Logging a System information

System logs are crucial for tracking the application's state and identifying issues. Here's how to log different levels of system information:

```python
# Log general information useful for understanding the flow of the application.
logger.info("The dialogue agent has started successfully.")

# Log a warning message indicating a potential issue that isn't immediately problematic.
logger.warning("The agent is running slower than expected.")

# Log an error message when something has gone wrong.
logger.error("The agent encountered an unexpected error while processing a request.")
```

## Integrating logging with WebUI

To visualize these logs and running details, AgentScope provides a simple
web interface.

### Quick Running

You can run the WebUI in the following python code:

```python
import agentscope

agentscope.web.init(
    path_save="YOUR_SAVE_PATH"
)
```

By this way, you can see all the running instances and projects in `http://127.0.0.1:5000` as follows:

![webui](https://img.alicdn.com/imgextra/i3/O1CN01kpHFkn1HpeYEkn60I_!!6000000000807-0-tps-3104-1849.jpg)

By clicking a running instance, we can observe more details.

![The running details](https://img.alicdn.com/imgextra/i2/O1CN01AZtsf31MIHm4FmjjO_!!6000000001411-0-tps-3104-1849.jpg)

### Note

The WebUI is still under development. We will provide more features and
better user experience in the future.

[[Return to the top]](#105-logging-en)
