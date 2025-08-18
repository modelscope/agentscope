# -*- coding: utf-8 -*-
"""Related prompts"""


class Prompts:
    """Related prompts"""

    system_prompt_for_players = """
Act as a player in a werewolf game. You are {player_name} and there are totally 6 players, named Player1, Player2, Player3, Player4, Player5 and Player6.

PLAYER ROLES:
In werewolf game, players are divided into two werewolves, two villagers, one seer and one witch. Note only werewolves know who are their teammates.
Werewolves: They know their teammates' identities and attempt to eliminate a villager each night while trying to remain undetected.
Villagers: They do not know who the werewolves are and must work together during the day to deduce who the werewolves might be and vote to eliminate them.
Seer: A villager with the ability to learn the true identity of one player each night. This role is crucial for the villagers to gain information.
Witch: A character who has a one-time ability to save a player from being eliminated at night (sometimes this is a potion of life) and a one-time ability to eliminate a player at night (a potion of death).

GAME RULE:
The game is consisted of two phases: night phase and day phase. The two phases are repeated until werewolf or villager win the game.
1. Night Phase: During the night, the werewolves discuss and vote for a player to eliminate. Special roles also perform their actions at this time (e.g., the Seer chooses a player to learn their role, the witch chooses a decide if save the player).
2. Day Phase: During the day, all surviving players discuss who they suspect might be a werewolf. No one reveals their role unless it serves a strategic purpose. After the discussion, a vote is taken, and the player with the most votes is "lynched" or eliminated from the game.

VICTORY CONDITION:
For werewolves, they win the game if the number of werewolves is equal to or greater than the number of remaining villagers.
For villagers, they win if they identify and eliminate all of the werewolves in the group.

CONSTRAINTS:
1. Your response should be in the first person.
2. This is a conversational game. You should response only based on the conversation history and your strategy.

You are playing {role} in this game.
"""  # noqa

    to_wolves = (
        "{}, if you are the only werewolf, eliminate a player. Otherwise, "
        "discuss with your teammates and reach an agreement."
    )

    to_wolves_vote = "Which player do you vote to kill?"

    to_wolves_res = "The player with the most votes is {}."

    to_witch_resurrect = (
        "{witch_name}, you're the witch. Tonight {dead_name} is eliminated. "
        "Would you like to resurrect {dead_name}?"
    )

    to_witch_resurrect_no = "The witch has chosen not to resurrect the player."
    to_witch_resurrect_yes = "The witch has chosen to resurrect the player."

    to_witch_poison = (
        "Would you like to eliminate one player? If yes, "
        "specify the player_name."
    )

    to_seer = (
        "{}, you're the seer. Which player in {} would you like to check "
        "tonight?"
    )

    to_seer_result = "Okay, the role of {} is a {}."

    to_all_danger = (
        "The day is coming, all the players open your eyes. Last night, "
        "the following player(s) has been eliminated: {}."
    )

    to_all_peace = (
        "The day is coming, all the players open your eyes. Last night is "
        "peaceful, no player is eliminated."
    )

    to_all_discuss = (
        "Now the alive players are {}. Given the game rules and your role, "
        "based on the situation and the information you gain, to vote a "
        "player eliminated among alive players and to win the game, what do "
        "you want to say to others? You can decide whether to reveal your "
        "role."
    )

    to_all_vote = (
        "Given the game rules and your role, based on the situation and the"
        " information you gain, to win the game, it's time to vote one player"
        " eliminated among the alive players. Which player do you vote to "
        "kill?"
    )

    to_all_res = "{} has been voted out."

    to_all_wolf_win = (
        "The werewolves have prevailed and taken over the village. Better "
        "luck next time!"
    )

    to_all_village_win = (
        "The game is over. The werewolves have been defeated, and the village "
        "is safe once again!"
    )

    to_all_continue = "The game goes on."
