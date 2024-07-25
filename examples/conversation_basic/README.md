# Multi-Agent Conversation in AgentScope

This example will show how to program a multi-agent conversation in AgentScope.
Complete code is in `conversation.py`, which set up a user agent and an
assistant agent to have a conversation. When user input "exit", the
conversation ends.
You can modify the `sys_prompt` to change the role of assistant agent.
```bash
# Note: Set your api_key in conversation.py first
python conversation.py
```
## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- dashscope_chat (qwen-max)
- ollama_chat (ollama_llama3_8b)
- gemini_chat (models/gemini-pro)

## Prerequisites
To set up model serving with open-source LLMs, follow the guidance in
[scripts/README.md](https://github.com/modelscope/agentscope/blob/main/scripts/README.md).
