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
    studio_url="http://127.0.0.1:5000"          # The URL of AgentScope Studio
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
        if img.format != 'JPEG':
            img = img.convert('RGB')
            new_image_path = image_path.rsplit('.', 1)[0] + '.jpeg'
            img.save(new_image_path, format='JPEG')
        
        # Resize if necessary
        max_size = (1024, 1024)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size)
            img.save(new_image_path, format='JPEG')
    
    # Encode image to base64
    with open(new_image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Path to your image
image_path = "/Users/zhangzeyu/Documents/agentscope/examples/neurosymbolic_QA/nash_equilibrium.webp"
# Get the base64 string of the image
base64_image = encode_image(image_path)

YOUR_MODEL_CONFIGURATION =  [{
    "config_name": "dashscope_chat-qwen-max",
    "model_type": "dashscope_chat",
    "model_name": "qwen-max-1201",
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
        "temperature": 0
    }
},

{
                "model_type": "openai_chat",
                "config_name": "gpt",
                "model_name": "gpt-4o",
                "api_key": "",  # Load from env if not provided
                "generate_args": {
                    "temperature": 0.2,
                },
            },
            {
    "config_name": "gemini_chat-gemini-pro",
    "model_type": "gemini_chat",
    "model_name": "gemini-1.5-pro",
    "api_key": ""
},
{
    "config_name": "lite_llm_claude",
    "model_type": "litellm_chat",
    # "model_name": "claude-3-opus-20240229",
    "model_name": "claude-3-5-sonnet-20240620",
    "generate_args": {
        # "max_tokens": 4096,
                    "temperature": 0.1,
                },
}
            
            ]

from agentscope.service import (
    query_wolfram_alpha_short_answers,
    query_wolfram_alpha_simple,
    query_wolfram_alpha_show_steps,
    query_wolfram_alpha_llm
)

    
from agentscope.service import ServiceToolkit

# Initialize the ServiceToolkit and register the TripAdvisor API functions
service_toolkit = ServiceToolkit()
service_toolkit.add(query_wolfram_alpha_short_answers, api_key="")  # Replace with your actual TripAdvisor API key
service_toolkit.add(query_wolfram_alpha_simple, api_key="")  # Replace with your actual TripAdvisor API key
service_toolkit.add(query_wolfram_alpha_show_steps, api_key="")  # Replace with your actual TripAdvisor API key
service_toolkit.add(query_wolfram_alpha_llm, api_key="")  # Replace with your actual TripAdvisor API key
service_toolkit2 = ServiceToolkit()

import json
print(json.dumps(service_toolkit.json_schemas, indent=4))

from agentscope.agents import ReActAgent
import agentscope

agentscope.init(model_configs=YOUR_MODEL_CONFIGURATION)

student_agent1 = ReActAgent(
    name="Student1",
    sys_prompt='''You are a smart student. You are given problem to solve. Use the approprite wolfram alpha APIs to help you solve simultaneous equations/calculations. Note that wolfram alpha apis can only help you solve an explicitly given equation or calculation. Don't use them if you are not solving equations or doing calculations.''',
    model_config_name="lite_llm_claude",
    service_toolkit=service_toolkit, 
    verbose=True, # set verbose to True to show the reasoning process
)

# student_agent1 = ReActAgent(
#     name="Student1",
#     sys_prompt='''You are a smart student. You are given problem to solve. Give the problem to wolfram alpha APIs to solve.''',
#     model_config_name="gpt",
#     service_toolkit=service_toolkit, 
#     verbose=True, # set verbose to True to show the reasoning process
# )

student_agent2 = ReActAgent(
    name="Student2",
    sys_prompt='''You are a smart student. You are given problem to solve.''',
    model_config_name="dashscope_multimodal-qwen-vl-max",
    service_toolkit=service_toolkit2, 
    verbose=False, # set verbose to True to show the reasoning process
)

# player_agent = DialogAgent(
#         name="player",
#         sys_prompt='''You're a player in a geoguessr-like turn-based game. Upon getting the url of an image from the gamemaster, you are supposed to guess where is the place shown in the image. Your guess can be a country,
#         a state, a region, a city, etc., but try to be as precise as possoble. If your answer is not correct, try again based on the hint given by the gamemaster.''',
#         model_config_name="dashscope_multimodal-qwen-vl-max",  # replace by your model config name
#     )

# print("#"*80)
# print(agent.sys_prompt)
# print("#"*80)

from agentscope.agents import UserAgent

user = UserAgent(name="User")
from agentscope.message import Msg
x = None

# x = Msg("system", "Answer the question in the image.", url = "data:image/jpeg;base64," + base64_image)
# student_agent1.speak(x)
# x = student_agent1(x)

# x = Msg("system", '''Problem: Quantum Harmonic Oscillator Energy Distribution
# A quantum physicist is studying a one-dimensional harmonic oscillator in its ground state. The wave function of the oscillator in this state is given by:
# ψ(x) = A * exp(-αx²/2)
# where A is a normalization constant and α is a positive real number related to the oscillator's properties.
# The physicist wants to determine the average potential energy of the oscillator in this state. The potential energy at any point x is given by:
# V(x) = (1/2) * k * x²
# where k is the spring constant of the oscillator.
# Tasks:

# Determine the normalization constant A, ensuring that the total probability of finding the particle anywhere is 1.
# Calculate the average potential energy of the oscillator in its ground state.
# Express your final answer in terms of ℏ (reduced Planck's constant) and ω (angular frequency of the oscillator), given that α = mω/ℏ, where m is the mass of the particle.

# Hint: You may find it useful to consider the properties of Gaussian integrals and to recall that for a quantum harmonic oscillator, k = mω².
#         ''')
# # student_agent1.speak(x)
# for i in range(1):
#     x = student_agent1(x)




x = Msg("system", '''Solve the problem: For the following games, compute all mixed Nash equilibria. In each table cell, the number on the left is the payoff to the row player, and the number on the right is the payoff to the column player.
        |   | L   | R   |
        |---|-----|-----|
        | T | 7,1 | 2,2 |
        | B | 0,5 | 3,1 |
        You need to formulate the relevant equations and ask it to solve it for you.''')
        # Note that you cannot simply ask wolfrm aplha api to find the equilibra for you. You need to formulate the relevant equations and ask it to solve it for you.''')
student_agent1.speak(x)
for i in range(5):
    x = student_agent1(x)


x = Msg("system", "Answer the following question: is 9.9 bigger than 9.11")
student_agent1.speak(x)
x = student_agent1(x)



    
