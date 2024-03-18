(104-usecase-en)=

# Crafting Your First Application

<img src="https://img.alicdn.com/imgextra/i3/O1CN01dFpOh82643mygUh2Z_!!6000000007607-2-tps-1024-1024.png" alt="img" style="zoom:25%;" />

Before diving into the advanced topics of AgentScope, in this tutorial, we will give you a glance at building a Werewolf application with out-of-the-box components of AgentScope.

**Werewolf** is a well-known social-deduction game, that involves an imaginary village where a few villagers are secretly werewolves, and the objective is to identify who they are before they eliminate all other players. It's a good use case to demonstrate the interaction between multiple autonomous agents, each with its own objectives and the need for communication.

Let the adventure begin to unlock the potential of multi-agent applications with AgentScope!

## Getting Started

Firstly, ensure that you have installed and configured AgentScope properly. Besides, we will involve the basic concepts of `Model API`,  `Agent`, `Msg`, and `Pipeline,` as described in [Tutorial-Concept](101-agentscope).

**Note**: all the configurations and code for this tutorial can be found in `examples/werewolf`.

### Step 1: Prepare Model API and Set Model Configs

As we discussed in the last tutorial, you need to prepare your model configurations into a JSON file for standard OpenAI chat API, FastChat, and vllm. More details and advanced usages such as configuring local models with POST API are presented in [Tutorial-Model-API](203-model).

```json
[
    {
        "config_name": "gpt-4-temperature-0.0",
        "model_type": "openai",
        "model_name": "gpt-4",
        "api_key": "xxx",
        "organization": "xxx",
        "generate_args": {
            "temperature": 0.0
        }
    },
]
```

### Step 2: Define the Roles of Each Agent

In the Werewolf game, agents assume a variety of roles, each endowed with distinctive abilities and objectives. Below, we will outline the agent classes corresponding to each role:

- Villager: Ordinary townsfolk trying to survive.
- Werewolf: Predators in disguise, aiming to outlast the villagers.
- Seer: A villager with the power to see the true nature of one player each night.
- Witch: A villager who can save or poison a player each night.

To implement your own agent, you need to inherit `AgentBase` and implement the `reply` function, which is executed when an agent instance is called via `agent1(x)`.

```python
from agentscope.agents import AgentBase

class MyAgent(AgentBase):
    def reply(self, x):
        # Do something here
        ...
        return x
```

AgentScope provides several out-of-the-box Agents implements and organizes them as an *Agent Pool*. In this application, we use a built-in agent, `DictDialogAgent`. Here we give an example configuration of `DictDialogAgent` for a player assigned as the role of a werewolf:

```json
{
    "class": "DictDialogAgent",
    "args": {
        "name": "Player1",
        "sys_prompt": "Act as a player in a werewolf game. You are Player1 and\nthere are totally 6 players, named Player1, Player2, Player3, Player4, Player5 and Player6.\n\nPLAYER ROLES:\nIn werewolf game, players are divided into two werewolves, two villagers, one seer, and one witch. Note only werewolves know who are their teammates.\nWerewolves: They know their teammates' identities and attempt to eliminate a villager each night while trying to remain undetected.\nVillagers: They do not know who the werewolves are and must work together during the day to deduce who the werewolves might be and vote to eliminate them.\nSeer: A villager with the ability to learn the true identity of one player each night. This role is crucial for the villagers to gain information.\nWitch: A character who has a one-time ability to save a player from being eliminated at night (sometimes this is a potion of life) and a one-time ability to eliminate a player at night (a potion of death).\n\nGAME RULE:\nThe game consists of two phases: night phase and day phase. The two phases are repeated until werewolf or villager wins the game.\n1. Night Phase: During the night, the werewolves discuss and vote for a player to eliminate. Special roles also perform their actions at this time (e.g., the Seer chooses a player to learn their role, the witch chooses a decide if save the player).\n2. Day Phase: During the day, all surviving players discuss who they suspect might be a werewolf. No one reveals their role unless it serves a strategic purpose. After the discussion, a vote is taken, and the player with the most votes is \"lynched\" or eliminated from the game.\n\nVICTORY CONDITION:\nFor werewolves, they win the game if the number of werewolves is equal to or greater than the number of remaining villagers.\nFor villagers, they win if they identify and eliminate all of the werewolves in the group.\n\nCONSTRAINTS:\n1. Your response should be in the first person.\n2. This is a conversational game. You should respond only based on the conversation history and your strategy.\n\nYou are playing werewolf in this game.\n",
        "model_config_name": "gpt-3.5-turbo",
        "use_memory": true
    }
}
```

In this configuration, `Player1` is designated as a `DictDialogAgent`. The parameters include a system prompt (`sys_prompt`) that can guide the agent's behavior, a model config name (`model_config_name`) that determines the name of the model configuration, and a flag (`use_memory`) indicating whether the agent should remember past interactions.

