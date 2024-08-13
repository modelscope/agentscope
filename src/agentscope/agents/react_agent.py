# -*- coding: utf-8 -*-
"""An agent class that implements the ReAct algorithm. The agent will reason
and act iteratively to solve problems. More details can be found in the paper
https://arxiv.org/abs/2210.03629.
"""
from typing import Optional, Union, Sequence

from agentscope.exception import ResponseParsingError, FunctionCallError
from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.parsers.regex_tagged_content_parser import (
    RegexTaggedContentParser,
)
from agentscope.service import ServiceToolkit

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

    Note this is an example implementation of ReAct algorithm in AgentScope.
    We follow the idea within the paper, but the detailed prompt engineering
    maybe different. Developers are encouraged to modify the prompt to fit
    their own needs.
    """

    def __init__(
        self,
        name: str,
        model_config_name: str,
        service_toolkit: ServiceToolkit,
        sys_prompt: str = "You're a helpful assistant. Your name is {name}.",
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
        """The reply function that achieves the ReAct algorithm.
        The more details please refer to https://arxiv.org/abs/2210.03629"""

        self.memory.add(x)

        for _ in range(self.max_iters):
            # Step 1: Thought
            if self.verbose:
                self.speak(f" ITER {_+1}, STEP 1: REASONING ".center(70, "#"))

            # Prepare hint to remind model what the response format is
            # Won't be recorded in memory to save tokens
            hint_msg = Msg(
                "system",
                self.parser.format_instruction,
                role="system",
                echo=self.verbose,
            )

            # Prepare prompt for the model
            prompt = self.model.format(self.memory.get_memory(), hint_msg)

            # Generate and parse the response
            try:
                raw_response = self.model(prompt)

                # Print out the text generated by llm in non-/streaming mode
                if self.verbose:
                    # To be compatible with streaming and non-streaming mode
                    self.speak(raw_response.stream or raw_response.text)

                res = self.parser.parse(raw_response)

                # Record the raw text into memory to avoid that LLMs learn
                # from the previous response format
                self.memory.add(Msg(self.name, res.text, "assistant"))

                # Skip the next steps if no need to call tools
                # The parsed field is a dictionary
                arg_function = res.parsed.get("function", "")
                if (
                    isinstance(arg_function, str)
                    and arg_function in ["[]", ""]
                    or isinstance(arg_function, list)
                    and len(arg_function) == 0
                ):
                    # Only the response field is exposed to users or other
                    # agents
                    msg_returned = Msg(
                        self.name,
                        res.parsed.get("response", res.text),
                        "assistant",
                    )

                    if not self.verbose:
                        # Print out the returned message
                        self.speak(msg_returned)

                    return msg_returned

            # Only catch the response parsing error and expose runtime
            # errors to developers for debugging
            except ResponseParsingError as e:
                # Print out raw response from models for developers to debug
                response_msg = Msg(self.name, e.raw_response, "assistant")
                if not self.verbose:
                    self.speak(response_msg)

                # Re-correct by model itself
                error_msg = Msg("system", str(e), "system")
                self.speak(error_msg)

                self.memory.add([response_msg, error_msg])

                # Skip acting step to re-correct the response
                continue

            # Step 2: Acting
            if self.verbose:
                self.speak(f" ITER {_+1}, STEP 2: ACTING ".center(70, "#"))

            # Parse, check and execute the tool functions in service toolkit
            try:
                # Reorganize the parsed response to the required format of the
                # service toolkit
                res.parsed["function"] = [
                    {
                        "name": res.parsed["function"],
                        "arguments": {
                            k: v
                            for k, v in res.parsed.items()
                            if k not in ["speak", "thought", "function"]
                        },
                    },
                ]

                # Execute the function
                execute_results = self.service_toolkit.parse_and_call_func(
                    res.parsed["function"],
                )

                # Note: Observing the execution results and generate response
                # are finished in the next reasoning step. We just put the
                # execution results into memory, and wait for the next loop
                # to generate response.

                # Record execution results into memory as system message
                msg_res = Msg("system", execute_results, "system")
                self.speak(msg_res)
                self.memory.add(msg_res)

            except FunctionCallError as e:
                # Catch the function calling error that can be handled by
                # the model
                error_msg = Msg("system", str(e), "system")
                self.speak(error_msg)
                self.memory.add(error_msg)

        # Exceed the maximum iterations
        hint_msg = Msg(
            "system",
            "You have failed to generate a response in the maximum "
            "iterations. Now generate a reply by summarizing the current "
            "situation.",
            role="system",
            echo=self.verbose,
        )

        # Generate a reply by summarizing the current situation
        prompt = self.model.format(self.memory.get_memory(), hint_msg)
        res = self.model(prompt)
        self.speak(res.stream or res.text)
        res_msg = Msg(self.name, res.text, "assistant")

        return res_msg
