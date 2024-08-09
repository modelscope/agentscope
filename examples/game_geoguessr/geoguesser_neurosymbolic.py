# -*- coding: utf-8 -*-
"""
This module implements the neurosymbolic version of a GeoGuessr-like game
using AgentScope.

It includes classes and functions for managing the game state, interacting with
external APIs (like TripAdvisor), and handling user inputs. The game involves
a gamemaster agent that selects locations and provides hints, and a player
agent that tries to guess the locations based on images and clues.
"""

from ExtendedDialogAgent import ExtendedDialogAgent
import agentscope
from agentscope.message import Msg
from agentscope.agents import DialogAgent
from agentscope.service import (
    get_tripadvisor_location_photos,
    search_tripadvisor,
    get_tripadvisor_location_details,
)
from agentscope.service.service_toolkit import ServiceToolkit


agentscope.init(
    # ...
    project="xxx",
    name="xxx",
    studio_url="http://127.0.0.1:5000",  # The URL of AgentScope Studio
)


# Initialize the ServiceToolkit and register the TripAdvisor API functions
service_toolkit = ServiceToolkit()
service_toolkit.add(
    search_tripadvisor,
    api_key="",
)  # Replace with your actual TripAdvisor API key
service_toolkit.add(
    get_tripadvisor_location_details,
    api_key="",
)  # Replace with your actual TripAdvisor API key
service_toolkit.add(
    get_tripadvisor_location_photos,
    api_key="",
)  # Replace with your actual TripAdvisor API key


# Initialize AgentScope and run
def main() -> None:
    """A GeoGuessr-like game demo"""

    agentscope.init(
        model_configs=[
            {
                "config_name": "dashscope_chat-qwen-max",
                "model_type": "dashscope_chat",
                "model_name": "qwen-max-1201",
                "api_key": "",
                "generate_args": {
                    "temperature": 0.1,
                },
            },
            {
                "config_name": "dashscope_multimodal-qwen-vl-max",
                "model_type": "dashscope_multimodal",
                "model_name": "qwen-vl-max",
                "api_key": "",
                "generate_args": {
                    "temperature": 0.01,
                },
            },
            {
                "config_name": "gpt-4o_config",
                "model_type": "openai_chat",
                "model_name": "gpt-4o",
                "api_key": "",
                "generate_args": {
                    "temperature": 1.5,
                },
            },
        ],
    )

    # Init the dialog agent
    gamemaster_agent = ExtendedDialogAgent(
        name="GeoGuessr Gamemaster",
        sys_prompt="You're a game master for a geography guessing game.",
        model_config_name="gpt-4o_config",
        service_toolkit=service_toolkit,
        use_memory=True,
    )

    player_agent = DialogAgent(
        name="player",
        sys_prompt="""You're a player in a geoguessr-like turn-based game.
        Upon getting an image from the gamemaster, you are supposed to guess
        where is the place shown in the image. Your guess can be a country,
        a state, a region, a city, etc., but try to be as precise as possoble.
        If your answer is not correct, try again based on the hint given
        by the gamemaster.""",
        model_config_name=("dashscope_multimodal-qwen-vl-max"),
        # Replace by your model config name.
        # The model needs to be have vision modality.
    )

    # Start the game
    x = None
    while gamemaster_agent.game_state != "guessing":
        response = gamemaster_agent.handle_input(
            {"text": "Let's start the game"},
        )
        x = Msg(
            "GeoGuessr Gamemaster",
            response[0]["text"],
        )

        gamemaster_agent.speak(x)
        x["url"] = response[1]["image"]

        y = Msg(
            "GeoGuessr Gamemaster",
            "image",
            url=response[2]["image_for_display"],
        )
        gamemaster_agent.speak(y)
        print("Game Master:", response[0]["text"])

    # Main game loop

    while gamemaster_agent.game_state != "end":
        x = player_agent(x)
        if "quit" in x["content"].lower():
            print("Thanks for playing!")
            break
        response = gamemaster_agent.handle_input({"text": x["content"]})
        x = Msg("GeoGuessr Gamemaster", response["text"])
        gamemaster_agent.speak(x)
        print("Game Master:", response["text"])


if __name__ == "__main__":
    main()
