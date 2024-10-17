# WebBrowsing in AgentScope

This example demonstrates how to utilize AgentScope to build a web browsing agent. Throughout this tutorial, you will gain insights into the following features of AgentScope:

- How to use the [WebBrowser](https://github.com/modelscope/agentscope/blob/main/src/agentscope/service/browser/web_browser.py) module in AgentScope
- How to build a conversation with an agent that can browse the web

Refer to our tutorial for more details on the `WebBrowser` module.

> Note: The `WebBrowser` module is currently in beta, and we are continuously working on enhancements, such as
> - allowing the agent to make long-term plan
> - handling web pages with CAPTCHA.
> - enabling text-based models to interact with web pages

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
3. [Optional] For a better understanding of how web browsing is implemented, refer to the original code in [web_browser.py](https://github.com/modelscope/agentscope/blob/main/src/agentscope/service/browser/web_browser.py) and [webact_agent.py](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_web_browser_agent/webact_agent.py).

## Running the Example

Follow the steps below to run the example:
1. Fill your OpenAI API key in `main.py`, or providing a new configuration for vision models.
2. Run the `main.py` file directly:
```bash
python main.py
```

> Note
> - The screenshots of the web pages will be saved locally.

## Code Snippets

The `webact_agent.py` provides an agent `WebActAgent` that integrates the web browsing module into [ReAct algorithm](https://arxiv.org/abs/2210.03629).
It will interact with web pages in a reasoning-acting loop, and provide the final answer to the user by calling a built-in `finish` function.

The major difference with the traditional ReAct algorithm is that the agent will set interactive marks and obtain the web page screenshot in the reasoning phase.
This allows the agent to interact with the web page more naturally.

```python
    # ...

    def _reasoning(self) -> Union[dict, None]:
        """The reasoning process of the agent.

        Returns:
            `Union[dict, None]`:
                Return `None` if meet parsing error, otherwise return the
                parsed function call dictionary.
        """

        # Mark the current interactive elements in the web page
        self.browser.set_interactive_marks()

        # After marking, take a screenshot and save it locally
        path_img = FileManager.get_instance().save_image(
            self.browser.page_screenshot,
        )

        # Assemble the prompt
        prompt = self.model.format(
            self.memory.get_memory(),
            # The observation message won't be stored in memory to avoid too
            # many images in prompt
            Msg(
                "user",
                _HINT_PROMPT.format(
                    url=self.browser.url,
                    format_instruction=self.parser.format_instruction,
                ),
                role="user",
                url=path_img,
                echo=True,
            ),
        )

        # ...
```

To save image tokens, the message with the screenshot won't be saved to the agent's memory.
That means, in each reasoning phase, the agent will only have the latest screenshot.
Developers can modify the code to implement a more complex memory mechanism.

### Example Demonstration


https://github.com/user-attachments/assets/6d03caab-6193-4ac6-8b1c-36f152ec02ec


In the first iter of our web browsing agent, the agent opens the default webpage, in this case, the Google webpage.

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