For other players, configurations can be customized based on their roles. Each role may have different prompts, models, or memory settings. You can refer to the JSON file located at `examples/werewolf/configs/agent_configs.json` within the AgentScope examples directory.

### Step 3: Initialize AgentScope and the Agents

Now we have defined the roles in the application and we can initialize the AgentScope environment and all agents. This process is simplified by AgentScope via a few lines, based on the configuration files we've prepared (assuming there are **2** werewolves, **2** villagers, **1** witch, and **1** seer):

```python
import agentscope

# read model and agent configs, and initialize agents automatically
survivors = agentscope.init(
    model_configs="./configs/model_configs.json",
    agent_configs="./configs/agent_configs.json",
    logger_level="DEBUG",
)

# Define the roles within the game. This list should match the order and number
# of agents specified in the 'agent_configs.json' file.
roles = ["werewolf", "werewolf", "villager", "villager", "seer", "witch"]

# Based on their roles, assign the initialized agents to variables.
# This helps us reference them easily in the game logic.
wolves, villagers, witch, seer = survivors[:2], survivors[2:-2], survivors[-1], survivors[-2]
```

Through this snippet of code, we've allocated roles to our agents and associated them with the configurations that dictate their behavior in the application.

### Step 4: Set Up the Game Logic

In this step, you will set up the game logic and orchestrate the flow of the Werewolf game using AgentScope's helper utilities.

#### Leverage Pipeline and MsgHub

To simplify the construction of agent communication, AgentScope provides two helpful concepts: **Pipeline** and **MsgHub**.

- **Pipeline**: It allows users to program communication among agents easily.

    ```python
    from agentscope.pipelines import SequentialPipeline

    pipe = SequentialPipeline(agent1, agent2, agent3)
    x = pipe(x) # the message x will be passed and replied by agent 1,2,3 in order
    ```

- **MsgHub**: You may have noticed that all the above examples are one-to-one communication. To achieve a group chat, we provide another communication helper utility `msghub`. With it, the messages from participants will be broadcast to all other participants automatically. In such cases, participating agents even don't need input and output messages. All we need to do is to decide the order of speaking. Besides, `msghub` also supports dynamic control of participants.

    ```python
    with msghub(participants=[agent1, agent2, agent3]) as hub:
        agent1()
        agent2()

        # Broadcast a message to all participants
        hub.broadcast(Msg("Host", "Welcome to join the group chat!"))

        # Add or delete participants dynamically
        hub.delete(agent1)
        hub.add(agent4)
    ```

#### Implement Werewolf Pipeline

The game logic is divided into two major phases: (1) night when werewolves act, and (2) daytime when all players discuss and vote. Each phase will be handled by a section of code using pipelines to manage multi-agent communications.

- **1.1 Night Phase: Werewolves Discuss and Vote**

During the night phase, werewolves must discuss among themselves to decide on a target. The `msghub` function creates a message hub for the werewolves to communicate in, where every message sent by an agent is observable by all other agents within the `msghub`.

```python
# start the game
for i in range(1, MAX_GAME_ROUND + 1):
    # Night phase: werewolves discuss
    hint = HostMsg(content=Prompts.to_wolves.format(n2s(wolves)))
    with msghub(wolves, announcement=hint) as hub:
        for _ in range(MAX_WEREWOLF_DISCUSSION_ROUND):
            x = sequentialpipeline(wolves)
            if x.agreement:
                break
```

After the discussion, werewolves proceed to vote for their target, and the majority's choice is determined.  The result of the vote is then broadcast to all werewolves.

**Note**: the detailed prompts and utility functions can be found in `examples/werewolf`.

```python
        # werewolves vote
        hint = HostMsg(content=Prompts.to_wolves_vote)
        votes = [extract_name_and_id(wolf(hint).content)[0] for wolf in wolves]
        # broadcast the result to werewolves
        dead_player = [majority_vote(votes)]
        hub.broadcast(
            HostMsg(content=Prompts.to_wolves_res.format(dead_player[0])),
        )
```

- **1.2 Witch's Turn**

If the witch is still alive, she gets the opportunity to use her powers to either save the player chosen by the werewolves or use her poison.

```python
    # Witch's turn
    healing_used_tonight = False
    if witch in survivors:
        if healing:
            # Witch decides whether to use the healing potion
            hint = HostMsg(
                content=Prompts.to_witch_resurrect.format_map(
                    {"witch_name": witch.name, "dead_name": dead_player[0]},
                ),
            )
            # Witch decides whether to use the poison
            if witch(hint).resurrect:
                healing_used_tonight = True
                dead_player.pop()
                healing = False
```

