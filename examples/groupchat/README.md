# Multi-Agent Group Conversation in AgentScope

This example demonstrates a multi-agent group conversation facilitated by AgentScope. The script `main.py` sets up a virtual chat room where a user agent interacts with several NPC (non-player character) agents. The chat utilizes a special **"@"** mention functionality, which allows participants to address specific agents and have a more directed conversation.

## Key Features

- **Real-time Group Conversation**: Engage in a chat with multiple agents responding in real time.
- **@ Mention Functionality**: Use the "@" symbol followed by an agent's name to specifically address that agent within the conversation.
- **Dynamic Flow**: User-driven conversation with agents responding based on the context and mentions.
- **Configurable Agent Roles**: Easily modify agent roles and behaviors by editing the `sys_prompt` in the configuration files.
- **User Timeout**: If the user does not respond within a specified time, the conversation continues with the next agent.

## How to Use

To start the group conversation, follow these steps:

1. Make sure to set your `api_key` in the `configs/model_configs.json` file.
2. Run the script using the following command:

```bash
python main.py

# or launch agentscope studio
as_studio main.py
```

1. To address a specific agent in the chat, type "@" followed by the agent's name in your message.
2. To exit the chat, simply type "exit" when it's your turn to speak.

## Background and Conversation Flow

The conversation takes place in a simulated chat room environment with roles defined for each participant. The user acts as a regular chat member with the ability to speak freely and address any agent. NPC agents are pre-configured with specific roles that determine their responses and behavior in the chat. The topic of the conversation is open-ended and can evolve organically based on the user's input and agents' programmed personas.

### Example Interaction

```
User input: Hi, everyone! I'm excited to join this chat.
AgentA: Welcome! We're glad to have you here.
User input: @AgentB, what do you think about the new technology trends?
AgentB: It's an exciting time for tech! There are so many innovations on the horizon.
...
```

## Customization Options

The group conversation script provides several options for customization, allowing you to tailor the chat experience to your preferences.

You can customize the conversation by editing the agent configurations and model parameters. The `agent_configs.json` file allows you to set specific behaviors for each NPC agent, while `model_configs.json` contains the parameters for the conversation model.

### Changing User Input Time Limit

The `USER_TIME_TO_SPEAK` variable sets the time limit (in seconds) for the user to input their message during each round. By default, this is set to 10 seconds. You can adjust this time limit by modifying the value of `USER_TIME_TO_SPEAK` in the `main.py` script.

For example, to change the time limit to 20 seconds, update the line in `main.py` as follows:

```
USER_TIME_TO_SPEAK = 20  # User has 20 seconds to type their message
```

### Setting a Default Topic for the Chat Room

The `DEFAULT_TOPIC` variable defines the initial message or topic of the chat room. It sets the stage for the conversation and is announced at the beginning of the chat session. You can change this message to prompt a specific discussion topic or to provide instructions to the agents.

To customize this message, modify the `DEFAULT_TOPIC` variable in the `main.py` script. For instance, if you want to set the default topic to discuss "The Future of Artificial Intelligence," you would change the code as follows:

```python
DEFAULT_TOPIC = """
This is a chat room about the Future of Artificial Intelligence and you can
speak freely and briefly.
"""
```

With these customizations, the chat room can be tailored to fit specific themes or time constraints, enhancing the user's control over the chat experience.
