# -*- coding: utf-8 -*-
"""An agent class that implements the ReAct algorithm. The agent will reason
and act iteratively to solve problems. More details can be found in the paper
https://arxiv.org/abs/2210.03629.
"""
from typing import Tuple, List

from agentscope._exception import (
    JsonParsingError,
    MissingTagError,
    ResponseParsingError,
)
from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.parser import MultiTaggedContentParser, TaggedContent
from agentscope.service import ServiceResponse, ServiceExecStatus


DEFAULT_TOOL_PROMPT = """The following tool functions are available in the format of
```
{{index}}. {{function name}}: {{function description}}
    {{argument1 name}} ({{argument type}}): {{argument description}}
    {{argument2 name}} ({{argument type}}): {{argument description}}
    ...
```

## Tool Functions:
{function_prompt}

## What You Should Do:
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

FUNCTION_RESULT_TITLE_PROMPT = """Execution Results:
"""

FUNCTION_RESULT_PROMPT = """{index}. Executing {function_name}
    [EXECUTE ARGUMENTS]:
        {arguments}
    [EXECUTE STATUS]: {status}
    [EXECUTE RESULT]: {result}
"""


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
        tools: List[Tuple],
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
            tools (`List[Tuple]`):
                A list of tuples, each containing the name of a tool and the
                tool's description in JSON schema format.
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

        self.tools = tools
        self.verbose = verbose
        self.max_iters = max_iters

        func_prompt, self.func_name_mapping = self.prepare_funcs_prompt(tools)

        # Prepare system prompt
        tools_prompt = DEFAULT_TOOL_PROMPT.format(function_prompt=func_prompt)

        if sys_prompt.endswith("\n"):
            self.sys_prompt = sys_prompt.format(name=self.name) + tools_prompt
        else:
            self.sys_prompt = (
                sys_prompt.format(name=self.name) + "\n" + tools_prompt
            )

        # Put sys prompt into memory
        self.memory.add(Msg("system", self.sys_prompt, role="system"))

        # Initialize a parser object to
        self.parser = MultiTaggedContentParser(
            TaggedContent(
                name="thought",
                tag_begin="[THOUGHT]",
                content_hint="what you thought",
                tag_end="[/THOUGHT]",
            ),
            TaggedContent(
                name="speak",
                tag_begin="[SPEAK]",
                content_hint="what you speak",
                tag_end="[/SPEAK]",
            ),
            TaggedContent(
                name="function",
                tag_begin="[FUNCTION]",
                content_hint=(
                    '[{"name": "{function name}", "arguments": '
                    '{"{argument1 name}": xxx, "{argument2 name}": xxx}}, ...]'
                ),
                tag_end="[/FUNCTION]",
                parse_json=True,
            ),
        )

    def reply(self, x: dict = None) -> dict:
        """The reply function that achieves the ReAct algorithm.
        The more details please refer to https://arxiv.org/abs/2210.03629"""

        self.memory.add(x)

        for _ in range(self.max_iters):
            # Step 1: Thought
            if self.verbose:
                self.speak(f" ITER {_+1}, STEP 1: REASONING ".center(70, "#"))

            try:
                # Memory won't record hint_msg to save tokens
                hint_msg = Msg(
                    "system",
                    self.parser.format_instruction,
                    role="system",
                )
                if self.verbose:
                    self.speak(hint_msg)

                # Generate LLM response
                prompt = self.model.format(self.memory.get_memory(), hint_msg)
                res = self.model(
                    prompt,
                    parse_func=self.parser.parse,
                    max_retries=1,
                )

            # Only catch the response parsing error and expose runtime
            # errors to developers for debugging
            except (
                ResponseParsingError,
                MissingTagError,
                JsonParsingError,
            ) as e:
                # Still print out the raw response from models for developers
                # to debug
                response_msg = Msg(self.name, e.raw_response, "assistant")
                self.speak(response_msg)

                # Re-correct by model itself
                error_msg = Msg("system", str(e), "system")
                self.speak(error_msg)

                self.memory.add([response_msg, error_msg])

                # Skip acting step to re-correct the response
                continue

            # Record the response in memory
            msg_response = Msg(self.name, res.text, "assistant")
            self.memory.add(msg_response)
            if self.verbose:
                self.speak(msg_response)
            else:
                self.speak(Msg(self.name, res.parsed["speak"], "assistant"))

            # Skip the next steps if no need to call tools
            # The parsed field is a dictionary
            if len(res.parsed.get("function", [])) == 0:
                # Only the speak field is exposed to users or other agents
                return Msg(self.name, res.parsed["speak"], "assistant")

            # Step 2: Action
            if self.verbose:
                self.speak(f" ITER {_+1}, STEP 2: ACTION ".center(70, "#"))

            # Check the format of function calling

            # Execute functions
            # TODO: check the provided arguments and re-correct them if needed
            execute_results = []
            for i, func in enumerate(res.parsed["function"]):
                # Execute the function
                func_res = self.execute_func(i, func)
                execute_results.append(func_res)

            # Prepare prompt for execution results
            execute_results_prompt = "\n".join(
                [
                    FUNCTION_RESULT_PROMPT.format_map(res)
                    for res in execute_results
                ],
            )
            # Add title
            execute_results_prompt = (
                FUNCTION_RESULT_TITLE_PROMPT + execute_results_prompt
            )

            # Note: Observing the execution results and generate response are
            # finished in the next loop. We just put the execution results
            # into memory, and wait for the next loop to generate response.

            # Record execution results into memory as a message from the system
            msg_res = Msg(
                name="system",
                content=execute_results_prompt,
                role="system",
            )
            self.speak(msg_res)
            self.memory.add(msg_res)

        return Msg(
            "system",
            "The agent has reached the maximum iterations.",
            role="system",
        )

    def execute_func(self, index: int, func_call: dict) -> dict:
        """Execute the tool function and return the result.

        Args:
            index (`int`):
                The index of the tool function.
            func_call (`dict`):
                The function call dictionary with keys 'name' and 'arguments'.

        Returns:
            `ServiceResponse`: The execution results.
        """
        # Extract the function name and arguments
        func_name = func_call["name"]
        func_args = func_call["arguments"]

        self.speak(f">>> Executing function {func_name} with arguments:")
        for key, value in func_args.items():
            value = value if len(str(value)) < 50 else str(value)[:50] + "..."
            self.speak(f">>> \t{key}: {value}")

        try:
            func_res = self.func_name_mapping[func_name](**func_args)
        except Exception as e:
            func_res = ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=str(e),
            )

        self.speak(">>> END ")

        status = (
            "SUCCESS"
            if func_res.status == ServiceExecStatus.SUCCESS
            else "FAILED"
        )

        # return the result of the function
        return {
            "index": index + 1,
            "function_name": func_name,
            "status": status,
            "result": func_res.content,
        }

    def prepare_funcs_prompt(self, tools: List[Tuple]) -> Tuple[str, dict]:
        """Convert function descriptions from json schema format to
        string prompt format.

        Args:
            tools (`List[Tuple]`):
                The list of tool functions and their descriptions in JSON
                schema format.

        Returns:
            `Tuple[str, dict]`:
                The string prompt for the tool functions and a function name
                mapping dict.

            .. code-block:: python

                {index}. {function name}: {function description}
                    {argument name} ({argument type}): {argument description}
                    ...

        """
        tools_prompt = []
        func_name_mapping = {}
        for i, (func, desc) in enumerate(tools):
            func_name = desc["function"]["name"]
            func_name_mapping[func_name] = func

            func_desc = desc["function"]["description"]
            args_desc = desc["function"]["parameters"]["properties"]

            args_list = [f"{i + 1}. {func_name}: {func_desc}"]
            for args_name, args_info in args_desc.items():
                if "type" in args_info:
                    args_line = (
                        f'\t{args_name} ({args_info["type"]}): '
                        f'{args_info.get("description", "")}'
                    )
                else:
                    args_line = (
                        f'\t{args_name}: {args_info.get("description", "")}'
                    )
                args_list.append(args_line)

            func_prompt = "\n".join(args_list)
            tools_prompt.append(func_prompt)

        return "\n".join(tools_prompt), func_name_mapping
