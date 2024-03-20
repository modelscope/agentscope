(104-usecase-zh)=

# 创造您的第一个应用

<img src="https://img.alicdn.com/imgextra/i3/O1CN01dFpOh82643mygUh2Z_!!6000000007607-2-tps-1024-1024.png" alt="img" style="zoom:25%;" />

在介绍更多AgentScope的高阶内容前，我们先会给您展示如何利用AgentScope内置的功能，快速搭建一个狼人杀游戏模拟应用。

**狼人杀**是一个广为人知的桌面游戏。游戏设定在一个虚拟世界的村庄里。村庄里有真正的村民、也有伪装成村民的狼人；每个参与者都在游戏中都有自己的角色。对于村民方而言，他们的胜利条件是在全灭之前找出并杀死所有的狼人；对于狼人方而言，胜利条件就是杀死所有的村民。狼人杀这样的游戏是一个很好的可以自动展示多个有不同目标的智能体之间如何互动。

话不多说，让我们开始通过狼人杀这个游戏，解锁AgentScope多智体的应用吧！

## 开始

首先，确保您已经正确安装和配置好AgentScope。除此之外，本节内容会涉及到`Model API`,  `Agent`, `Msg`和 `Pipeline`这几个概念（详情可以参考[关于AgentScope](101-agentscope)）。以下是本节教程内容概览。

**提示**：本教程中的所有配置和代码文件均可以在`examples/werewolf`中找到。

### 第一步: 准备模型API和设定模型配置

就像我们在上一节教程中展示的，您需要为了您选择的OpenAI chat API, FastChat, 或vllm 准备一个JSON样式的模型配置文件。更多细节和高阶永达，比如用POST API配置本地模型，可以参考[关于模型](203-model)。

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

### 第二步：定义每个智能体（Agent）的角色

在狼人杀游戏中，不同智能体会扮演不同角色；不同角色的智能体也有不同的能力和目标。下面便是我们大概归纳

- 普通村民：普通的村民，没有特殊能力，只是寻求生存到最后。
- 狼人：伪装成村民的掠夺者，目标是比村民活得更久并杀死村民们。
- 预言家：一位拥有每晚看到一名玩家真实身份能力的村民。
- 女巫：一位村民，每晚可以救活或毒杀一名玩家

要实现你自己的agent，你需要继承AgentBase并实现reply函数，当通过agent1(x)调用agent实例时，将执行此函数。

```python
from agentscope.agents import AgentBase

class MyAgent(AgentBase):
    def reply(self, x):
        # Do something here
        ...
        return x
```

AgentScope提供了几种开箱即用的agent实现，作为一个agent样例池。在这个应用程序中，我们使用一个内置agent，DictDialogAgent。这里我们给出一个将玩家分配为狼人角色的DictDialogAgent的示例配置：

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

在这个配置中，Player1被指定为一个DictDialogAgent。参数包括一个系统提示（sys_prompt），它可以指导agent的行为；一个模型配置名（model_config_name），它决定了模型配置的名称；以及一个标志（use_memory），指示agent是否应该记住过去的互动。

对于其他玩家，大家可以根据他们的角色进行定制。每个角色可能有不同的提示、模型或记忆设置。你可以参考位于AgentScope示例目录下的`examples/werewolf/configs/agent_configs.json`文件。

### 第三步：初始化AgentScope和Agents

现在我们已经定义了角色，我们可以初始化AgentScope环境和所有agents。这个过程通过AgentScope的几行代码和我们准备的配置文件（假设有2个狼人、2个村民、1个女巫和1个预言家）就能简单完成：

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

上面这段代码中，我们为我们的agent分配了角色，并将它们与决定它们行为的配置相关联。

### 第四步：构建游戏逻辑

在这一步中，你将使用AgentScope的辅助工具设置游戏逻辑，并组织狼人游戏的流程。

#### 使用 Pipeline 和 MsgHub

为了简化agent通信的构建，AgentScope提供了两个有用的概念：Pipeline和MsgHub。

- **Pipeline**：它能让用户轻松地编程实现agent之间的不同通信编排。

    ```python
    from agentscope.pipelines import SequentialPipeline

    pipe = SequentialPipeline(agent1, agent2, agent3)
    x = pipe(x) # the message x will be passed and replied by agent 1,2,3 in order
    ```

- **MsgHub**：你可能已经注意到，上述所有例子都是一对一通信。为了实现群聊，我们提供了另一个通信辅助工具msghub。有了它，参与者的消息将自动广播给所有其他参与者。在这种情况下，参与agent甚至不需要输入和输出消息。我们需要做的只是决定发言的顺序。此外，msghub还支持参与者的动态控制。

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

#### 实现狼人杀的游戏流程

游戏逻辑分为两个主要阶段：(1)夜晚，狼人行动；以及(2)白天，所有玩家讨论和投票。每个阶段都将通过使用pipelines来管理多agent通信的代码部分来处理。

- **1.1 夜晚阶段：狼人讨论和投票**

在夜晚阶段，狼人必须相互讨论以决定一个要杀死的目标。msghub函数为狼人之间的通信创建了一个消息中心，其中每个agent发送的消息都能被msghub内的所有其他agent观察到。

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

讨论结束后，根据少数服从多数，狼人进行投票选出他们的目标。然后，投票的结果将广播给所有狼人。

注意：具体的提示和实用函数可以在`examples/werewolf`中找到。

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

- **1.2 女巫的回合**

如果女巫还活着，她就有机会使用她的力量：救被狼人选中的（被杀的）玩家，或使用她的毒药去杀一位玩家。

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

- **1.3 预言家的回合**

预言家有机会揭示一名玩家的真实身份。这信息对于村民方来说可能至关重要。`observe()`函数允许每个agent注意到一个消息，而不需要立即产生回复。

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

- **1.4 更新存活玩家**

根据夜间采取的行动，程序需要更新幸存玩家的列表。

```python
    # Update the list of survivors and werewolves after the night's events
    survivors, wolves = update_alive_players(survivors, wolves, dead_player)
```

- **2.1 白天阶段：讨论和投票**

在白天，所有存活玩家将讨论然后投票以淘汰一名疑似狼人的玩家。

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

- **2.2 检查胜利条件**

每个阶段结束后，游戏会检查是狼人还是村民获胜。

```python
        # Check if either side has won
        if check_winning(survivors, wolves, "Moderator"):
            break
```

- **2.3 继续到下一轮**

如果狼人和村民都没有获胜，游戏将继续到下一轮。

```python
        # If the game hasn't ended, prepare for the next round
        hub.broadcast(HostMsg(content=Prompts.to_all_continue))
```

这些代码块展现了使用AgentScope的`msghub`和`pipeline`的狼人游戏的核心游戏循环，这些工具有助于轻松管理应用程序的操作逻辑。

### 第五步：运行应用

完成了以上游戏逻辑和agent的设置，你已经可以运行狼人游戏了。通过执行`pipeline`，游戏将按预定义的阶段进行，agents
基于它们的角色和上述编码的策略进行互动：

```bash
cd examples/game_werewolf
python main.py  # Assuming the pipeline is implemented in main.py
```

游戏开始后，你将在终端看到类似于下面的日志输出。这些日志展示了游戏是如何展开的：

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

## 下一步

现在你已经掌握了如何使用AgentScope方便地设置多agent应用程序。您可以随意修改游戏，包括引入额外的角色或者引入更复杂的策略。如果你想更深入地探索AgentScope的更多功能，比如agent使用的内存管理和服务函数，请参考高级探索部分的教程并查阅API参考。

[[返回顶部]](#104-usecase-zh)
