# -*- coding: utf-8 -*-
"""
This module implements a GeoGuessr-like game using AgentScope.

It includes classes and functions for managing the game state, interacting with
external APIs (like TripAdvisor), and handling user inputs. The game involves
a gamemaster agent that selects locations and provides hints, and a player
agent that tries to guess the locations based on images and clues.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
import re
import logging

from agentscope.service.service_toolkit import ServiceToolkit
import agentscope
from agentscope.message import Msg
from agentscope.agents import DialogAgent
from agentscope.service import (
    get_tripadvisor_location_photos,
    search_tripadvisor,
    get_tripadvisor_location_details,
)
from agentscope.parsers import ParserBase
from agentscope.models import ModelResponse
import ExtendedDialogAgent

class LocationMatcherParser(ParserBase):
    """
    A parser to match locations in natural language text
    against a predefined list of locations.
    """

    def __init__(self, locations: List[Dict[str, Any]]):
        """
        Initialize the parser with a list of location dictionaries.

        Args:
            locations (list): A list of dictionaries,
                              each containing location information.
        """
        self.locations = locations

    def parse(self, response: ModelResponse) -> ModelResponse:
        """
        Parse the response text to find matches with the predefined locations.

        Args:
            response (ModelResponse): The response object containing
                                      the text to parse.

        Returns:
            ModelResponse: The response object with the parsed result added.
        """
        text = response.text
        matches = []

        for location in self.locations:
            if re.search(
                r"\b" + re.escape(location["name"]) + r"\b",
                text,
                re.IGNORECASE,
            ):
                matches.append(location)

        response.parsed = matches
        return response


agentscope.init(
    # ...
    project="xxx",
    name="xxx",
    studio_url="http://127.0.0.1:5000",  # The URL of AgentScope Studio
)
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                "model_type": "openai_chat",
                "config_name": "gpt-3.5-turbo",
                "model_name": "gpt-3.5-turbo",
                "api_key": "",  # Load from env if not provided
                "generate_args": {
                    "temperature": 0.5,
                },
            },
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
