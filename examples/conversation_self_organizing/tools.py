# -*- coding: utf-8 -*-
"""some utils of angent_builder example"""
import re


def load_txt(instruction_file: str) -> str:
    """
    load .txt file
    Arguments:
        instruction_file: str type, which is the .txt file pth

    Returns:
        instruction: str type, which is the str in the instruction_file

    """
    with open(instruction_file, "r", encoding="utf-8") as f:
        instruction = f.read()
    return instruction


# extract scenario和participants
def extract_scenario_and_participants(content: str) -> dict:
    """
    extract the scenario and participants from agent builder's response

    Arguments:
        content: the agent builders response

    Returns:
        result: dict

    Examples:
        content: #scenario#: Astronomy club meeting
    #participants#:
    * Club Leader: Act as the club leader who is knowledgeable about\
     astronomy and optics. You are leading a discussion about the \
     capabilities of telescopes versus the human eye. Please provide \
     accurate information and guide the discussion.
    * Curious Member: Act as a curious club member who is interested \
    in astronomy but may not know all the technical details. You are \
    eager to learn and ask questions.
    * Experienced Astronomer: Act as an experienced astronomer who has \
    practical experience using telescopes for stargazing. You can \
    provide real-world examples and insights into the topic.

    Return:
        {'Scenario': 'Astronomy club meeting',
        'Participants':
        {'Club_Leader': 'Act as the club leader who is knowledgeable \
        about astronomy and optics. You are leading a discussion about the  \
        capabilities of telescopes versus the human eye. Please provide\
        accurate information and guide the discussion.',
        'Curious_Member': 'Act as a curious club member who is interested \
        in astronomy but may not know all the technical details. You are \
        eager to learn and ask questions.',
        'Experienced_Astronomer': 'Act as an experienced astronomer who has\
        practical experience using telescopes for stargazing. You can\
        provide real-world examples and insights into the topic.'}}

    """
    result = {}
    # define regular expression
    scenario_pattern = r"#scenario#:\s*(.*)"
    participants_pattern = r"\*\s*([^:\n]+):\s*([^\n]+)"

    # search and extract scenario
    scenario_match = re.search(scenario_pattern, content)
    if scenario_match:
        result["Scenario"] = scenario_match.group(1).strip()

    # search and extract participants
    participants_matches = re.finditer(participants_pattern, content)
    participants_dict = {}
    for match in participants_matches:
        participant_type, characteristic = match.groups()
        participants_dict[
            participant_type.strip().replace(" ", "_")
        ] = characteristic.strip()
    result["Participants"] = participants_dict

    return result
