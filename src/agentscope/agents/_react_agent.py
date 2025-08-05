# -*- coding: utf-8 -*-
"""An agent class that implements the ReAct algorithm. The agent will reason
and act iteratively to solve problems. More details can be found in the paper
https://arxiv.org/abs/2210.03629.
"""
from typing import Optional, Union, Sequence

from shortuuid import uuid

from agentscope.exception import ResponseParsingError
from agentscope.agents import AgentBase
from agentscope.message import Msg, ToolUseBlock
from agentscope.parsers import RegexTaggedContentParser
from agentscope.service import (
    ServiceToolkit,
    ServiceResponse,
    ServiceExecStatus,
)

INSTRUCTION_PROMPT = """## What You Should Do:
1. First, analyze the current situation, and determine your goal.
2. Then, check if your goal is already achieved. If so, try to generate a response. Otherwise, think about how to achieve it with the help of provided tool functions.
3. Respond in the required format.

## Note:
1. Fully understand the tool functions and their arguments before using them.
2. You should decide if you need to use the tool functions, if not then return an empty list in "function" field.
3. Make sure the types and values of the arguments you provided to the tool functions are correct.
4. Don't take things for granted. For example, where you are, what's the time now, etc. You can try to use the tool functions to get information.
5. If the function execution fails, you should analyze the error and try to solve it.
"""  # noqa


class ReActAgent(AgentBase):
    """An agent class that implements the ReAct algorithm. More details refer
    to https://arxiv.org/abs/2210.03629.

    This is an example implementation of ReAct algorithm in AgentScope.
    We follow the idea within the paper, but the detailed prompt engineering
    maybe different. Developers are encouraged to modify the prompt to fit
    their own needs.

    Note:
        1. We use the "thought" field in the response to support
        Chain-of-Thought, which means the tool functions cannot use "thought"
        as their argument name.
        2. The function name "finish" is also a reserved name when using this
        agent, which will be used to end the reasoning-acting loop.
    """

    def __init__(
        self,
        name: str,
        model_config_name: str,
        service_toolkit: ServiceToolkit,
        sys_prompt: str = "You're a helpful assistant named {name}.",
        max_iters: int = 10,
        verbose: bool = True,
    ) -> None:
        """Initialize the ReAct agent with the given name, model config name
        and tools.

        Args:
            name (`str`):
                The name of the agent.
            sys_prompt (`str`):
                The system prompt of the agent.
            model_config_name (`str`):
                The name of the model config, which is used to load model from
                configuration.
            service_toolkit (`ServiceToolkit`):
                A `ServiceToolkit` object that contains the tool functions.
            max_iters (`int`, defaults to `10`):
                The maximum number of iterations of the reasoning-acting loops.
            verbose (`bool`, defaults to `True`):
                Whether to print the detailed information during reasoning and
                acting steps. If `False`, only the content in speak field will
                be print out.
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
        )

        self.service_toolkit = service_toolkit

        # Add `finish` function to the toolkit to allow agent to end
        # the reasoning-acting loop
        self.service_toolkit.add(self.finish)

        self.verbose = verbose
        self.max_iters = max_iters

        if not sys_prompt.endswith("\n"):
            sys_prompt = sys_prompt + "\n"

        self.sys_prompt = "\n".join(
            [
                # The brief intro of the role and target
                sys_prompt.format(name=self.name),
                # The instruction prompt for tools
                self.service_toolkit.tools_instruction,
                # The detailed instruction prompt for the agent
                INSTRUCTION_PROMPT,
            ],
        )

        # Put sys prompt into memory
        self.memory.add(Msg("system", self.sys_prompt, role="system"))

        # Initialize a parser object to formulate the response from the model
        self.parser = RegexTaggedContentParser(
            format_instruction="""Respond with specific tags as outlined below:
<thought>{what you thought}</thought>
<function>{the function name you want to call}</function>
<{argument name}>{argument value}</{argument name}>
<{argument name}>{argument value}</{argument name}>
...""",  # noqa
            try_parse_json=True,
            required_keys=["thought", "function"],
        )

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """The reply method of the agent."""
        self.memory.add(x)

        for _ in range(self.max_iters):
            # Step 1: Reasoning: decide what function to call
            tool_call = self._reasoning()

            if tool_call is None:
                # Meet parsing error, skip acting to reason the parsing error,
                # which has been stored in memory
                continue

            # Step 2: Acting: execute the function accordingly
            msg_finish = self._acting(tool_call)
            if msg_finish:
                return msg_finish

        # Generate a response when exceeding the maximum iterations
        return self._summarizing()

    def _reasoning(self) -> Union[ToolUseBlock, None]:
        """The reasoning process of the agent.

        Returns:
            `Union[ToolUseBlock, None]`:
                Return `None` if no tool is used, otherwise return the tool use
                block.
        """
        # Assemble the prompt
        prompt = self.model.format(
            self.memory.get_memory(),
            # Hint LLM how to respond without putting hint message into memory
            Msg(
                "system",
                self.parser.format_instruction,
                role="system",
                echo=self.verbose,
            ),
        )

        # Get the response from the model and print it out
        raw_response = self.model(prompt)
        if self.verbose:
            self.speak(raw_response.stream or raw_response.text)
        self.memory.add(Msg(self.name, raw_response.text, role="assistant"))

        # Try to parse the response into tool use block
        try:
            res = self.parser.parse(raw_response)
            # Compose into a tool use block
            function_name: str = res.parsed["function"]
            input_ = {
                k: v
                for k, v in res.parsed.items()
                if k not in ["function", "thought"]
            }

            return ToolUseBlock(
                type="tool_use",
                id=uuid(),
                name=function_name,
                input=input_,
            )

        except ResponseParsingError as e:
            # When failed to parse the response, return the error message to
            # the llm
            self.memory.add(Msg("system", str(e), "system", echo=self.verbose))
            return None

    def _acting(self, tool_call: ToolUseBlock) -> Union[None, Msg]:
        """The acting process of the agent, which takes a tool use block as
        input, execute the function and return a message if the `finish`
        function is called.

        Args:
            tool_call (`ToolUseBlock`):
                The tool use block to be executed.

        Returns:
            `Union[None, Msg]`:
                Return `None` if the function is not `finish`, otherwise return
                a message to the user.
        """
        # The execution message, may be execution output or error information
        msg_execution = self.service_toolkit.parse_and_call_func(tool_call)

        if self.verbose:
            self.speak(msg_execution)
        self.memory.add(msg_execution)

        if tool_call["name"] == "finish":
            return Msg(
                self.name,
                str(tool_call["input"]["response"]),
                "assistant",
            )
        return None

    def _summarizing(self) -> Msg:
        """Generate a response when the agent fails to solve the problem in
        the maximum iterations."""
        hint_msg = Msg(
            "user",
            "You have failed to generate response within the maximum "
            "iterations. Now respond directly by summarizing the current "
            "situation.",
            role="user",
            echo=self.verbose,
        )

        # Generate a reply by summarizing the current situation
        prompt = self.model.format(
            self.memory.get_memory(),
            hint_msg,
        )
        res = self.model(prompt)
        self.speak(res.stream or res.text)
        res_msg = Msg(self.name, res.text, "assistant")
        return res_msg

    @staticmethod
    def finish(response: str) -> ServiceResponse:
        """Finish reasoning and generate a response to the user.

        Note:
            The function won't be executed, actually.

        Args:
            response (`str`):
                The response to the user.
        """
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=response,
        )
