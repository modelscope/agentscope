# -*- coding: utf-8 -*-
"""An agent that are provided with a set of tools to use. """

from typing import List, Literal, Tuple

import json

from agentscope.message import Msg
from agentscope.models import ModelResponse
from agentscope.prompt import PromptEngine
from agentscope.prompt import PromptType
from agentscope.agents import AgentBase
from agentscope.service import ServiceResponse
from agentscope.service import ServiceExecStatus

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

RESPONSE_HINT_PROMPT = """
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


def parse_func(response: ModelResponse) -> ModelResponse:
    """Parse the response from the model into a dictionary with `function`,
    `thought`, and `speak` fields."""
    json_response = json.loads(response.text)

    # Check keys
    if "function" not in json_response:
        json_response["function"] = []
    if "thought" not in json_response:
        json_response["thought"] = ""
    if "speak" not in json_response:
        raise RuntimeError("The response should contain a 'speak' field.")
    return ModelResponse(raw=json_response)


def fault_handler(response: ModelResponse) -> ModelResponse:
    """Handle the response from model when parse function fails for more
    than `max_tries` times."""
    return ModelResponse(
        raw={
            "thought": "",
            "speak": response.text,
            "function": [],
        },
    )


class ToolAgent(AgentBase):
    """An agent that are provided with a set of tools to use."""

    def __init__(
        self,
        name: str,
        model_config_name: str,
        tools: List[Tuple],
        sys_prompt: str = DEFAULT_SYS_PROMPT,
        use_memory: bool = True,
        verbose: bool = True,
    ) -> None:
        """Initialize a tool agent with pre-processed tool functions.

        Args:
            name (`str`):
                The name of the agent.
            model_config_name (`str`):
                The name of the model configuration.
            tools (`List[Tuple]`):
                The pre-processed tool functions and their descriptions in
                JSON schema format, e.g.
                `[(bing_search, {"function": "bing_search", ...}), ...]`
            sys_prompt (`str`, defaults to `DEFAULT_SYS_PROMPT`):
                The system prompt for the tool agent.
            use_memory (`bool`, defaults to `True`):
                Whether to use memory for the agent.
            verbose (`bool`, defaults to `False`):
                Whether to print the agent's thought and function execution
                results.

        Note:
            The tool functions in the `tools` argument should be available to
            the agent directly. That is, the arguments that requires developers
            input should already be processed, e.g. api key, username,
            password, etc. AgentScope provides `ServiceFactory` to help
            developers handle these arguments.
        """
        super().__init__(
            name,
            sys_prompt,
            model_config_name=model_config_name,
            use_memory=use_memory,
        )

        self.engine = PromptEngine(self.model, prompt_type=PromptType.LIST)

        # Record the function name mapping
        self.tools_prompt, self.func_name_mapping = self.prepare_funcs_prompt(
            tools,
        )

        self.verbose = verbose

        self.sys_prompt = sys_prompt.format_map(
            {
                "function_prompt": self.tools_prompt,
            },
        )

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

    def execute_func(self, func_call: dict) -> ServiceResponse:
        """Execute the tool function and return the result.

        Args:
            func_call (`dict`):
                The function call dictionary with keys 'name' and 'arguments'.

        Returns:
            `ServiceResponse`: The execution results.
        """
        # Extract the function name and arguments
        func_name = func_call["name"]
        func_args = func_call["arguments"]

        # Execute the function
        self._customize_print(
            " EXECUTE FUNCTION ".center(80, "#"),
        )
        self._customize_print(f"FUNCTION NAME: {func_name}")
        self._customize_print(
            f"FUNCTION ARGS: "
            f"\n{json.dumps(func_args, indent=4, ensure_ascii=False)}",
        )

        try:
            res_func = self.func_name_mapping[func_name](**func_args)
        except Exception as e:
            res_func = ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=str(e),
            )

        status = (
            "SUCCESS"
            if res_func.status == ServiceExecStatus.SUCCESS
            else "FAILED",
        )

        self._customize_print(
            content=(
                f"EXECUTE RESULT: \n\tSTATUS: {status}\n"
                f"\tCONTENT: {res_func.content}"
            ),
            color="blue",
        )
        self._customize_print("END EXECUTION".center(80, "#"))

        # return the result of the function
        return res_func

    def reply(self, x: dict = None) -> dict:
        """Reply to the user based on the input."""
        if self.memory:
            self.memory.add(x)

        prompt = self.engine.join(
            Msg("system", self.sys_prompt, role="system"),
            self.memory and self.memory.get_memory(),
            Msg("system", RESPONSE_HINT_PROMPT, role="system"),
        )

        response = self.model(
            prompt,
            parse_func=parse_func,
            fault_handler=fault_handler,
        )

        # parse function call
        res = response.raw
        self._customize_print(" RAW RESPONSE FROM MODEL ".center(80, "#"))
        self._customize_print(json.dumps(res, indent=4))
        msg = Msg(self.name, res["speak"])

        # print and feed into memory
        self.speak(msg)
        if self.memory:
            self.memory.add(msg)

        if len(res["function"]) == 0:
            return msg
        else:
            # Execute the function
            execute_results = []
            for i, func in enumerate(res["function"]):
                func_res = self.execute_func(func)
                execute_results.append(
                    {
                        "index": i + 1,
                        "function_name": func["name"],
                        "status": "SUCCESS"
                        if func_res.status == ServiceExecStatus.SUCCESS
                        else "FAILED",
                        "result": func_res.content,
                    },
                )

            # Format execution results into prompt
            execute_results_prompt = "\n".join(
                [FUNCTION_RESULT_TITLE_PROMPT]
                + [
                    FUNCTION_RESULT_PROMPT.format_map(res)
                    for res in execute_results
                ],
            )

            # Record execution results into memory as a message from the system
            msg = Msg(
                name="system",
                role="system",
                content=execute_results_prompt,
            )
            if self.memory:
                self.memory.add(msg)

            # Note: the failed execution results won't be handled now.

            # Generate response based on the execution results and conversation
            prompt = self.engine.join(
                self.memory and self.memory.get_memory(),
                Msg(
                    name="system",
                    content=(
                        "Now, generate a response based on execution "
                        "results and conversation"
                    ),
                    role="system",
                ),
            )

            response = self.model(prompt)

            msg = Msg(self.name, response.text)

            self.speak(msg)
            if self.memory:
                self.memory.add(msg)

            return msg
