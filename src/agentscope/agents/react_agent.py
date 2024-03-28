# -*- coding: utf-8 -*-
"""An agent class that implements the ReAct algorithm. The agent will reason
and act iteratively to solve problems. More details can be found in the paper
https://arxiv.org/abs/2210.03629.
"""
import json
from typing import Tuple, List

from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.models import ModelResponse
from agentscope.service import ServiceResponse, ServiceExecStatus


DEFAULT_TOOL_PROMPT = """
The following tool functions are available in the format of
```
{{index}}. {{function name}}: {{function description}}
    {{argument name}} ({{argument type}}): {{argument description}}
    ...
```

Tool Functions:
{function_prompt}

Notice:
1. Fully understand the tool function and its arguments before using it.
2. Only use the tool function when it's necessary.
3. Check if the arguments you provided to the tool function is correct in type and value.
4. You can't take some problems for granted. For example, where you are, what's the time now, etc. But you can try to use the tool function to solve the problem.
5. If the function execution fails, you should analyze the error and try to solve it.

"""  # noqa

TOOL_HINT_PROMPT = """
Generate a response in the following format:

Response Format:
You should respond in the following format, which can be loaded by `json.loads` in Python:
{{
    "thought": "what you thought",
    "speak": "what you said",
    "function": [{{"name": "{{function name}}", "arguments": {{"{{argument name}}": {{argument_value}}, ...}}}}, ...]
}}

Taking using web_search function as an example, the response should be like this:
{{
    "thought": "xxx",
    "speak": "xxx",
    "function": [{{"name": "web_search", "arguments": {{"query": "what's the weather today?"}}}}]
}}
"""  # noqa

FUNCTION_RESULT_TITLE_PROMPT = """Execution Results:
"""

FUNCTION_RESULT_PROMPT = """{index}. {function_name}:
    [EXECUTE STATUS]: {status}
    [EXECUTE RESULT]: {result}
"""


def parse_func(response: ModelResponse) -> ModelResponse:
    """Parsing the response into a dict object."""
    return ModelResponse(raw=json.loads(response.text))


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
        sys_prompt: str = "You're a helpful assistant.",
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
                Whether to print the output of the tools.
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
            self.sys_prompt = sys_prompt + tools_prompt
        else:
            self.sys_prompt = sys_prompt + "\n" + tools_prompt

        # Put sys prompt into memory
        self.memory.add(Msg("system", self.sys_prompt, role="system"))

    def reply(self, x: dict = None) -> dict:
        """The reply function that achieves the ReAct algorithm.
        The more details please refer to https://arxiv.org/abs/2210.03629"""

        if self.memory:
            self.memory.add(x)

        for _ in range(self.max_iters):
            # Step 1: Thought

            self.speak(f" ITER {_+1}, STEP 1: REASONING ".center(70, "#"))

            # Generate LLM response
            prompt = self.model.format(
                self.memory.get_memory(),
                Msg("system", TOOL_HINT_PROMPT, role="system"),
            )

            res = self.model(
                prompt,
                parse_func=parse_func,
                max_retries=3,
            ).raw

            # Record the response in memory
            msg_thought = Msg(self.name, res, role="assistant")

            # To better display the response, we reformat it by json.dumps here
            self.speak(
                Msg(self.name, json.dumps(res, indent=4), role="assistant"),
            )

            if self.memory:
                self.memory.add(msg_thought)

            # Skip the next steps if no need to call tools
            if len(res.get("function", [])) == 0:
                return msg_thought

            # Step 2: Action

            self.speak(f" ITER {_+1}, STEP 2: ACTION ".center(70, "#"))

            # Execute functions
            execute_results = []
            for i, func in enumerate(res["function"]):
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
            if self.memory:
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

        self.speak(f">>> Executing function {func_name} ...")

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
