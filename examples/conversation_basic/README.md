# Multi-Agent Conversation in AgentScope
This is a demo of how to program a multi-agent conversation in AgentScope.
Complete code is in `conversation.py`, which set up a user agent and an
assistant agent to have a conversation. When user input "exit", the
conversation ends.
You can modify the `sys_prompt` to change the role of assistant agent.
```bash
# Note: Set your api_key in conversation.py first
python conversation.py
```
To set up model serving with open-source LLMs, follow the guidance in
[scripts/REAMDE.md](../../scripts/README.md).