- **1.3 Seer's Turn**

The seer has a chance to reveal the true identity of a player. This information can be crucial for the villagers. The `observe()` function allows each agent to take note of a message without immediately replying to it.

```python
    # Seer's turn
    if seer in survivors:
        # Seer chooses a player to reveal their identity
        hint = HostMsg(
            content=Prompts.to_seer.format(seer.name, n2s(survivors)),
        )
        x = seer(hint)

        player, idx = extract_name_and_id(x.content)
        role = "werewolf" if roles[idx] == "werewolf" else "villager"
        hint = HostMsg(content=Prompts.to_seer_result.format(player, role))
        seer.observe(hint)
```

- **1.4 Update Alive Players**

Based on the actions taken during the night, the list of surviving players needs to be updated.

```python
    # Update the list of survivors and werewolves after the night's events
    survivors, wolves = update_alive_players(survivors, wolves, dead_player)
```

- **2.1 Daytime Phase: Discussion and Voting**

During the day, all players will discuss and then vote to eliminate a suspected werewolf.

```python
    # Daytime discussion
    with msghub(survivors, announcement=hints) as hub:
        # Discuss
        x = sequentialpipeline(survivors)
        # Vote
        hint = HostMsg(content=Prompts.to_all_vote.format(n2s(survivors)))
        votes = [extract_name_and_id(_(hint).content)[0] for _ in survivors]
        vote_res = majority_vote(votes)
        # Broadcast the voting result to all players
        result = HostMsg(content=Prompts.to_all_res.format(vote_res))
        hub.broadcast(result)
        # Update the list of survivors and werewolves after the vote
        survivors, wolves = update_alive_players(survivors, wolves, vote_res)
```

- **2.2 Check for Winning Conditions**

After each phase, the game checks if the werewolves or villagers have won.

```python
        # Check if either side has won
        if check_winning(survivors, wolves, "Moderator"):
            break
```

- **2.3 Continue to the Next Round**

If neither werewolves nor villagers win, the game continues to the next round.

```python
        # If the game hasn't ended, prepare for the next round
        hub.broadcast(HostMsg(content=Prompts.to_all_continue))
```

These code blocks outline the core game loop for Werewolf using AgentScope's `msghub` and `pipeline`, which help to easily manage the operational logic of an application.

### Step 5: Run the Application

With the game logic and agents set up, you're ready to run the Werewolf game. By executing the `pipeline`, the game will proceed through the predefined phases, with agents interacting based on their roles and the strategies coded above:

```bash
cd examples/werewolf
python main.py  # Assuming the pipeline is implemented in main.py
```

As the game starts, you'll see output in the terminal, similar to the logs below, which illustrate how the game unfolds:

```bash
Moderator: Player1 and Player2, you are werewolves. If you are alone, eliminate a player, else discuss with your teammates and reach an agreement. Response in the following format which can be loaded by  json.loads(){
    "thought": "thought",
    "speak": "thoughts summary to say to others",
    "agreement": "whether the discussion reached an agreement or not(true/false)"
}
Player1: Player2, let's discuss who we should eliminate tonight.
Player2: I think we should eliminate Player4 tonight. They seem suspicious to me.
Player1: I think we should eliminate Player4 tonight. They seem suspicious to me.
Player2: I agree with Player2, let's eliminate Player4 tonight. They seem suspicious.
Moderator: Which player do you vote to kill? Response in the following format which can be loaded by python json.loads()
{{
   "thought": "thought" ,
   "speak": "player_name"
}}
Player1: Player4
Player2: Player4
Moderator: The player with the most votes is Player4.
Moderator: Player6, you're witch. Tonight Player4 is eliminated. Would you like to resurrect Player4? Response in the following format which can be loaded by python json.loads()
{
    "thought": "thought",
    "speak": "thoughts summary to say",
    "resurrect": "true/false"
}
Player6: I have considered the options, and I choose to resurrect Player4.
Moderator: Player5, you're seer. Which player in Player1, Player2, Player3, Player4, Player5 and Player6 would you like to check tonight? Response in the following json format which can be loaded by python json.loads()
{
    "thought": "thought" ,
    "speak": "player_name"
}
Player5: Player3
Moderator: Okay, the role of Player3 is villager.
Moderator: The day is coming, all the players open your eyes. Last night is peaceful, no player is eliminated.
...
```

## Next step

Now you've grasped how to conveniently set up a multi-agent application with AgentScope. Feel free to tailor the game to include additional roles and introduce more sophisticated strategies. For more advanced tutorials that delve deeper into more capabilities of AgentScope, such as *memory management* and *service functions* utilized by agents, please refer to the tutorials in the **Advanced Exploration** section and look up the API references.


[[Return to the top]](#104-usecase-en)
