# -*- coding: utf-8 -*-
import requests
from typing import Dict, Any, List
from agentscope.service import ServiceResponse, ServiceExecStatus
from agentscope.agents import DialogAgent
import agentscope
import os

agentscope.init(
    # ...
    project="xxx",
    name="xxx",
    studio_url="http://127.0.0.1:5000",  # The URL of AgentScope Studio
)

# set env
os.environ["ANTHROPIC_API_KEY"] = ""

from PIL import Image
import os
import base64
from litellm import completion


def encode_image(image_path):
    # Determine new path for converted image if necessary
    new_image_path = image_path
    with Image.open(image_path) as img:
        # Convert to JPEG if not already
        if img.format != "JPEG":
            img = img.convert("RGB")
            new_image_path = image_path.rsplit(".", 1)[0] + ".jpeg"
            img.save(new_image_path, format="JPEG")

        # Resize if necessary
        max_size = (1024, 1024)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size)
            img.save(new_image_path, format="JPEG")

    # Encode image to base64
    with open(new_image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Path to your image
import os

current_path = os.getcwd()
image_path = "/Users/zhangzeyu/Documents/agentscope/examples/neurosymbolic_QA/nash_equilibrium.webp"
# Get the base64 string of the image
base64_image = encode_image(image_path)

YOUR_MODEL_CONFIGURATION = [
    {
        "config_name": "lite_llm_claude",
        "model_type": "litellm_chat",
        # "model_name": "claude-3-opus-20240229",
        "model_name": "claude-3-5-sonnet-20240620",
        "generate_args": {
            "temperature": 0.1,
        },
    },
]

from agentscope.service import (
    query_wolfram_alpha_short_answers,
    query_wolfram_alpha_simple,
    query_wolfram_alpha_show_steps,
    query_wolfram_alpha_llm,
)


from agentscope.service import ServiceToolkit

# Initialize the ServiceToolkit and register the TripAdvisor API functions
service_toolkit = ServiceToolkit()
service_toolkit.add(
    query_wolfram_alpha_short_answers, api_key=""
)  # Replace with your actual TripAdvisor API key
service_toolkit.add(
    query_wolfram_alpha_simple, api_key=""
)  # Replace with your actual TripAdvisor API key
service_toolkit.add(
    query_wolfram_alpha_show_steps, api_key=""
)  # Replace with your actual TripAdvisor API key
service_toolkit.add(
    query_wolfram_alpha_llm, api_key=""
)  # Replace with your actual TripAdvisor API key
service_toolkit2 = ServiceToolkit()

import json

print(json.dumps(service_toolkit.json_schemas, indent=4))

from agentscope.agents import ReActAgent
import agentscope

agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION)

student_agent1 = ReActAgent(
    name="Student1",
    sys_prompt="""You are a smart student. You are given problem to solve. Use the approprite wolfram alpha APIs to help you solve simultaneous equations/calculations. Note that wolfram alpha apis can only help you solve an explicitly given equation or calculation. Don't use them if you are not solving equations or doing calculations.""",
    model_config_name="lite_llm_claude",
    service_toolkit=service_toolkit,
    verbose=True,  # set verbose to True to show the reasoning process
)


student_agent2 = ReActAgent(
    name="Student2",
    sys_prompt="""You are a smart student. You are given problem to solve.""",
    model_config_name="dashscope_multimodal-qwen-vl-max",
    service_toolkit=service_toolkit2,
    verbose=False,  # set verbose to True to show the reasoning process
)



from agentscope.agents import UserAgent

user = UserAgent(name="User")
from agentscope.message import Msg


x = Msg(
    "system",
    """Solve the problem: For the following games, compute all mixed Nash equilibria. In each table cell, the number on the left is the payoff to the row player, and the number on the right is the payoff to the column player.
        |   | L   | R   |
        |---|-----|-----|
        | T | 7,1 | 2,2 |
        | B | 0,5 | 3,1 |
        You need to formulate the relevant equations and ask it to solve it for you.""",
)
# Note that you cannot simply ask wolfrm aplha api to find the equilibra for you. You need to formulate the relevant equations and ask it to solve it for you.''')
student_agent1.speak(x)
for i in range(5):
    x = student_agent1(x)

