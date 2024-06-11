(105-logging-en)=

# Logging

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

[[Return to the top]](#105-logging-en)
