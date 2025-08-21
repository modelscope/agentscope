# Router Agent Example

## What This Example Demonstrates

This example showcases a **Router Agent** implementation using AgentScope framework. The Router Agent acts as an intelligent dispatcher that analyzes user questions and routes them to the most appropriate specialized agents for optimal responses.

### Key Features:

- **Intelligent Routing**: Automatically analyzes user questions and routes to appropriate specialized agents
- **Multi-Agent Collaboration**: Coordinates between specialized agents for math and history domains
- **Structured Output**: Uses Pydantic models to ensure structured routing decisions
- **Flexible Handling**: Can either route questions to specialists or answer directly when appropriate
- **Async Conversation**: Supports real-time conversation flow with streaming responses
- **Memory Management**: Each agent maintains its own conversation context

The router follows a smart decision-making process:

1. **Analyze** the user's question content and context
2. **Decide** whether to route to a specialist or handle directly
3. **Route** to the appropriate agent (Math/History) or respond directly
4. **Coordinate** the response back to the user

## How to Run This Example

1. **Set Environment Variable**:

   ```
   export DASHSCOPE_API_KEY="your_dashscope_api_key_here"
   ```

2. **Run the script**:

   ```
   python main.py
   ```

3. **Interact with the system**:

   ```
   User: Calculate 15 * 8 + 23
   Router: I'm going to route this calculation to our math specialist for an accurate response.
   Math: The calculation 15 * 8 + 23 equals 143.
   User: When did World War II end?
   Router: I will route your question to our history specialist who can provide you with the exact date of when World War II ended.
   History: World War II ended on September 2, 1945, ...
   user: hello
   Router: Hello! How can I assist you today?
   ```

## Replace the Model and Formatter

AgentScope provides several built-in model implementations that you can easily switch between. You can also implement your own custom model if needed.

For example, to use the OpenAI model, you can replace the model configuration in the create_agent function:

```python
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter

def create_agent(name: str, sys_prompt: str) -> ReActAgent:
    """Create a ReActAgent with OpenAI configuration."""
    return ReActAgent(
        name=name,
        sys_prompt=sys_prompt,
        model=OpenAIChatModel(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name="gpt-4",
            stream=True,
        ),
        formatter=OpenAIChatFormatter(),  # Use matching formatter
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
    )
```

## Customizing the Router System

### Adding New Specialized Agents

You can easily extend the system with additional specialized agents:

```python
# Add new agent prompt
SCIENCE_PROMPT = "You are a science assistant specializing in physics, chemistry, and biology."

# Create the agent in main()
agent_science = create_agent("Science", SCIENCE_PROMPT)

# Update routing logic
elif agent_name == "Science":
    msg = await agent_science(user_msg)

# Update ROUTER_PROMPT to include the new agent
```

### Modifying Routing Rules

To add new agents, update the `ROUTER_PROMPT` by adding:


```python
ROUTER_PROMPT = """
# Add to DECISION PROCESS section:
    - If it's a science question, route it to the science agent.

# Add to Available Agents section:
    - Science: Specialized in physics, chemistry, and biology questions.
"""
```

## Notes

⚠️ **Structured Output**: The RouterResponse model ensures consistent routing decisions. Make sure the agent_name values match your routing logic exactly.

🔧 **Model Compatibility**: Ensure your chosen model supports structured output generation for optimal routing performance.

🎯 **Routing Accuracy**: The quality of routing decisions depends on clear system prompts and good model performance. Consider fine-tuning prompts based on your specific use cases.

🔄 **Extensibility**: The factory function pattern makes it easy to add new agents and modify configurations without changing core logic.