# MCP-Agent Conversation in AgentScope

## Things You Need to Know

This is just a quick preview demo, demonstrating how you can connect to MCP with agentscope. MCP is being integrated into AgentScope more natively, coming soon.

## MCP-Agent Conversation Demo

This example illustrates how to establish a conversation between a user agent and an MCP agent using AgentScope. The conversation will proceed until the user inputs "exit". You can personalize the role of the assistant agent by altering the `sys_prompt`.

```bash
# Note: Ensure to set your api_key in main.py first
python main.py
```
In this example, the `mcp_servers_config.json` file includes the following configuration:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/YOU_USER_NAME/Desktop"  # Change YOU_USER_NAME to actual user name
      ]
    }
  }
}
```

To connect additional MCP servers, please refer to: [Model Context Protocol Servers](https://github.com/modelcontextprotocol/servers)

## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- dashscope_chat (qwen-max)

## Prerequisites
```bash
pip install -r requirements.txt
```

## Disclaimer
Some codes are modified from: https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/clients/simple-chatbot

