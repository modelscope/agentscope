# -*- coding: utf-8 -*-
"""
This module implements the generative version of a Geoguessr-like game using
the AgentScope framework.
"""
import os
import json
from typing import List
import requests
from agentscope.service import ServiceResponse, ServiceExecStatus
from agentscope.service import ServiceToolkit
from agentscope.agents import DialogAgent
import agentscope
from agentscope.message import Msg
from agentscope.agents import ReActAgent
from agentscope.service import (
    get_tripadvisor_location_photos,
    search_tripadvisor,
    get_tripadvisor_location_details,
)

agentscope.init(
    # ...
    project="xxx",
    name="xxx",
    studio_url="http://127.0.0.1:5000",  # The URL of AgentScope Studio
)

YOUR_MODEL_CONFIGURATION_NAME = "dashscope_chat-qwen-max"


YOUR_MODEL_CONFIGURATION = [
    {
        "config_name": "dashscope_chat-qwen-max",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
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
            "temperature": 0.2,
        },
    },
    {
        "model_type": "openai_chat",
        "config_name": "gpt",
        "model_name": "gpt-4o",
        "api_key": "",  # Load from env if not provided
        "generate_args": {
            "temperature": 0.7,
        },
    },
]


def search_files_with_keywords(
    directory: str,
    keywords: List[str],
) -> List[str]:
    """
    Search for filenames containing certain keywords within a given directory.

    Args:
        directory (`str`):
            The directory to search in.
        keywords (`List[str]`):
            A list of keywords to search for in filenames.

    Returns:
        `List[str]`: A list of filenames containing any of the keywords.

    Example:
        .. code-block:: python

            result = search_files_with_keywords(
                "./my_directory", ["example", "test"]
            )
            print("Files found:", result)
    """
    matching_files = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if any(keyword in file for keyword in keywords):
                    matching_files.append(os.path.join(root, file))

        return matching_files
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def save_image_from_url(
    url: str,
) -> ServiceResponse:
    """
    Save an image from a URL to a specified local path.

    Args:
        url (`str`):
            The URL of the image to be downloaded.
    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is either the full path where the image has been saved
        or error information, which depends on the `status` variable.

    Example:
        .. code-block:: python

            result = save_image_from_url("http://example.com/image.jpg")
            if result.status == ServiceExecStatus.SUCCESS:
                print(f"Image saved at {result.content['path']}")
            else:
                print(f"Error: {result.content['error']}")
    """
    try:
        save_path = "./images"
        os.makedirs(save_path, exist_ok=True)
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check if the request was successful

        file_name = os.path.basename(url)
        file_name = "image" + os.path.splitext(file_name)[1]
        full_path = os.path.join(save_path, file_name)

        with open(full_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        # Save the URL to a .txt file
        url_txt_path = os.path.join(save_path, "url.txt")
        with open(url_txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(url)

        print(f"Image saved successfully at {full_path}")
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content={"path": full_path},
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
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
service_toolkit.add(
    save_image_from_url,
)  # Replace with your actual TripAdvisor API key


print(json.dumps(service_toolkit.json_schemas, indent=4))


agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION)

gamemaster_agent = ReActAgent(
    name="gamemaster",
    sys_prompt="""You are the gamemaster of a geoguessr-like game.
        You interacts with the player following the procedures below:
        1. You propose a location (anywhere on earth, the mroe random
        and low-profile the better, diversify your proposal), then
        uses the tool `search_tripadvisor` to get its `location_id`;
        if multiple places are returned, you choose the one that matches
        what you proposed the most.
        2. You use the method `get_tripadvisor_location_photos` to get
        the url of the image about this location, save the image with
        the method `save_image_from_url` (do not tell the url directly
        to the player; the player will be able to see the saved image),
        and asks the player to guess which
        country/state/region/city/municipality this location is in.
        If the url is not available for this particular location,
        repeat step 1 and 2 until a valid image url is found.
        3. You use the tool `get_tripadvisor_location_details`
        to get this location's details.
        4. If the player's answer matches exactly the locaiton name
        correspond to the most precise `level` in `ancestors` in the
        returned details from step 2, they have won the game and game is over.
        Note that it is sufficient for the player to just give the exact
        location name to win the game. Congratulate the player. If the
        player's answer corresponds to other `level` in `ancestors` instead
        of the most precise one, encourage the player to give a
        more precise guess. if the player's answer does not
        matches the location name, nor any of the values of
        `name` in `ancestors` in the returned details from step 2,
        give the player a hint from the details from step 2
        that is not too revealing, and ask the player to guess again.
        Under no circumstances should you reveal the name of the
        location or of any object in the image before
        the player guesses it correctly. When the game is over,
        append 'exit = True' to your last output.""",
    model_config_name="gpt",
    service_toolkit=service_toolkit,
    verbose=False,  # set verbose to True to show the reasoning process
)

player_agent = DialogAgent(
    name="player",
    sys_prompt="""You're a player in a geoguessr-like turn-based game.
        Upon getting the url of an image from the gamemaster, you are
        supposed to guess where is the place shown in the image. Your
        guess can be a country, a state, a region, a city, etc., but try
        to be as precise as possoble. If your answer is not correct,
        try again based on the hint given by the gamemaster.""",
    # replace by your model config name
    model_config_name="dashscope_multimodal-qwen-vl-max",
)


x = None
image_display_flag = 0
while True:
    x = gamemaster_agent(x)

    if "exit" in x.content or "congratulation" in x.content.lower():
        break
    if image_display_flag == 0:
        images_path = search_files_with_keywords("./images", ["image"])
        x["url"] = images_path[0]
        try:
            with open("./images/url.txt", "r", encoding="utf-8") as f:
                image_url = f.read().strip()
            image_display_flag = 1
        except Exception as error:
            print(f"An error occurred while reading the file: {error}")
        y = Msg("system", "Image:", url=image_url)
        gamemaster_agent.speak(y)
    x = player_agent(x)
