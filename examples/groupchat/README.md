# Multi-Agent Group Conversation in AgentScope

This example demonstrates a multi-agent group conversation using AgentScope. The script `main.py` orchestrates a group chat where a user agent and several assistant agents interact dynamically in a group conversation. The chat continues until the user types "exit", signaling the end of the session.

## Features

* Implements a real-time group conversation with multiple agents.
* User-driven conversation flows with easy-to-modify agent roles via `sys_prompt`.
* Round-based agent conversation selection with timeout for user agent.

```bash
# Note: Set your api_key in configs/model_configs.json first
python main.py
```
