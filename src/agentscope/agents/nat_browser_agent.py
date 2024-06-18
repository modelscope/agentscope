# -*- coding: utf-8 -*-
"""A general dialog agent."""
import time
from typing import Optional

from loguru import logger

from ..message import Msg
from .agent import AgentBase
from ..prompt import PromptType

from agentscope.browser.web_browser import WebBrowser


DEFAULT_PROMPT_TEMP = """
You are an agent controlling a browser. You are given:

	(1) an objective that you are trying to achieve
	(2) the URL of your current web page
	(3) a simplified text description of what's visible in the browser window (more on that below)

You can issue these commands:
	SCROLL UP - scroll up one page
	SCROLL DOWN - scroll down one page
	CLICK X - click on a given element. You can only click on links, buttons, and inputs!
	TYPE X "TEXT" - type the specified text into the input with id X
	TYPESUBMIT X "TEXT" - same as TYPE above, except then it presses ENTER to submit the form
    ANSWER "TEXT - you can provide answers to the questions, if you think you can infer the answer from the context.

The format of the browser content is highly simplified; all formatting elements are stripped.
Interactive elements such as links, inputs, buttons are represented like this:

		<link id=1>text</link>
		<button id=2>text</button>
		<input id=3>text</input>

Images are rendered as their alt text like this:

		<img id=4 alt=""/>

Based on your given objective, issue whatever command you believe will get you closest to achieving your goal.
You always start on Google; you should submit a search query to Google that will take you to the best page for
achieving your objective. And then interact with that page to achieve your objective.

If you find yourself on Google and there are no search results displayed yet, you should probably issue a command 
like "TYPESUBMIT 7 "search query"" to get to a more useful page.

Then, if you find yourself on a Google search results page, you might issue the command "CLICK 24" to click
on the first link in the search results. (If your previous command was a TYPESUBMIT your next command should
probably be a CLICK.)

Don't try to interact with elements that you can't see.

Here are some examples:

EXAMPLE 1:
==================================================
CURRENT BROWSER CONTENT:
------------------
<link id=1>About</link>
<link id=2>Store</link>
<link id=3>Gmail</link>
<link id=4>Images</link>
<link id=5>(Google apps)</link>
<link id=6>Sign in</link>
<img id=7 alt="(Google)"/>
<input id=8 alt="Search"></input>
<button id=9>(Search by voice)</button>
<button id=10>(Google Search)</button>
<button id=11>(I'm Feeling Lucky)</button>
<link id=12>Advertising</link>
<link id=13>Business</link>
<link id=14>How Search works</link>
<link id=15>Carbon neutral since 2007</link>
<link id=16>Privacy</link>
<link id=17>Terms</link>
<text id=18>Settings</text>
------------------
OBJECTIVE: Find a 2 bedroom house for sale in Anchorage AK for under $750k
CURRENT URL: https://www.google.com/
YOUR COMMAND: 
TYPESUBMIT 8 "anchorage redfin"
==================================================

EXAMPLE 2:
==================================================
CURRENT BROWSER CONTENT:
------------------
<link id=1>About</link>
<link id=2>Store</link>
<link id=3>Gmail</link>
<link id=4>Images</link>
<link id=5>(Google apps)</link>
<link id=6>Sign in</link>
<img id=7 alt="(Google)"/>
<input id=8 alt="Search"></input>
<button id=9>(Search by voice)</button>
<button id=10>(Google Search)</button>
<button id=11>(I'm Feeling Lucky)</button>
<link id=12>Advertising</link>
<link id=13>Business</link>
<link id=14>How Search works</link>
<link id=15>Carbon neutral since 2007</link>
<link id=16>Privacy</link>
<link id=17>Terms</link>
<text id=18>Settings</text>
------------------
OBJECTIVE: Make a reservation for 4 at Dorsia at 8pm
CURRENT URL: https://www.google.com/
YOUR COMMAND: 
TYPESUBMIT 8 "dorsia nyc opentable"
==================================================

EXAMPLE 3:
==================================================
CURRENT BROWSER CONTENT:
------------------
<button id=1>For Businesses</button>
<button id=2>Mobile</button>
<button id=3>Help</button>
<button id=4 alt="Language Picker">EN</button>
<link id=5>OpenTable logo</link>
<button id=6 alt ="search">Search</button>
<text id=7>Find your table for any occasion</text>
<button id=8>(Date selector)</button>
<text id=9>Sep 28, 2022</text>
<text id=10>7:00 PM</text>
<text id=11>2 people</text>
<input id=12 alt="Location, Restaurant, or Cuisine"></input> 
<button id=13>Let’s go</button>
<text id=14>It looks like you're in Peninsula. Not correct?</text> 
<button id=15>Get current location</button>
<button id=16>Next</button>
------------------
OBJECTIVE: Make a reservation for 4 for dinner at Dorsia in New York City at 8pm
CURRENT URL: https://www.opentable.com/
YOUR COMMAND: 
TYPESUBMIT 12 "dorsia new york city"
==================================================

The current browser content, objective, and current URL follow. Reply with your next command to the browser.


CURRENT BROWSER CONTENT:
------------------
$browser_content
------------------

OBJECTIVE: $objective
CURRENT URL: $url
PREVIOUS COMMAND: $previous_command
YOUR COMMAND:
"""

