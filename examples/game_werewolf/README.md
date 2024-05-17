
# Werewolf Game in AgentScope

This example demonstrates how to use AgentScope to play the Werewolf game, where six agents play against each other as werewolves and villagers. You will learn the following features in AgentScope:

- **Quick Setup**: How to initialize agents via agent config files
- **Syntactic Sugar**: How to use msghub and pipeline to construct a complex workflow with less than 100 lines of code
- **Prompt to Variable**: How to obtain variables from agents using prompts


## Tested Models

This example has been tested with the following models:
- dashscope_chat (qwen-turbo)


## Prerequisites

To run this example, you need to:
- Set your API key in `./configs/model_configs.json`

[Optional] To play the game in person, see [werewolf.py](werewolf.py) for the complete code.


## Code Snippets

### Quick Setup

The following code reads both model and agent configs, and initializes agents automatically:

```python
# read model and agent configs, and initialize agents automatically
survivors = agentscope.init(
    model_configs="./configs/model_configs.json",
    agent_configs="./configs/agent_configs.json",
)
```

In the agent config, you only need to specify the agent class under `agentscope.agents` and the required arguments. Taking Player1 as an example, its config is as follows:

```json
{
    "class": "DictDialogAgent",
    "args": {
        "name": "Player1",
        "sys_prompt": "Act as a player in a werewolf game. You are Player1 and\nthere are totally 6 players, named Player1, Player2, Player3, Player4, Player5 and Player6.\n\nPLAYER ROLES:\nIn werewolf game, players are divided into two werewolves, two villagers, one seer and one witch. Note only werewolves know who are their teammates.\nWerewolves: They know their teammates' identities and attempt to eliminate a villager each night while trying to remain undetected.\nVillagers: They do not know who the werewolves are and must work together during the day to deduce who the werewolves might be and vote to eliminate them.\nSeer: A villager with the ability to learn the true identity of one player each night. This role is crucial for the villagers to gain information.\nWitch: A character who has a one-time ability to save a player from being eliminated at night (sometimes this is a potion of life) and a one-time ability to eliminate a player at night (a potion of death).\n\nGAME RULE:\nThe game is consisted of two phases: night phase and day phase. The two phases are repeated until werewolf or villager win the game.\n1. Night Phase: During the night, the werewolves discuss and vote for a player to eliminate. Special roles also perform their actions at this time (e.g., the Seer chooses a player to learn their role, the witch chooses a decide if save the player).\n2. Day Phase: During the day, all surviving players discuss who they suspect might be a werewolf. No one reveals their role unless it serves a strategic purpose. After the discussion, a vote is taken, and the player with the most votes is \"lynched\" or eliminated from the game.\n\nVICTORY CONDITION:\nFor werewolves, they win the game if the number of werewolves is equal to or greater than the number of remaining villagers.\nFor villagers, they win if they identify and eliminate all of the werewolves in the group.\n\nCONSTRAINTS:\n1. Your response should be in the first person.\n2. This is a conversational game. You should response only based on the conversation history and your strategy.\n\nYou are playing werewolf in this game.\n",
        "model_config_name": "gpt-3.5-turbo",
        "use_memory": true
    }
}
```

### Syntactic Sugar

The following code is the implementation of daytime discussion in Werewolf. With msghub and pipeline, it's very easy to program a discussion among agents.

```python
    # ...
    with msghub(survivors, announcement=hints) as hub:
        # discuss
        x = sequentialpipeline(survivors)
    # ...
```

### Prompt to Variable

Sometimes, we need to extract required variables from agent responses. Taking a discussion as an example, we want the agent to determine if they reach an agreement during the discussion.

The following prompt requires the agent to respond with an "agreement" field to indicate whether they reach an agreement or not.

```text
... Response in the following format which can be loaded by
json.loads() in python
{{
    "thought": "thought",
    "speak": "thoughts summary to say to others",
    "agreement": "whether the discussion reached an agreement or not (true/false)"
}}
```

With the arguments `parse_func`, `fault_handler`, and `max_retries` in [`DictDialogAgent`](../../src/agentscope/agents/dict_dialog_agent.py), we can directly use the variable `x.agreement` to know if the discussion reached an agreement.

More details please refer to the code of [`DictDialogAgent`](../../src/agentscope/agents/dict_dialog_agent.py) and our documents.

```python
    # ...
    with msghub(wolves, announcement=hint) as hub:
        for _ in range(MAX_WEREWOLF_DISCUSSION_ROUND):
            x = sequentialpipeline(wolves)
            if x.get("agreement", False):
                break
    # ...
```