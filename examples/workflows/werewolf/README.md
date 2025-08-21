# 🐺 Werewolf Game Powered by AgentScope

A multi-agent werewolf game built with AgentScope, demonstrating agent interactions, group decision-making, and role-based gameplay mechanics.

## 🎯 AgentScope Integration Highlights

### **Multi-Agent Message Formatting**

`MultiAgentFormatters` such as `DashScopeMultiAgentFormatter`   are specifically designed for multi-agent scenarios:

```python
ReActAgent(
    name="Player1",
    formatter=DashScopeMultiAgentFormatter(),  # Essential for multi-agent memory
    memory=InMemoryMemory(),
    ...
)
```

**Key Features:**

- **Speaker Identity Preservation**: Each message includes the speaker's name (e.g., "Player1: I think Player3 is suspicious")
- **Contextual Memory Management**: Automatically organizes conversation history with <history> tags
- **Multi-Modal Support**: Handles text, images, audio, and tool calls in group conversations
- **Intelligent History Structuring**: Combines previous messages into a structured format for each agent's memory

Each agent receives formatted conversation history like:

```
# Conversation History
The content between <history></history> tags contains your conversation history
<history>
Player1: I think we should target Player3tonight
Player2: I agree, but we need to be careful about the seer
Player1: Good point, let's discuss our strategy
</history>
```

This enables each agent to:

- Track who said what in group discussions
- Maintain coherent memories across conversation rounds
- Reference previous statements by specific players
- Build relationships and suspicions based on conversation history

### **Sequential Agent Pipeline**

`sequential_pipeline` orchestrates turn-based agent interactions:

```python
# Free-form discussion among all players
await sequential_pipeline(survivors)
```

**Pipeline Features:**

- **Turn-Based Coordination**: Ensures agents speak in sequence, preventing message overlap
- **Flexible Participation**: Supports both structured discussions with specific goals and open conversations
- **Automatic Flow Control**: Manages conversation flow without manual turn management

**Use Cases:**

- **Werewolf Strategy Discussions**: Coordinated planning between werewolf teammates
- **Village Debates**: Organized discussions among all surviving players

### **Multi-Agent Coordination**

AgentScope's `MsgHub` enables seamless group interactions:

```python
async with MsgHub(wolves, announcement=hint) as hub:
    for _ in range(MAX_WEREWOLF_DISCUSSION_ROUND):
        x = None
        for wolf in wolves:
            x = await wolf(x, structured_model=WolfDiscussionModel)
        if x.metadata.get("finish_discussion", False):
            break
```

**Coordination Capabilities:**

- **Group Discussions**: Manages multi-participant conversations seamlessly
- **Message Broadcasting**: Distributes announcements to all participants

### **Structured Decision Making**

Pydantic models ensure reliable AI outputs:

```python
class VoteModel(BaseModel):
    name: str = Field(description="The name you vote for")

# Automatic validation and parsing
votes = await collect_votes(survivors, hint, VoteModel)
```

### **Async Agent Processing**

All agents operate concurrently:

```python
vote_tasks = [voter(hint, structured_model=VoteModel) for voter in voters]
results = await asyncio.gather(*vote_tasks)
```

## 🎮 Game Features

### **Complete Role System**

- **Werewolves** (2): Team coordination and elimination voting
- **Villagers** (2): Individual reasoning and survival
- **Seer** (1): Information gathering through role detection
- **Witch** (1): Strategic intervention with healing/poison abilities

### **Game Mechanics**

- **Night Phase**: Private werewolf discussions, special role actions
- **Day Phase**: Public debates and elimination voting
- **Win Conditions**: Werewolf majority or werewolf elimination

## 🚀 Quick Start

### Prerequisites

```
export DASHSCOPE_API_KEY="your_api_key"
```

### Run the Game

```
python werewolf.py
```

## 📁 Project Structure

``````
werewolf-game/
├── werewolf.py			# Main game loop and agent coordination
├── werewolf_utils.py     # Game logic utilities and models
├── prompt.py  						# Role prompts and game text
└── README.md
``````

### **Core Components**

**werewolf.py**: Game orchestration

- Night/day phase management
- Role action coordination
- Win condition checking

**werewolf_utils.py**: Game mechanics

- Vote aggregation: `majority_vote()`
- Player state management: `update_alive_players()`
- Win condition logic: `check_winning()`
- Structured models for all game actions

**prompt.py**: Role definitions

- Comprehensive role instructions
- Game phase prompts
- Result announcements

## ⚙️ Configuration

### Game Parameters

```python
MAX_WEREWOLF_DISCUSSION_ROUND = 3  # Night discussion rounds
MAX_GAME_ROUND = 6                 # Maximum game length
roles = ["werewolf", "werewolf", "villager", "villager", "seer", "witch"]
```

### Model and formatter Setup

```Python
model = OpenAIChatModel(
    model_name="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY"),
    stream=True,
)

formatter = OpenAIMultiAgentFormatter()
```

## 🔧 Customization

### **Adding Roles**

1. Define role in prompt template
2. Create corresponding Pydantic model
3. Add role logic to game loop
4. Update win conditions if needed

### **Game Rules**

- Modify discussion rounds and game length
- Adjust voting mechanisms
- Customize special abilities

### **Scaling**

```python
# Expand to 10+ players
roles = ["werewolf"] * 3+ ["villager"] *4 + ["seer", "witch", "hunter"]
```

