# -*- coding: utf-8 -*-
"""
"""
import json
from typing import Sequence, Tuple, Literal

from loguru import logger

from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.models import ModelResponse
from agentscope.service import ServiceResponse, ServiceExecStatus


DEFAULT_SYS_PROMPT = """
You're a helpful assistant. You target is to help users to solve their problems.

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

FUNCTION_RESULT_TITLE_PROMPT = """
Execute Results:
"""

FUNCTION_RESULT_PROMPT = """
{index}. {function_name}:
    [EXECUTE STATUS]: {status}
    [EXECUTE RESULT]: {result}
"""

OBSERVE_HINT_PROMPT = """
Determine if you've achieved your goals based on the above dialogue history and execution results. 

You should respond in the following format, which can be loaded by `json.loads` in Python:
{{
    "thought": "Your thought and analysis",
    "achieved": true/false 
}} 
"""


def parse_func(response: ModelResponse) -> ModelResponse:
    return ModelResponse(raw=json.loads(response.raw))


class ReactAgent(AgentBase):
    def __init__(
            self,
            name: str,
            sys_prompt: str,
            model_config_name: str,
            tools: Sequence[Tuple[str, dict]],
            max_iters: int = 10,
            verbose: bool = True,
    ):
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
            tools (`Sequence[Tuple[str, dict]]`):
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

        self.func_name_mapping = ()

        # Put system prompt into memory
        self.memory.add(Msg("system", self.sys_prompt, role="system"))

    def reply(self, x: dict = None) -> dict:
        if self.memory:
            self.memory.add(x)

        for _ in range(self.max_iters):
            ######################## Step 1: Thought ########################

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

            self.speak(msg_thought)

            if self.memory:
                self.memory.add(msg_thought)

            # Skip the next steps if no need to call tools
            if len(res.get("function", [])) == 0:
                return msg_thought

            ######################## Step 2: Action ##########################

            # Execute functions
            execute_results = []
            for i, func in enumerate(res["function"]):
                # Execute the function
                func_res = self.execute_func(i, func)
                execute_results.append(func_res)

            # Prepare prompt for execution results
            execute_results_prompt = "\n".join([FUNCTION_RESULT_PROMPT.format_map(res) for res in execute_results])
            # Add title
            execute_results_prompt = FUNCTION_RESULT_TITLE_PROMPT + execute_results_prompt

            # Record execution results into memory as a message from the system
            msg = Msg(
                name="system",
                content=execute_results_prompt,
                role="system",
            )
            if self.memory:
                self.memory.add(msg)

            ######################## Step 3: Observe ########################

            # Generate LLM response or
            prompt_obs = self.model.format(
                Msg("system", self.sys_prompt, role="system"),
                self.memory.get_memory(),
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

        logger.info(f"Executing function {func_name} with arguments {func_args}")
        try:
            func_res = self.func_name_mapping[func_name](**func_args)
        except Exception as e:
            func_res = ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=str(e),
            )

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

    def _customize_print(
        self,
        content: str,
        color: Literal["red", "blue", "green"] = "blue",
    ) -> None:
        """Print the content with customized color.
        Args:
            content (`str`):
                The content to be printed.
            color (`Literal["red", "blue", "green"]`):
                The color of the printed content.
        """
        # TODO: This is only a temporary solution for customized print.
        #  The printed content won't be recorded in logging files, and
        #  it will be replaced by a better solution soon.
        if self.verbose:
            if color == "red":
                print("\033[31m" + content + "\033[0m")
            elif color == "green":
                print("\033[32m" + content + "\033[0m")
            elif color == "blue":
                print("\033[34m" + content + "\033[0m")
            else:
                print(content)