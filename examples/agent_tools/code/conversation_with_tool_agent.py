# -*- coding: utf-8 -*-
"""Main script to run the conversation between the tool agent and user"""
import sys
import io

import agentscope
from agentscope.agents import ToolAgent, UserAgent
from agentscope.service import ServiceResponse, ServiceExecStatus

from agentscope.service import (
    bing_search,  # or google_search,
    read_text_file,
    write_text_file,
    ServiceFactory,
)

# Prerequisites:
# 1. You need to have a Bing Search API key to use the `bing_search` service.
BING_API_KEY = "{YOUR_BING_API}"
# 2. Init agentscope by your model configuration
YOUR_MODEL_CONFIG_NAME = "{YOUR_MODEL_CONFIG_NAME}"
agentscope.init(model_configs="{YOUR_MODEL_CONFIG}")


# Step 1: Customize a new service function
def execute_python_code(code: str) -> ServiceResponse:  # pylint: disable=C0301
    """
    Execute Python code and capture the output. Note you must `print` the output to get the result.

    Args:
        code (`str`):
            The Python code to be executed.
    """  # noqa

    # Create a StringIO object to capture the output
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    try:
        # Using `exec` to execute code
        exec(code)
    except Exception as e:
        # If an exception occurs, capture the exception information
        output = str(e)
        status = ServiceExecStatus.ERROR
    else:
        # If the execution is successful, capture the output
        output = new_stdout.getvalue()
        status = ServiceExecStatus.SUCCESS
    finally:
        # Recover the standard output
        sys.stdout = old_stdout

    # Wrap the output and status into a ServiceResponse object
    return ServiceResponse(status, output)


# Step 2: Prepare all tool functions for the agent
# Deal with arguments that need to be input by developers
tools = [
    ServiceFactory.get(bing_search, api_key=BING_API_KEY, num_results=3),
    ServiceFactory.get(execute_python_code),
    ServiceFactory.get(read_text_file),
    ServiceFactory.get(write_text_file),
]

# Step 3: Create a tool agent and build a conversation
agent = ToolAgent(
    name="Assistant",
    model_config_name=YOUR_MODEL_CONFIG_NAME,
    tools=tools,
    verbose=True,  # whether to print the raw response from LLM, execution
    # status, and output
)
user = UserAgent(name="User")

# construct the conversation
x = None
while True:
    x = user(x)
    if x.content == "exit":
        break
    x = agent(x)
