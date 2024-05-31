let invocationEditor = null;

function initializeDashboardDetailInvocationPage(runId) {
    // load monaco editor
    require.config({paths: {'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@latest/min/vs'}});
    require(['vs/editor/editor.main'], function () {
        invocationEditor = monaco.editor.create(document.getElementById('invocation-content'), {
            language: 'json',
            theme: 'vs-light',
            minimap: {
                enabled: false  // 禁用minimap
            },
            scrollBeyondLastLine: false,
            readOnly: true,
        });
    });

    // fetch data from server
    fetch("/api/invocation/run/" + runId)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error("Failed to fetch invocation detail");
            }
        })
        .then(data => {
            var invocationTable = new Tabulator("#invocation-list", {
                data: data,
                columns: [
                    {
                        title: "Model Wrapper",
                        field: "model wrapper",
                        editor: false,
                        vertAlign: "middle",
                    },
                    {
                        title: "Timestamp",
                        field: "timestamp",
                        editor: false,
                        vertAlign: "middle",
                    },
                ],
                layout: "fitColumns",
            });

            // Set up row click event
            invocationTable.on("rowClick", function (e, row) {
                // Jump to the run detail page
                invocationEditor.setValue('{\n' +
                    '    "model_class": "PostAPIChatWrapper",\n' +
                    '    "timestamp": "20240513-212337",\n' +
                    '    "arguments": {\n' +
                    '        "url": "https://api.mit-spider.alibaba-inc.com/chatgpt/api/ask",\n' +
                    '        "json": {\n' +
                    '            "messages": [\n' +
                    '                {\n' +
                    '                    "role": "system",\n' +
                    '                    "name": "system",\n' +
                    '                    "content": "Act as a player in a werewolf game. You are Player2 and\\nthere are totally 6 players, named Player1, Player2, Player3, Player4, Player5 and Player6.\\n\\nPLAYER ROLES:\\nIn werewolf game, players are divided into two werewolves, two villagers, one seer and one witch. Note only werewolves know who are their teammates.\\nWerewolves: They know their teammates\' identities and attempt to eliminate a villager each night while trying to remain undetected.\\nVillagers: They do not know who the werewolves are and must work together during the day to deduce who the werewolves might be and vote to eliminate them.\\nSeer: A villager with the ability to learn the true identity of one player each night. This role is crucial for the villagers to gain information.\\nWitch: A character who has a one-time ability to save a player from being eliminated at night (sometimes this is a potion of life) and a one-time ability to eliminate a player at night (a potion of death).\\n\\nGAME RULE:\\nThe game is consisted of two phases: night phase and day phase. The two phases are repeated until werewolf or villager win the game.\\n1. Night Phase: During the night, the werewolves discuss and vote for a player to eliminate. Special roles also perform their actions at this time (e.g., the Seer chooses a player to learn their role, the witch chooses a decide if save the player).\\n2. Day Phase: During the day, all surviving players discuss who they suspect might be a werewolf. No one reveals their role unless it serves a strategic purpose. After the discussion, a vote is taken, and the player with the most votes is \\"lynched\\" or eliminated from the game.\\n\\nVICTORY CONDITION:\\nFor werewolves, they win the game if the number of werewolves is equal to or greater than the number of remaining villagers.\\nFor villagers, they win if they identify and eliminate all of the werewolves in the group.\\n\\nCONSTRAINTS:\\n1. Your response should be in the first person.\\n2. This is a conversational game. You should response only based on the conversation history and your strategy.\\n\\nYou are playing werewolf in this game.\\n"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "content": "Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "content": "Player2, I suggest we consider eliminating Player3. They seem to be asking a lot of questions which might indicate they are the Seer trying to gather information. What do you think?"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player2",\n' +
                    '                    "content": "Player1, your suggestion makes sense. It\'s possible Player3 could be the Seer. But we should also consider the possibility that they might just be a regular villager trying to help. What about Player4? They\'ve been rather quiet."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "content": "Player2, I see your point about Player4. However, I still believe Player3 might be a bigger threat. Their questions could be a strategy to identify us. If they are the Seer, it could be dangerous for us. Let\'s vote for Player3."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player2",\n' +
                    '                    "content": "Alright, Player1. I agree with you. Let\'s eliminate Player3."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "content": "Player3"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "content": "Which player do you vote to kill?"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player2",\n' +
                    '                    "content": "Player3"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "content": "The player with the most votes is Player3."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "content": "The day is coming, all the players open your eyes. Last night, the following player(s) has been eliminated: Player3."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "content": "Now the alive players are Player1, Player2, Player4, Player5 and Player6. Given the game rules and your role, based on the situation and the information you gain, to vote a player eliminated among alive players and to win the game, what do you want to say to others? You can decide whether to reveal your role. "\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "content": "I find Player4\'s silence a bit suspicious. Don\'t you think it\'s odd that they haven\'t contributed much to our discussions? Maybe they are trying to avoid drawing attention to themselves. I suggest we vote for Player4."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player2",\n' +
                    '                    "content": "I agree with Player1. Player4\'s silence is indeed suspicious. I also vote for Player4."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player4",\n' +
                    '                    "content": "I understand why my silence might seem suspicious, but I assure you, I am a villager. I was silent because I was trying to observe and gather information. I suggest we should focus on finding the real werewolves. Let\'s think about it, who has been aggressively pointing fingers without concrete evidence?"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player5",\n' +
                    '                    "content": "I agree that Player4\'s silence was suspicious, but their defense makes sense. They could\'ve been observing, just like us. We need to be careful about who we accuse and why. Let\'s not rush into conclusions. I suggest we continue observing for now."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player6",\n' +
                    '                    "content": "I agree with Player5. We shouldn\'t rush into conclusions. Let\'s continue observing and gathering information. As for Player4, I think we should give them a chance to prove their innocence."\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "content": "Player4"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "assistant",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "content": "Given the game rules and your role, based on the situation and the information you gain, to win the game, it\'s time to vote one player eliminated among the alive players. Which player do you vote to kill?"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "role": "system",\n' +
                    '                    "name": "system",\n' +
                    '                    "content": "You should respond a json object in a json fenced code block as follows:\\n```json\\n{\\"thought\\": \\"what you thought\\", \\"speak\\": \\"player_name\\"}\\n```"\n' +
                    '                }\n' +
                    '            ],\n' +
                    '            "model": "gpt-4",\n' +
                    '            "temperature": 0.5\n' +
                    '        },\n' +
                    '        "headers": {\n' +
                    '            "Content-Type": "application/json",\n' +
                    '            "Authorization": "Bearer eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjIyNTE4NiIsInBhc3N3b3JkIjoiMjI1MTg2IiwiZXhwIjoyMDA2OTMzNTY1fQ.wHKJ7AdJ22yPLD_-1UHhXek4b7uQ0Bxhj_kJjjK0lRM"\n' +
                    '        }\n' +
                    '    },\n' +
                    '    "response": {\n' +
                    '        "code": 200,\n' +
                    '        "data": {\n' +
                    '            "completion_tokens": 52,\n' +
                    '            "messages": [\n' +
                    '                {\n' +
                    '                    "content": "Act as a player in a werewolf game. You are Player2 and\\nthere are totally 6 players, named Player1, Player2, Player3, Player4, Player5 and Player6.\\n\\nPLAYER ROLES:\\nIn werewolf game, players are divided into two werewolves, two villagers, one seer and one witch. Note only werewolves know who are their teammates.\\nWerewolves: They know their teammates\' identities and attempt to eliminate a villager each night while trying to remain undetected.\\nVillagers: They do not know who the werewolves are and must work together during the day to deduce who the werewolves might be and vote to eliminate them.\\nSeer: A villager with the ability to learn the true identity of one player each night. This role is crucial for the villagers to gain information.\\nWitch: A character who has a one-time ability to save a player from being eliminated at night (sometimes this is a potion of life) and a one-time ability to eliminate a player at night (a potion of death).\\n\\nGAME RULE:\\nThe game is consisted of two phases: night phase and day phase. The two phases are repeated until werewolf or villager win the game.\\n1. Night Phase: During the night, the werewolves discuss and vote for a player to eliminate. Special roles also perform their actions at this time (e.g., the Seer chooses a player to learn their role, the witch chooses a decide if save the player).\\n2. Day Phase: During the day, all surviving players discuss who they suspect might be a werewolf. No one reveals their role unless it serves a strategic purpose. After the discussion, a vote is taken, and the player with the most votes is \\"lynched\\" or eliminated from the game.\\n\\nVICTORY CONDITION:\\nFor werewolves, they win the game if the number of werewolves is equal to or greater than the number of remaining villagers.\\nFor villagers, they win if they identify and eliminate all of the werewolves in the group.\\n\\nCONSTRAINTS:\\n1. Your response should be in the first person.\\n2. This is a conversational game. You should response only based on the conversation history and your strategy.\\n\\nYou are playing werewolf in this game.\\n",\n' +
                    '                    "name": "system",\n' +
                    '                    "role": "system"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Player1 and Player2, if you are the only werewolf, eliminate a player. Otherwise, discuss with your teammates and reach an agreement.",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Player2, I suggest we consider eliminating Player3. They seem to be asking a lot of questions which might indicate they are the Seer trying to gather information. What do you think?",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Player1, your suggestion makes sense. It\'s possible Player3 could be the Seer. But we should also consider the possibility that they might just be a regular villager trying to help. What about Player4? They\'ve been rather quiet.",\n' +
                    '                    "name": "Player2",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Player2, I see your point about Player4. However, I still believe Player3 might be a bigger threat. Their questions could be a strategy to identify us. If they are the Seer, it could be dangerous for us. Let\'s vote for Player3.",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Alright, Player1. I agree with you. Let\'s eliminate Player3.",\n' +
                    '                    "name": "Player2",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Player3",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Which player do you vote to kill?",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Player3",\n' +
                    '                    "name": "Player2",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "The player with the most votes is Player3.",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "The day is coming, all the players open your eyes. Last night, the following player(s) has been eliminated: Player3.",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Now the alive players are Player1, Player2, Player4, Player5 and Player6. Given the game rules and your role, based on the situation and the information you gain, to vote a player eliminated among alive players and to win the game, what do you want to say to others? You can decide whether to reveal your role. ",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "I find Player4\'s silence a bit suspicious. Don\'t you think it\'s odd that they haven\'t contributed much to our discussions? Maybe they are trying to avoid drawing attention to themselves. I suggest we vote for Player4.",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "I agree with Player1. Player4\'s silence is indeed suspicious. I also vote for Player4.",\n' +
                    '                    "name": "Player2",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "I understand why my silence might seem suspicious, but I assure you, I am a villager. I was silent because I was trying to observe and gather information. I suggest we should focus on finding the real werewolves. Let\'s think about it, who has been aggressively pointing fingers without concrete evidence?",\n' +
                    '                    "name": "Player4",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "I agree that Player4\'s silence was suspicious, but their defense makes sense. They could\'ve been observing, just like us. We need to be careful about who we accuse and why. Let\'s not rush into conclusions. I suggest we continue observing for now.",\n' +
                    '                    "name": "Player5",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "I agree with Player5. We shouldn\'t rush into conclusions. Let\'s continue observing and gathering information. As for Player4, I think we should give them a chance to prove their innocence.",\n' +
                    '                    "name": "Player6",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Player4",\n' +
                    '                    "name": "Player1",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "Given the game rules and your role, based on the situation and the information you gain, to win the game, it\'s time to vote one player eliminated among the alive players. Which player do you vote to kill?",\n' +
                    '                    "name": "Moderator",\n' +
                    '                    "role": "assistant"\n' +
                    '                },\n' +
                    '                {\n' +
                    '                    "content": "You should respond a json object in a json fenced code block as follows:\\n```json\\n{\\"thought\\": \\"what you thought\\", \\"speak\\": \\"player_name\\"}\\n```",\n' +
                    '                    "name": "system",\n' +
                    '                    "role": "system"\n' +
                    '                }\n' +
                    '            ],\n' +
                    '            "prompt_tokens": 19,\n' +
                    '            "response": {\n' +
                    '                "choices": [\n' +
                    '                    {\n' +
                    '                        "finish_reason": "stop",\n' +
                    '                        "index": 0,\n' +
                    '                        "logprobs": {\n' +
                    '                            "content": []\n' +
                    '                        },\n' +
                    '                        "message": {\n' +
                    '                            "content": "```json\\n{\\"thought\\": \\"I still suspect Player4, but I need to be careful not to draw suspicion to myself. I will go along with the group\'s decision for now to avoid looking suspicious.\\", \\"speak\\": \\"Player4\\"}\\n```",\n' +
                    '                            "role": "assistant"\n' +
                    '                        }\n' +
                    '                    }\n' +
                    '                ],\n' +
                    '                "created": 1715606613,\n' +
                    '                "id": "chatcmpl-9OPwL8pxJmd8vlt7eTsNNxlB3cZ61",\n' +
                    '                "model": "gpt-4",\n' +
                    '                "object": "chat.completion",\n' +
                    '                "system_fingerprint": null,\n' +
                    '                "usage": {\n' +
                    '                    "completion_tokens": 52,\n' +
                    '                    "prompt_tokens": 19,\n' +
                    '                    "total_tokens": 71\n' +
                    '                }\n' +
                    '            },\n' +
                    '            "total_tokens": 71,\n' +
                    '            "username": "225186"\n' +
                    '        },\n' +
                    '        "message": "success"\n' +
                    '    }\n' +
                    '}'
                );
            });
        })
        .catch(error => {
            console.error(error);
        });
}

