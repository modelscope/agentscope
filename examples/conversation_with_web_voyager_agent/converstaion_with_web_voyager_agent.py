# -*- coding: utf-8 -*-
"""Example of using web browsing agent"""
import agentscope

from agentscope.browser.web_browser import WebBrowser
from agentscope.agents import WebVoyagerAgent
from agentscope.agents import UserAgent

# Fill in your OpenAI API key
YOUR_OPENAI_API_KEY = "xxx"

model_config = {
    "config_name": "gpt-4o_config",
    "model_type": "openai_chat",
    "model_name": "gpt-4o",
    "api_key": YOUR_OPENAI_API_KEY,
    "generate_args": {
        "temperature": 0.7,
    },
}

agentscope.init(
    model_configs="gpt-4o_config",
    project="Conversation with WebVoyagerAgent",
)


browser = WebBrowser()
agent = WebVoyagerAgent(
    browser=browser,
    model_config_name="gpt-4o",
    name="Browser Agent",
)

user = UserAgent("user")

x = user(None)
while x is not None:
    x = agent.reply(x)
    x = user(x)
    if x.content == "exit":  # type exit to break
        break
