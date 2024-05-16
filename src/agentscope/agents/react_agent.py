# -*- coding: utf-8 -*-
"""An agent class that implements the ReAct algorithm. The agent will reason
and act iteratively to solve problems. More details can be found in the paper
https://arxiv.org/abs/2210.03629.
"""
from typing import Any

from loguru import logger

from agentscope.exception import ResponseParsingError, FunctionCallError
from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.parsers import MarkdownJsonDictParser
from agentscope.service import ServiceToolkit
from agentscope.service.service_toolkit import ServiceFunction

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
        service_toolkit: ServiceToolkit = None,
        sys_prompt: str = "You're a helpful assistant. Your name is {name}.",
        max_iters: int = 10,
        verbose: bool = True,
        **kwargs: Any,
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

        # TODO: To compatible with the old version, which will be deprecated
        #  soon
        if "tools" in kwargs:
            logger.warning(
                "The argument `tools` will be deprecated soon. "
                "Please use `service_toolkit` instead. Example refers to "
                "https://github.com/modelscope/agentscope/blob/main/"
                "examples/conversation_with_react_agent/code/"
                "conversation_with_react_agent.py",
            )

            service_funcs = {}
            for func, json_schema in kwargs["tools"]:
                name = json_schema["function"]["name"]
                service_funcs[name] = ServiceFunction(
                    name=name,
                    original_func=func,
                    processed_func=func,
                    json_schema=json_schema,
                )

            if service_toolkit is None:
                service_toolkit = ServiceToolkit()
                service_toolkit.service_funcs = service_funcs
            else:
                service_toolkit.service_funcs.update(service_funcs)

        elif service_toolkit is None:
            raise ValueError(
                "The argument `service_toolkit` is required to initialize "
                "the ReActAgent.",
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
        self.parser = MarkdownJsonDictParser(
            content_hint={
                "thought": "what you thought",
                "speak": "what you speak",
                "function": service_toolkit.tools_calling_format,
            },
            required_keys=["thought", "speak", "function"],
            # Only print the speak field when verbose is False
            keys_to_content=True if self.verbose else "speak",
        )

    def reply(self, x: dict = None) -> dict:
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
                res = self.model(
                    prompt,
                    parse_func=self.parser.parse,
                    max_retries=1,
                )

                # Record the response in memory
                self.memory.add(
                    Msg(
                        self.name,
                        self.parser.to_memory(res.parsed),
                        "assistant",
                    ),
                )

                # Print out the response
                msg_returned = Msg(
                    self.name,
                    self.parser.to_content(res.parsed),
                    "assistant",
                )
                self.speak(msg_returned)

                # Skip the next steps if no need to call tools
                # The parsed field is a dictionary
                arg_function = res.parsed["function"]
                if (
                    isinstance(arg_function, str)
                    and arg_function in ["[]", ""]
                    or isinstance(arg_function, list)
                    and len(arg_function) == 0
                ):
                    # Only the speak field is exposed to users or other agents
                    return msg_returned

            # Only catch the response parsing error and expose runtime
            # errors to developers for debugging
            except ResponseParsingError as e:
                # Print out raw response from models for developers to debug
                response_msg = Msg(self.name, e.raw_response, "assistant")
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
        res_msg = Msg(self.name, res.text, "assistant")
        self.speak(res_msg)

        return res_msg
