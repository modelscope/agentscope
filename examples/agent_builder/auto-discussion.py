# -*- coding: utf-8 -*-
"""A simple example for auto discussion: the agent builder automatically\
 set up the agents participating the discussion ."""
from utils import load_txt, extract_scenario_and_participants
import agentscope
from agentscope.agents import DialogAgent
from agentscope.pipelines.functional import sequentialpipeline

model_configs = [
    {
        "type": "openai",
        "name": "gpt-3.5-turbo",
        "api_key": "xxx",  # Load from env if not provided
        "organization": "xxx",  # Load from env if not provided
        "generate_args": {
            "temperature": 0.5,
        },
    },
    {
        "type": "post_api",
        "name": "my_post_api",
        "api_url": "https://xxx",
        "headers": {},
    },
]
agentscope.init(model_configs=model_configs)


# init agent_builder
agent_builder = DialogAgent(
    name="agent_builder",
    sys_prompt="You're a helpful assistant.",
    model="my_post_api",
    # model="gpt-3.5-turbo",  # replace by your model config name
)

discussion_agent = DialogAgent(
    name="agent_builder",
    sys_prompt="You're a helpful assistant.",
    model="my_post_api",
    # model="gpt-3.5-turbo",  # replace by your model config name
)


max_round = 2
query = "Say the pupil of your eye has a diameter of 5 mm and you have a \
telescope with an aperture of 50 cm. How much more light can the \
telescope gather than your eye?"

# get the discussion scenario and participant agents
x = load_txt("examples/auto-agent/agent_builder_instruct.txt").format(
    question=query,
)
settings = agent_builder(x)
scenario_participants = extract_scenario_and_participants(settings["content"])

# set the agents that participant the discussion
agents = [
    DialogAgent(
        name=key,
        sys_prompt=val,
        model="my_post_api",
        # model="gpt-3.5-turbo",  # replace by your model config name
    )
    for key, val in scenario_participants["Participants"].items()
]

# begin discussion
x = f"let's discuss to solve the question: {query}"
for i in range(max_round):
    x = sequentialpipeline(agents, x)