class TextBrowseAgent(AgentBase):
    """
    A simple agent use text based only browser to browse web pages.
    Referanced from the project: natbot.
    """

    def __init__(
        self,
        browser: WebBrowser,
        model_config_name: str,
        name: str,
        sys_prompt: str,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
    ) -> None:
        """Initialize the dialog agent.

        Arguments:
            name (`str`):
                The name of the agent.
            model_config_name (`str`):
                The name of the model config, which is used to load model from
                configuration.
            sys_prompt (`Optional[str]`):
                The system prompt of the agent, which can be passed by args
                or hard-coded in the agent.tion.
            use_memory (`bool`, defaults to `True`):
                Whether the agent has memory.
            memory_config (`Optional[dict]`):
                The config of memory.
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            use_memory=use_memory,
            memory_config=memory_config,
        )
        self.browser = browser
        # TODO where is the best place for objective init
        self.objective = ""
        self.prev_command = ""


    # TODO change typing from dict to MSG
    def reply(self, x: dict = None) -> dict:
        """
        Given the command, execute the browsing actions.
        Args:
            x (`dict`, defaults to `None`):
                A dictionary representing the user's input to the agent. This
                input is added to the dialogue memory if provided. Defaults to
                None.
        Returns:
            A dictionary representing the message generated by the agent in
            response to the user's input.
        """
        self.objective = x.content
        gpt_cmd = ""
        prev_cmd = ""
        self.browser.visit_page("https://www.google.com/")

        while True:
        # visit google as homepage here
            
            # get browser content
            browser_content = "\n".join(self.browser._crawl_by_text())
            prompt = DEFAULT_PROMPT_TEMP
            prompt = prompt.replace("$objective", self.objective)
            url = self.browser.url
            prompt = prompt.replace("$url", url[:100])
            previous_command = prev_cmd
            prompt = prompt.replace("$previous_command", previous_command)
            prompt = prompt.replace("$browser_content", browser_content[:4500])
            browser_content_markdown= self.browser.page_html
            # prompt = prompt.replace("$browser_content_markdown", browser_content_markdown[:4500])

            prompt = self.model.format(
                Msg("user", prompt, role="user"),
            )

            quiet = False
            if not quiet:
                self.speak("URL: " + self.browser.url)
                self.speak("Objective: " + self.objective)
                self.speak("----------------\n")
                self.speak("Page Markdown:" + browser_content_markdown)
                self.speak("----------------\n")
                self.speak("----------------\n" + browser_content + "\n----------------\n")

            gpt_cmd = self.model(prompt).text
            if len(gpt_cmd) > 0:
                self.speak("Suggested command: " + gpt_cmd)





            def run_cmd(cmd):
                self.speak("running cmd:" + cmd)
                cmd = cmd.split("\n")[0]

                if cmd.startswith("SCROLL UP"):
                    self.browser.scroll("up")
                elif cmd.startswith("SCROLL DOWN"):
                    self.browser.scroll("down")
                elif cmd.startswith("CLICK"):
                    commasplit = cmd.split(",")
                    id = commasplit[0].split(" ")[1]
                    self.speak("id is:" + id)
                    self.browser.click(id)
                elif cmd.startswith("TYPE"):
                    spacesplit = cmd.split(" ")
                    id = spacesplit[1]
                    text = spacesplit[2:]
                    text = " ".join(text)
                    # Strip leading and trailing double quotes
                    text = text[1:-1]

                    if cmd.startswith("TYPESUBMIT"):
                        text += '\n'
                    self.browser.type(id, text)
                elif cmd.startswith("ANSWER"):
                    self.speak(cmd)

            time.sleep(2)
            command = input()
            if command == "r" or command == "":
                run_cmd(gpt_cmd)
            elif command == "g":
                url = input("URL:")
                self.browser.visit_page(url)
            elif command == "u":
                self.browser.scroll("up")
                time.sleep(1)
            elif command == "d":
                self.browser.scroll("down")
                time.sleep(1)
            elif command == "c":
                id = input("id:")
                self.browser.click(id)
                time.sleep(5)
            elif command == "t":
                id = input("id:")
                text = input("text:")
                self.browser.type(id, text)
                time.sleep(5)
            elif command == "o":
                self.objective = input("Objective:")
            elif command == "e":
                break
            else:
                logger.info("Invalid command")
            
            time.sleep(5)

        return {}
