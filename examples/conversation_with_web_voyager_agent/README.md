# WebBrowsing with AgentScope

This example demonstrates how to utilize AgentScope to enable web browsing capabilities. Throughout this tutorial, you will gain insights into the following features of AgentScope:

- How to use the [WebBrowser](../../src/agentscope/browser/web_browser.py) component in AgentScope to enable web browsing capabilities.
- Utilizing the [WebVoyagerAgent](../../src/agentscope/agents/web_voyager_agent.py) to perform web browsing tasks.

**Note: Still in Beta**
- The [WebBrowser](../../src/agentscope/browser/web_browser.py) component is currently in beta, and we are continuously working on enhancements.
- The current implementation of the [WebVoyagerAgent](../../src/agentscope/agents/web_voyager_agent.py), referenced from the [WebVoyager GitHub repository](https://github.com/MinorJerry/WebVoyager/tree/main), serves as a demonstration of enabling agents with web browsing capabilities.

The existing implementation has several limitations, including:
- The agent is not yet equipped with planning or critic modules, which impairs its ability to manage complex tasks requiring strong reasoning and self-correction while performing web browsing tasks.
- The agent is unable to handle webpages with CAPTCHA.

We are actively developing a more advanced web browsing agent, focusing on improving performance, reducing error rates, and minimizing latency. Please stay tuned for updates.

## Tested Models

This example has been tested with the following model:
- GPT-4o

We plan to test additional vision models in the near future. Additionally, we will enable web browsing capabilities for text-only models.

## Prerequisites

To run this example, you need to:

1. Ensure you have access to a vision model that can handle vision tasks, and set your api key in the model config.
2. Install the necessary Playwright packages:
    - Run `pip install playwright` to set up the Python environment.
    - Run `playwright install` to install the required browser for Playwright.
3. [Optional] For a better understanding of how web browsing is implemented, refer to the original code in [web_browser.py](../../src/agentscope/browser/web_browser.py) and [web_voyager_agent.py](../../src/agentscope/agents/web_voyager_agent.py).


## Code Snippets and Example Demonstration

Here is a demo of the how web browsing currently works in AgentScope.

### Code Snippets

First we init agentcope and the model configs.

```python
import agentscope

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
```

Then we init the browser and the agent.

``` python
from agentscope.browser.web_browser import WebBrowser
from agentscope.agents.web_voyager_agent import WebVoyagerAgent


browser = WebBrowser()
agent = WebVoyagerAgent(
    browser=browser,
    model_config_name="gpt-4o",
    name="Browser Agent")
```

Finally, we can use the agent to perform web browsing tasks.
Here, we ask the agent how many stars have our agentscope project received on github.

```python
question = "How many stars have the project agentscope recieved on the github?"
msg = Msg(name="user", content=question, role="user")

ans_msg = agent.reply(msg)
```

### Example Demonstration


https://github.com/user-attachments/assets/6d03caab-6193-4ac6-8b1c-36f152ec02ec


In the first iter of our web browsing agent, the agent opens the default webpage, in this case, the google webpage.

We can see from the saved screenshot here that the interactive elements in this webpage are marked with numbers. This is called the set-of-mark prompting([github link](https://github.com/microsoft/SoM), [paper link](https://arxiv.org/abs/2310.11441)). Utilizing the set-of-mark prompting, the agent can interact with the webpage more naturally by selecting the elements with the corresponding numbers.

After recieving the observation, the agent will give it's thought and corresponding action.
In this case, the agent select the search bar (numbered as [4]) and type in it.

![screenshot_1](https://github.com/garyzhang99/agentscope/assets/46197280/9de208b8-4ef4-4b4f-9328-2f7bb500fcb2)


```
Thought: To find out how many stars the project "agentscope" has on GitHub, I need to search for "agentscope GitHub" on Google first.

Action: Type [4]; agentscope GitHub
```


In the next iter, we see that the agent is presented with the searching result page, and the agent select the offical github link.
![screenshot_2](https://github.com/garyzhang99/agentscope/assets/46197280/9b6708c6-eced-4d8b-8ebe-cdbd197b40ea)

```
Thought: The search results from Google have populated, and I found a link that likely leads to the "agentscope" GitHub project page.

Action: Click [18]
```

As the agent view the github page of agentscope, it note the github stars, hence it answer our question.

![screenshot_3](https://github.com/garyzhang99/agentscope/assets/46197280/5cad5472-b45b-4ef3-a8fa-324d5a20073a)


```
Thought: I can see from the screenshot that the star count for the "agentscope" project on GitHub is listed as "2.9k" stars.

Action: ANSWER; The project agentscope has received 2.9k stars on GitHub.
```

The above content provides a simple example of using the web browsing agent in AgentScope. Feel free to try it out yourself and explore the capabilities of web browsing with AgentScope!

