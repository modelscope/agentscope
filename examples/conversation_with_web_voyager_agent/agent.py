# -*- coding: utf-8 -*-
from typing import Optional, Union, Sequence

from agentscope.agents import AgentBase
from agentscope.browser import WebBrowser
from agentscope.exception import ResponseParsingError, FunctionCallError
from agentscope.manager import ModelManager
from agentscope.memory import TemporaryMemory
from agentscope.message import Msg
from agentscope.parsers import RegexTaggedContentParser
from agentscope.service import ServiceToolkit

_SYSTEM_PROMPT = """You're an AI assistant named {name}.

## Your Target
Help the user to solve problems with the given web browsing commands.

## Key Guidelines You MUST follow
1 To input text, NO need to click textbox first, directly type content. After typing, the system automatically hits `ENTER` key. Sometimes you should click the search button to apply search filters. Try to use simple language when searching.
2 You must Distinguish between textbox and search button, don't type content into the button! If no textbox is found, you may need to click the search button first before the textbox is displayed.
3 Execute only one action per iteration.
4 STRICTLY Avoid repeating the same action if the webpage remains unchanged. You may have selected the wrong web element or numerical label. Continuous use of the Wait is also NOT allowed. Continuous use of the Scroll with no change of webpage is NOT allowed.
5 When a complex Task involves multiple questions or steps, select "ANSWER" only at the very end, after addressing all of these questions (steps). Flexibly combine your own abilities with the information in the web page. Double check the formatting requirements in the task when ANSWER.
6 When the user's task is a simple request, you should select "ANSWER" to complete the task.
7 When you are not sure whether you are making progress, you can select "ANSWER" and ask the user for more infomation.

## Web Browsing Guidelines
1 Don't interact with useless web elements like Login, Sign-in, donation that appear in Webpages. Pay attention to Key Web Elements like search textbox and menu.
2 Focus on the numerical labels in the TOP LEFT corner of each rectangle (element). Ensure you don't mix them up with other numbers (e.g. Calendar) on the page.
3 Focus on the date in task, you must look for results that match the date. It may be necessary to find the correct year, month and day at calendar.
4 Pay attention to the filter and sort functions on the page, which, combined with scroll, can help you solve conditions like 'highest', 'cheapest', 'lowest', 'earliest', etc. Try your best to find the answer that best fits the task.
5 You can use "Goto" if you need to goto a specific webpage.
"""  # noqa

FORMAT_INSTRUCTION = """Your reply should strictly follow the format:
<thought> {Your brief thoughts (briefly summarize the info that will help ANSWER)} </thought>
<action> {One Action format you choose} </action>
""" # noqa


class WebActAgent(AgentBase):
    def __init__(
        self,
        name: str,
        model_config_name: str,
        vision: bool = False,
    ) -> None:
        super().__init__(name, model_config_name)

        # Init the browser
        self.browser = WebBrowser()

        # Init the service toolkit with the browser commands. Because these
        # commands don't require arguments, we directly add them to the toolkit
        # with the `get_action_functions` method.
        self.toolkit = ServiceToolkit()
        for func in self.browser.get_action_functions():
            self.toolkit.add(func)

        # Prepare system prompt, which includes the instruction for the tools
        self.sys_prompt = _SYSTEM_PROMPT + self.toolkit.tools_instruction
        self.memory.add(
            Msg(
                name="system",
                content=self.sys_prompt.format(name=self.name),
                role="system",
            ),
        )

        # Initialize a parser object to formulate the response from the model
        self.parser = RegexTaggedContentParser(
            format_instruction="""Respond with specific tags as outlined below:

- When calling tool functions (note the "arg_name" should be replaced with the actual argument name):
<thought>what you thought</thought>
<function>the function name you want to call</function>
<arg_name>the value of the argument</arg_name>
<arg_name>the value of the argument</arg_name>

- When you want to generate a final response:
<thought>what you thought</thought>
<response>what you respond</response>
...""",  # noqa
            try_parse_json=True,
            required_keys=["thought"],
            keys_to_content="response",
        )

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """The reply method of the agent."""
        self.memory.add(x)

        # The temporary used to store the thinking process, which will be
        # cleared at the end of the reply function and not saved in memory
        # temporary_memory = []

        return Msg("", "", "")
