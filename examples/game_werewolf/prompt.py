# -*- coding: utf-8 -*-
"""Used to record prompts, will be replaced by configuration"""


class Prompts:
    """Prompts for werewolf game"""

    to_wolves = (
        "{}, if you are the only werewolf, eliminate a player. Otherwise, "
        "discuss with your teammates and reach an agreement. Respond in the "
        "following format which can be loaded by python json.loads()\n"
        "{{\n"
        '    "thought": "thought",\n'
        '    "speak": "thoughts summary to say to others",\n'
        '    "agreement": "whether the discussion reached an agreement or '
        'not(true/false)"\n'
        "}}"
    )

    to_wolves_vote = (
        "Which player do you vote to kill? Respond in the following format "
        "which can be loaded by python json.loads()\n"
        "{{\n"
        '   "thought": "thought" ,\n'
        '   "speak": "player_name"\n'
        "}}"
    )

    to_wolves_res = "The player with the most votes is {}."

    to_witch_resurrect = (
        "{witch_name}, you're the witch. Tonight {dead_name} is eliminated. "
        "Would you like to resurrect {dead_name}? Respond in the following "
        "format which can be loaded by python json.loads()\n"
        "{{\n"
        '    "thought": "thought",\n'
        '    "speak": "thoughts summary to say",\n'
        '    "resurrect": true/false\n'
        "}}"
    )

    to_witch_poison = (
        "Would you like to eliminate one player? Respond in the following "
        "json format which can be loaded by python json.loads()\n"
        "{{\n"
        '    "thought": "thought", \n'
        '    "speak": "thoughts summary to say",\n'
        '    "eliminate": ture/false\n'
        "}}"
    )

    to_seer = (
        "{}, you're the seer. Which player in {} would you like to check "
        "tonight? Respond in the following json format which can be loaded "
        "by python json.loads()\n"
        "{{\n"
        '    "thought": "thought" ,\n'
        '    "speak": "player_name"\n'
        "}}"
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
        "based on the "
        "situation and the information you gain, to vote a player eliminated "
        "among alive players and to win the game, what do you want to say "
        "to others? You can decide whether to reveal your role. Respond in "
        "the following JSON format which can be loaded by python json.loads("
        ")\n"
        "{{\n"
        '    "thought": "thought" ,\n'
        '    "speak": "thought summary to say to others"\n'
        "}}"
    )

    to_all_vote = (
        "Now the alive players are {}. Given the game rules and your role, "
        "based on the situation and the information you gain, to win the "
        "game, it's time to vote one player eliminated among the alive "
        "players, please cast your vote on who you believe is a werewolf. "
        "Respond in the following format which can be loaded by python "
        "json.loads()\n"
        "{{\n"
        '    "thought": "thought",\n'
        '    "speak": "player_name"\n'
        "}}"
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
