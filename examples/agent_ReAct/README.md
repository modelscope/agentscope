# ReAct Agent in AgentScope

This example demonstrates how to use the ReAct agent in AgentScope to build a
simple conversation.

**Tip:** AgentScope provides two implementations of ReAct agent:
- `agentscope.agents.ReActAgent`: Extract tool calls from the text response of LLMs locally.
- `agentscope.agents.ReActAgentV2`: Use the tools API, where the tool calls extraction is done by the LLM API provider, currently supports OpenAI, DashScope, Anthropic.

They share the same interface, so you can easily switch between them. The
example in `main.py` use `ReActAgent` by default, you can change it to
`ReActAgentV2` by modifying the import statement.


To run this example, install agentscope and then execute the following command:

```bash
python main.py
```