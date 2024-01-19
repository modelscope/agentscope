(105-logging)=

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

To visualize these logs, we provide a customized gradio component in `src/agentscope/web_ui`.

### Quick Running

For convince, we provide the pre-built app in a wheel file, you can run the WebUI in the following command:

```shell
pip install gradio_groupchat-0.0.1-py3-none-any.whl
python app.py
```

After the init and entering the UI port printed by `app.py`, e.g., `http://127.0.0.1:7860/`, you can choose `run.log.demo` in the top-middle `FileSelector` window (it's a demo log file provided by us). Then, the dialog and system log should be shown correctly in the bottom windows.

![webui](https://img.alicdn.com/imgextra/i2/O1CN01hSaFue1EdL2yCEznc_!!6000000000374-2-tps-3066-1808.png)

### For Other Customization

To customize the backend, or the frontend of the provided WebUI, you can

```shell
# generate the template codes
# for network connectivity problem, try to run
# `npm config rm proxy && npm config rm https-proxy` first
gradio cc create GroupChat --template Chatbot
# replace the generated app.py into our built-in app.py
cp -f app.py groupchat/demo
# debug and develop your web_ui
cd groupchat
# edit the app.py, or other parts you want, reference link:
# https://www.gradio.app/guides/custom-components-in-five-minutes
gradio cc dev
```

If you want to release the modification, you can do

```shell
gradio cc build
pip install <path-to-whl>
python app.py
```

[[Return to the top]](#logging-and-webui)
