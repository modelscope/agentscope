
# Werewolf Game in AgentScope

This example demonstrates how to use AgentScope to play the Werewolf game, where six agents play against each other as werewolves and villagers.
You will learn the following features in AgentScope:

- How to make an agent respond with **different specified fields** in **different situations** in AgentScope (Like a finite state machine!)
- How to use **msghub** and **pipeline** in AgentScope to construct a game with **COMPLEX SOP**

## Background

The werewolf game involves a complex SOP with multiple roles and different phases. In these phases, players with different roles should take different actions, e.g. discussion, voting, checking roles (seer), using potions (witch), and so on.

Therefore, for an agent in werewolf game, it should be able to switch its status according to the game phase and its role, and respond accordingly.
Of course, we can hard code the SOP (or finite state machine) within the agent, but we expect the agent to be more **flexible**, **intelligent**, and **adaptive**, which means **the agent shouldn't be designed for a specific game only**. It should be able to adapt to different tasks and SOPs!

To achieve this goal, in AgentScope, we use a built-in [DictDialogAgent](https://github.com/modelscope/agentscope/blob/main/src/agentscope/agents/dict_dialog_agent.py) class, together with a [parser](https://modelscope.github.io/agentscope/en/tutorial/203-parser.html) module to construct the werewolf game.

Moreover, the [pipeline and msghub](https://modelscope.github.io/agentscope/en/tutorial/202-pipeline.html) in AgentScope enable us to easily construct a complex SOP with multiple agents. We hope the implementation is concise, clear and readable!

More details please refer to our tutorial:
- [Parser](https://modelscope.github.io/agentscope/en/tutorial/203-parser.html)
- [Pipeline and msghub](https://modelscope.github.io/agentscope/en/tutorial/202-pipeline.html)




https://github.com/DavdGao/AgentScope/assets/102287034/86951418-e1cc-486b-a3dc-b237a0108994





## Tested Models

This example has been tested with the following models:
- dashscope_chat (qwen-turbo)
- ollama_chat (llama3_8b)

## Prerequisites

To run this example, you need to:
- Set your API key in `./configs/model_configs.json`

[Optional] To play the game in person, see [werewolf.py](werewolf.py) for the complete code.


## Code Snippets

### About Pipeline and MsgHub

The following code is the implementation of daytime discussion in Werewolf. With msghub and pipeline, it's very easy to program a discussion among agents.

```python
    # ...
    with msghub(survivors, announcement=hints) as hub:
        # discuss
        set_parsers(survivors, Prompts.survivors_discuss_parser)
        x = sequentialpipeline(survivors)
    # ...
```

### About Parser

The parser is used to specify the required fields in the agent's response and how to handle them. Here's an example of a parser configuration:

```python
to_wolves_vote = "Which player do you vote to kill?"

wolves_vote_parser = MarkdownJsonDictParser(
    content_hint={
        "thought": "what you thought",
        "vote": "player_name",
    },
    required_keys=["thought", "vote"],
    keys_to_memory="vote",
    keys_to_content="vote",
)
```

In this example, the `MarkdownJsonDictParser` is used to parse the agent's response. The `content_hint` parameter specifies the expected fields and their descriptions. The `required_keys` parameter indicates the mandatory fields in the response. The `keys_to_memory` and `keys_to_content` parameters determine which fields should be stored in memory and included in the content of the returned message, respectively.
