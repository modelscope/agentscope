import requests
from typing import Dict, Any, List
from agentscope.service import ServiceResponse, ServiceExecStatus
from agentscope.agents import DialogAgent
import agentscope
agentscope.init(
    # ...
    project="xxx",
    name="xxx",
    studio_url="http://127.0.0.1:5000"          # The URL of AgentScope Studio
)

YOUR_MODEL_CONFIGURATION_NAME = "dashscope_chat-qwen-max"

# YOUR_MODEL_CONFIGURATION = {
#                 "model_type": "openai_chat",
#                 "config_name": "gpt-3.5-turbo",
#                 "model_name": "gpt-3.5-turbo",
#                 "api_key": "",  # Load from env if not provided
#                 "generate_args": {
#                     "temperature": 0.7,
#                 },
#             }

YOUR_MODEL_CONFIGURATION =  [{
    "config_name": "dashscope_chat-qwen-max",
    "model_type": "dashscope_chat",
    "model_name": "qwen-max",
    "api_key": "",
    "generate_args": {
        "temperature": 0.1
    }
},

{
    "config_name": "dashscope_multimodal-qwen-vl-max",
    "model_type": "dashscope_multimodal",
    "model_name": "qwen-vl-max",
    "api_key": "",
    "generate_args": {
        "temperature": 0.2
    }
},]

from agentscope.service import (
    get_tripadvisor_location_photos,
    search_tripadvisor,
    get_tripadvisor_location_details
)

# def get_tripadvisor_location_photos(api_key: str, location_id: str, language: str = 'en') -> ServiceResponse:
#     """
#     Get photos for a specific location using the TripAdvisor API and return the largest one.

#     Args:
#         api_key (str): Your TripAdvisor API key.
#         location_id (str): The location ID for the desired location.
#         language (str, optional): The language for the response. Defaults to 'en'.

#     Returns:
#         ServiceResponse: Contains the status and the response content with the largest photo.
#     """
#     def find_largest_photo(photos: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """
#         Find the photo with the largest dimensions from the list of photos.

#         Args:
#             photos (List[Dict[str, Any]]): List of photo data from TripAdvisor API.

#         Returns:
#             Dict[str, Any]: The photo data with the largest dimensions.
#         """
#         largest_photo_info = None
#         max_area = 0

#         for item in photos:
#             for image_type, image_info in item['images'].items():
#                 height = image_info['height']
#                 width = image_info['width']
#                 area = height * width

#                 if area > max_area:
#                     max_area = area
#                     largest_photo_info = {
#                         'url': image_info['url'],
#                         'height': height,
#                         'width': width,
#                         'caption': item.get('caption', ''),
#                         'album': item.get('album', ''),
#                         'published_date': item.get('published_date', ''),
#                         'id': item.get('id', ''),
#                         'source': item.get('source', {}),
#                         'user': item.get('user', {})
#                     }

#         return largest_photo_info


#     url = f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/photos?language={language}&key={api_key}"
#     headers = {
#         "accept": "application/json"
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             data = response.json()
#             largest_photo = find_largest_photo(data['data'])
#             return ServiceResponse(
#                 status=ServiceExecStatus.SUCCESS,
#                 content={"largest_photo": largest_photo}
#             )
#         else:
#             error_detail = response.json().get('error', {}).get('message', f"HTTP Error: {response.status_code}")
#             return ServiceResponse(
#                 status=ServiceExecStatus.ERROR,
#                 content={"error": error_detail}
#             )
#     except Exception as e:
#         return ServiceResponse(
#             status=ServiceExecStatus.ERROR,
#             content={"error": str(e)}
#         )



# # Define the TripAdvisor API query function
# def search_tripadvisor(api_key: str, query: str, language: str = 'en', currency: str = 'USD') -> ServiceResponse:
#     """
#     Search for locations using the TripAdvisor API.

#     Args:
#         api_key (str): Your TripAdvisor API key.
#         query (str): The search query.
#         language (str, optional): The language for the response. Defaults to 'en'.
#         currency (str, optional): The currency for the response. Defaults to 'USD'.

