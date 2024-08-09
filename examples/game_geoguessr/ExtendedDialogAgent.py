# -*- coding: utf-8 -*-
"""
This module contains the ExtendedDialogAgent class, which is an extension of
the BaseDialogAgent class for managing a GeoGuessr-like game.

The ExtendedDialogAgent class provides functionality for:
- Managing game states
- Interacting with external APIs for location information
- Handling user inputs and game logic
- Generating location proposals and hints
- Processing and validating user guesses

This module is part of a larger project aimed at creating an interactive
geography guessing game using AI-powered dialogue agents.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import ast
import logging
import re

import requests

from agentscope.service.service_toolkit import ServiceToolkit
from agentscope.service.service_response import ServiceExecStatus
from agentscope.agents.dialog_agent import DialogAgent as BaseDialogAgent


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtendedDialogAgent(BaseDialogAgent):
    """
    An extended dialog agent for managing a GeoGuessr-like game.

    This class extends the BaseDialogAgent to include additional functionality
    specific to the geography guessing game. It manages game states, interacts
    with external APIs for location information, and handles user inputs and
    game logic.

    Attributes:
        service_toolkit (ServiceToolkit): A toolkit for accessing
                                          external services.
        current_location (Optional[Dict[str, Any]]): The current location
                                                     being guessed.
        current_details (Optional[Dict[str, Any]]): Detailed information
                                                    about the current location.
        game_state (str): The current state of the game
                          (e.g., "start", "guessing", "end").

    Methods:
        parse_service_response: Parse the response from service calls.
        propose_location: Generate a proposal for a new location.
        search_and_select_location: Search for and select a location
                                    based on a query.
        get_location_details: Retrieve detailed information about a location.
        get_location_photos: Get photos for a specific location.
        check_guess_location: Check if a user's guess matches the actual
                              location.
        check_guess_ancestors: Check if a user's guess matches any ancestor
                               locations.
        save_image_from_url: Download and save an image from a URL.
        find_largest_photo: Find the largest photo from a list of photos.
        get_hint: Generate a hint about the current location.
        handle_input: Process user input based on the current game state.
        handle_start_state: Handle the initial state of the game.
        handle_guessing_state: Handle the guessing state of the game.
    """

    def __init__(
        self,
        name: str,
        sys_prompt: str,
        model_config_name: str,
        service_toolkit: ServiceToolkit,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
    ):
        super().__init__(
            name,
            sys_prompt,
            model_config_name,
            use_memory,
            memory_config,
        )
        self.service_toolkit = service_toolkit
        self.current_location = None
        self.current_details = None
        self.game_state = "start"

    def parse_service_response(self, response: str) -> dict:
        """
        Parse the service response string and extract the JSON content.
        Args:
            response (str): The response string from the service call.
        Returns:
            dict: The parsed JSON content.
        """
        result = {}
        lines = response.split("\n")
        for line in lines:
            if "[STATUS]:" in line:
                status = line.split("[STATUS]:")[-1].strip()
                result["status"] = (
                    ServiceExecStatus.SUCCESS
                    if status == "SUCCESS"
                    else ServiceExecStatus.ERROR
                )
            if "[RESULT]:" in line:
                json_str = line.split("[RESULT]:")[-1].strip()
                result["content"] = ast.literal_eval(json_str)
        return result

    def propose_location(self) -> str:
        """
        Propose an interesting location for the player to guess.

        This method uses the model to generate a proposal for an interesting
        location that the player will try to guess. It aims to diversify the
        proposals and include less known locations.

        Returns:
            str: The proposed location as a string.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a game master for a geography guessing game. "
                    "Propose an interesting location for the player to guess. "
                    "Diversify your proposal and give less known ones."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Propose an interesting location for the player to guess. "
                    "Only output your final proposed location."
                ),
            },
        ]
        response = self.model(messages).text.strip()
        return response

    def search_and_select_location(
        self,
        proposed_location: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a location using TripAdvisor API and
        select the most appropriate result.

        This method searches for a location using the
        provided query, then either automatically selects
        the first result or asks the model to choose the best
        match if multiple results are returned.

        Args:
            proposed_location (str): The location to search for.

        Returns:
            dict: The selected location information,
                  or None if no location is found.
        """
        response_str = self.service_toolkit.parse_and_call_func(
            [
                {
                    "name": "search_tripadvisor",
                    "arguments": {"query": proposed_location},
                },
            ],
        )
        result = self.parse_service_response(response_str)
        if (
            result["status"] == ServiceExecStatus.SUCCESS
            and result["content"]["data"]
        ):
            locations = result["content"]["data"]
            if len(locations) > 1:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are selecting the most appropriate location"
                            " from a list of search results."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Select the location that best matches"
                            f" '{proposed_location}' from this list:\n"
                            + "\n".join(
                                [
                                    f"{i+1}. {loc['name']}, "
                                    f"{loc.get('address_obj', {}).get('city', 'Unknown City')}, "  # noqa: E501 # pylint: disable=line-too-long
                                    f"{loc.get('address_obj',{}).get('country','Unknown Country')}"  # noqa: E501 # pylint: disable=line-too-long
                                    for i, loc in enumerate(locations)
                                ],
                            )
                            + "\nRespond with only the number"
                            " of your selection."
                        ),
                    },
                ]
                selection_response = self.model(messages).text.strip()
                try:
                    # Try to extract the number from the response
                    selection = (
                        int("".join(filter(str.isdigit, selection_response)))
                        - 1
                    )
                    if 0 <= selection < len(locations):
                        return locations[selection]
                    else:
                        # If the extracted number is out of range,
                        # return the first location
                        return locations[0]
                except ValueError:
                    # If no number can be extracted, return the first location
                    return locations[0]
            else:
                return locations[0]
        return None

    def get_location_details(self, location_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific
        location using its ID.

        This method calls the TripAdvisor API to get
        detailed information about a location,
        including its description, address, rating,
        and other relevant data.

        Args:
            location_id (str): The unique identifier of the
                               location in TripAdvisor's system.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed
                            response from the API call, including
                            the location details if the call was successful.
        """
        response_str = self.service_toolkit.parse_and_call_func(
            [
                {
                    "name": "get_tripadvisor_location_details",
                    "arguments": {"location_id": location_id},
                },
            ],
        )
        return self.parse_service_response(response_str)

    def get_location_photos(
        self,
        location_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the largest photo for a specific location.

        Args:
            location_id (str): The location ID to get photos for.

        Returns:
            dict: The largest photo information including the URL.
        """
        logger.info(
            "Calling TripAdvisor API for location photos: %s",
            location_id,
        )

        response_str = self.service_toolkit.parse_and_call_func(
            [
                {
                    "name": "get_tripadvisor_location_photos",
                    "arguments": {"location_id": location_id},
                },
            ],
        )
        logger.info("TripAdvisor location photos result: %s", response_str)
        result = self.parse_service_response(response_str)
        largest_photo = self.find_largest_photo(result["content"]["data"])
        return (
            largest_photo
            if result["status"] == ServiceExecStatus.SUCCESS
            else None
        )

    def check_guess_location(self, user_guess: str, location: str) -> str:
        """
        Check if the user's guess matches the actual location.

        This method uses the model to determine if the user's guess
        refers to the same place as the actual location.

        Args:
            user_guess (str): The location guessed by the user.
            location (str): The actual location to compare against.

        Returns:
            str: 'True' if the guess matches the location, 'False' otherwise.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the gamemaster of a geoguessr game."
                    " Check if the player's guess: "
                    + str(user_guess)
                    + " means the same place/location as "
                    + str(location)
                    + ". If yes, return 'True'. Else, return 'False'."
                    " Only output one of the two "
                    "options given and nothing else."
                ),
            },
            {"role": "user", "content": user_guess},
        ]

        response = self.model(messages).text.strip()
        logger.info("check_guess: %s", response)
        return response

    def check_guess_ancestors(
        self,
        user_guess: str,
        ancestors: List[Dict[str, Any]],
    ) -> Tuple[str, str, str]:
        """
        Check if the user's guess matches any of the location's ancestors.

        This method compares the user's guess against a list of ancestor
        locations, determining if there's a match and identifying the
        most specific (smallest level) correct guess.

        Args:
            user_guess (str): The user's guess for the location.
            ancestors (List[Dict[str, Any]]): A list of dictionaries containing
                                            information about ancestor
                                            locations.

        Returns:
            Tuple[str, str, str]: A tuple containing:
                - The level of the matched location (or "None" if no match)
                - The name of the matched location (or "None" if no match)
                - "True" if the match is the most specific, "False" otherwise
        """
        matches = []

        for location in ancestors:
            if re.search(
                r"\b" + re.escape(location["name"]) + r"\b",
                user_guess,
                re.IGNORECASE,
            ):
                matches.append(location)
        if not matches:
            return "None", "None", "False"
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Check if "
                        + str(matches)
                        + " include the smallest level in "
                        + str(ancestors)
                        + " based on their respective levels. If yes,"
                        " return the smallest matched name and the "
                        "corresponding level as 'level,name,True'. "
                        "Else, return 'False'. Note that the placeholders "
                        "'level', 'name' in the output are to be replaced"
                        " by the actual values. Only output one "
                        "of the two options given and nothing else."
                    ),
                },
                {"role": "user", "content": user_guess},
            ]

            response = self.model(messages).text.strip()
            if "True" in response:
                logger.info("check_guess: %s", response)
                response = response.split(",")
                return response[0], response[1], response[2]
            else:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Return the smallest name based on their"
                            " respective 'level' values and the "
                            "corresponding 'level' values in "
                            + str(matches)
                            + " as 'level,name,False'. Note that the "
                            "placeholders 'level', 'name' in the output are"
                            " to be replaced by the actual values. "
                            "Only output in the given format and nothing else."
                        ),
                    },
                    {"role": "user", "content": user_guess},
                ]
                response = self.model(messages).text.strip()
                logger.info("check_guess: %s", response)
                response = response.split(",")
                return response[0], response[1], response[2]

    def save_image_from_url(self, url: str, save_path: str) -> Optional[str]:
        """
        Download and save an image from a given URL to a specified path.

        This method sends a GET request to the provided URL, downloads the
        image, and saves it to the specified path. If successful, it returns
        the full path where the image was saved. If an error occurs during
        the process, it returns None.

        Args:
            url (str): The URL of the image to download.
            save_path (str): The directory path where the image
                             should be saved.

        Returns:
            Optional[str]: The full path where the image was saved
                           if successful, or None if an error occurred.
        """
        try:
            os.makedirs(save_path, exist_ok=True)
            # Send a HTTP request to the URL
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Check if the request was successful

            # Get the file name from the URL
            file_name = os.path.basename(url)
            file_name = "image" + os.path.splitext(file_name)[1]
            # Full path to save the image
            full_path = os.path.join(save_path, file_name)

            # Open a local file with write-binary mode
            with open(full_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            print(f"Image saved successfully at {full_path}")
            return full_path
        except Exception as e:
            print(f"An error occurred: {e}")
            return None  # Return None in case of an error

    def find_largest_photo(
        self,
        photos: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Find the photo with the largest
        dimensions from the list of photos."""
        largest_photo_info = {}
        max_area = 0

        for item in photos:
            for image_info in item["images"].values():
                height = image_info["height"]
                width = image_info["width"]
                area = height * width

                if area > max_area:
                    max_area = area
                    largest_photo_info = {
                        "url": image_info["url"],
                        "height": height,
                        "width": width,
                        "caption": item.get("caption", ""),
                        "album": item.get("album", ""),
                        "published_date": item.get("published_date", ""),
                        "id": item.get("id", ""),
                        "source": item.get("source", {}),
                        "user": item.get("user", {}),
                    }

        return largest_photo_info

    def get_hint(self, details: Dict[str, Any]) -> str:
        """
        Generate a hint about the location based on the provided details.

        This method uses the model to create a hint that gives the user some
        information about the location without making it too obvious.

        Args:
            details (Dict[str, Any]): A dictionary containing details
                                      about the location.

        Returns:
            str: A hint about the location.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You're a game master for a geography guessing game."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"give the user some hint about the location"
                    f" based on the info from {details}. "
                    "Don't make it too obvious."
                ),
            },
        ]
        response = self.model(messages).text.strip()
        logger.info("check_guess: %s", response)
        return response

    def handle_input(self, user_input: dict) -> dict:
        """
        Handle user input based on the current game state.

        This method processes the user's input and returns an appropriate
        response based on the current state of the game (start, guessing,
        or other).

        Args:
            user_input (dict): A dictionary containing the user's input.
                            It should have a 'text' key with the user's
                            message.

        Returns:
            dict: A dictionary containing the response to the user's input.
                The response format depends on the current game state.
        """
        query = user_input["text"]
        response = {}

        if self.game_state == "start":
            response = self.handle_start_state()
        elif self.game_state == "guessing":
            response = self.handle_guessing_state(query)
        else:
            response = {
                "text": (
                    "I'm sorry, I don't understand. " "Let's start a new game!"
                ),
            }

        return response

    def handle_start_state(
        self,
    ) -> Union[Dict[str, str], List[Dict[str, Union[str, Optional[str]]]]]:
        """
        Handle the start state of the game.

        This method is responsible for initializing the game by
        selecting a location, retrieving its details and photos,
        and preparing the initial response to the player.

        Returns:
            Union[Dict[str, str], List[Dict[str, Union[str, Optional[str]]]]]:
            A dictionary with a text response if there's an error, or a list
            containing dictionaries with text response, image path, and
            image URL for display.
        """
        photos: Any = None
        while not photos:
            proposed_location = self.propose_location()
            self.current_location = self.search_and_select_location(
                proposed_location,
            )
            print("self.current_location: ", self.current_location)

            if not self.current_location:
                raise ValueError(
                    "Make sure the correct API keys are provided.",
                )

            self.current_details = self.get_location_details(
                self.current_location["location_id"],
            )
            if self.current_details["status"] != ServiceExecStatus.SUCCESS:
                return {
                    "text": (
                        "I'm having trouble getting details for this location."
                        " Let's try again."
                    ),
                }

            ancestors = self.current_details["content"].get("ancestors", [])
            print("ancestors: ", ancestors)

            photos = self.get_location_photos(
                self.current_location["location_id"],
            )

        response = (
            "Let's play a geography guessing game! I've chosen a location"
            " and displayed an image of it. Can you guess which country, "
            "state, region, city, or municipality this location is in?"
        )
        self.game_state = "guessing"
        if isinstance(photos, dict) and isinstance(photos.get("url"), str):
            image_path = self.save_image_from_url(
                photos["url"],
                save_path="./images",
            )
            return [
                {"text": response},
                {"image": image_path},
                {"image_for_display": photos["url"]},
            ]
        else:
            return {"text": response}

    def handle_guessing_state(self, query: str) -> Dict[str, str]:
        """
        Handle the guessing state of the game.

        This method processes the user's guess, checks if it's correct,
        and provides appropriate feedback or hints.

        Args:
            query (str): The user's guess.

        Returns:
            Dict[str, str]: A dictionary containing the response text.
        """
        if self.current_location is None:
            return {
                "text": (
                    "I'm sorry, there seems to be an issue"
                    " with the current location. Let's start a new game."
                ),
            }

        if (
            self.check_guess_location(
                query.lower(),
                self.current_location["name"].lower(),
            )
            == "True"
        ):
            self.game_state = "end"
            return {
                "text": (
                    f"Congratulations! You've guessed correctly. The location"
                    f" is indeed in {self.current_location['name']}."
                ),
            }

        if (
            self.current_details is None
            or "content" not in self.current_details
        ):
            return {
                "text": (
                    "I'm sorry, there seems to be an issue"
                    " with the location details. Let's start a new game."
                ),
            }

        ancestors = self.current_details["content"].get("ancestors", [])
        level, correct_name, is_smallest = self.check_guess_ancestors(
            query,
            ancestors,
        )

        if level != "None":
            if is_smallest == "True":
                self.game_state = "end"
                return {
                    "text": (
                        f"Congratulations! You've guessed correctly. "
                        f"The location is indeed in {level}: {correct_name}."
                    ),
                }
            else:
                return {
                    "text": f"Good guess! {level}: {correct_name}"
                    f" is correct, but can you be more specific? "
                    f"Try guessing a smaller region or city.",
                }
        else:
            hint = self.get_hint(self.current_details["content"])
            return {
                "text": (
                    f"I'm sorry, that's not correct. Here's a hint: {hint} "
                    "Try guessing again!"
                ),
            }