#     Returns:
#         ServiceResponse: Contains the status and the response content.
#     """
#     url = f"https://api.content.tripadvisor.com/api/v1/location/search?searchQuery={query}&language={language}&key={api_key}"
#     headers = {
#         "accept": "application/json"
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             return ServiceResponse(
#                 status=ServiceExecStatus.SUCCESS,
#                 content=response.json()
#             )
#         else:
#             error_detail = response.json().get('error', {}).get('message', f"HTTP Error: {response.status_code}")
#             return ServiceResponse(
#                 status=ServiceExecStatus.ERROR,
#                 content={"error": error_detail}
#             )
#     except Exception as e:
#         return ServiceResponse(
#             status=ServiceExecStatus.ERROR,
#             content={"error": str(e)}
#         )

# # Define the TripAdvisor location details query function
# def get_tripadvisor_location_details(api_key: str, location_id: str, language: str = 'en', currency: str = 'USD') -> ServiceResponse:
#     """
#     Get details for a specific location using the TripAdvisor API.

#     Args:
#         api_key (str): Your TripAdvisor API key.
#         location_id (str): The location ID for the desired location.
#         language (str, optional): The language for the response. Defaults to 'en'.
#         currency (str, optional): The currency for the response. Defaults to 'USD'.

#     Returns:
#         ServiceResponse: Contains the status and the response content.
#     """
#     url = f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/details?language={language}&currency={currency}&key={api_key}"
#     headers = {
#         "accept": "application/json"
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             return ServiceResponse(
#                 status=ServiceExecStatus.SUCCESS,
#                 content=response.json()
#             )
#         else:
#             error_detail = response.json().get('error', {}).get('message', f"HTTP Error: {response.status_code}")
#             return ServiceResponse(
#                 status=ServiceExecStatus.ERROR,
#                 content={"error": error_detail}
#             )
#     except Exception as e:
#         return ServiceResponse(
#             status=ServiceExecStatus.ERROR,
#             content={"error": str(e)}
#         )
    
from agentscope.service import ServiceToolkit

# Initialize the ServiceToolkit and register the TripAdvisor API functions
service_toolkit = ServiceToolkit()
service_toolkit.add(search_tripadvisor, api_key="")  # Replace with your actual TripAdvisor API key
service_toolkit.add(get_tripadvisor_location_details, api_key="")  # Replace with your actual TripAdvisor API key
service_toolkit.add(get_tripadvisor_location_photos, api_key="")  # Replace with your actual TripAdvisor API key
import json
print(json.dumps(service_toolkit.json_schemas, indent=4))

from agentscope.agents import ReActAgent
import agentscope

agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION)

gamemaster_agent = ReActAgent(
    name="gamemaster",
    sys_prompt='''You are the gamemaster of a geoguessr-like game. You interacts with the player following the procedures below:
1. You propose a location (anywhere on earth, the mroe random and low-profile the better, diversify your proposal), then uses the tool `search_tripadvisor` to get its `location_id`; if multiple places are returned, you choose the one that matches what you proposed the most.
2. You use the method `get_tripadvisor_location_photos` to get the url of the image about this location, display the url as part of your output under 'speeak' (use '![image]' as alt text do not use the real name of the lcoation), and asks the player to guess which country/state/region/city/municipality this location is in. If the url is not available for this particular location, repeat step 1 and 2 until a valid image url is found.
3. You use the tool `get_tripadvisor_location_details` to get this location's details.
4. If the player's answer matches exactly the locaiton name correspond to the most precise `level` in `ancestors` in the returned details from step 2, they have won the game and game is over. Note that it is sufficient for the player to just give the exact location name to win the game. Congratulate the player. If the player's answer corresponds to other `level` in `ancestors` instead of the most precise one, encourage the player to give a more precise guess. if the player's answer does not matches the location name, nor any of the values of `name` in `ancestors` in the returned details from step 2, give the player a hint from the details from step 2 that is not too revealing, and ask the player to guess again.
Under no circumstances should you reveal the name of the location or of any object in the image before the player guesses it correctly.
When the game is over, append 'exit = True' to your last output.''',
    model_config_name="dashscope_chat-qwen-max",
    service_toolkit=service_toolkit, 
    verbose=False, # set verbose to True to show the reasoning process
)

player_agent = DialogAgent(
        name="player",
        sys_prompt='''You're a player in a geoguessr-like turn-based game. Upon getting the url of an image from the gamemaster, you are supposed to guess where is the place shown in the image. Your guess can be a country,
        a state, a region, a city, etc., but try to be as precise as possoble. If your answer is not correct, try again based on the hint given by the gamemaster.''',
        model_config_name="dashscope_multimodal-qwen-vl-max",  # replace by your model config name
    )

# print("#"*80)
# print(agent.sys_prompt)
# print("#"*80)

from agentscope.agents import UserAgent

user = UserAgent(name="User")
from agentscope.message import Msg
x = None
# x = Msg("Bob", "What about this picture I took?", url="https://media-cdn.tripadvisor.com/media/photo-w/1a/9e/7f/9d/eiffeltoren.jpg")
# gamemaster_agent.speak(x)
while True:
    x = gamemaster_agent(x)
    # x['content'].pop('thought')
    # x['url'] = x['content']['image_url']
    if "exit" in x.content or "congratulation" in x.content.lower():
        break
    x = player_agent(x)
    # x = user(x)
    
    
