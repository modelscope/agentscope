# -*- coding: utf-8 -*-
"""An agent class that partially implements the SWE-agent.
SWE-agent is an agent designed for solving github issues.
More details can be found in https://swe-agent.com/.

Here we partially implement and modified the SWE-agent,
try to make it work with wider range of tasks then just fixing github issues.
"""

from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.exception import ResponseParsingError
from agentscope.parsers import MarkdownJsonDictParser
from typing import List, Callable, Optional, Union, Sequence
import json
from agentscope.service import (
    ServiceFactory,
    execute_shell_command,
)

from swe_agent_service_func import (
    exec_py_linting,
    write_file,
    read_file,
)

from swe_agent_prompts import (
    get_system_prompt,
    get_context_prompt,
    get_step_prompt,
)


def prepare_func_prompt(function: Callable) -> str:
    func, desc = ServiceFactory.get(function)
    func_name = desc["function"]["name"]
    func_desc = desc["function"]["description"]
    args_desc = desc["function"]["parameters"]["properties"]

    args_list = [f"{func_name}: {func_desc}"]
    for args_name, args_info in args_desc.items():
        if "type" in args_info:
            args_line = (
                f'\t{args_name} ({args_info["type"]}): '
                f'{args_info.get("description", "")}'
            )
        else:
            args_line = f'\t{args_name}: {args_info.get("description", "")}'
        args_list.append(args_line)

    func_prompt = "\n".join(args_list)
    return func_prompt


COMMANDS_DISCRIPTION_DICT = {
    "exit": "exit: Executed when the current task is complete, takes no arguments",  # noqa
    "scroll_up": "scroll_up: Scrolls up the current open file, will scroll up and show you the 100 lines above your current lines, takes no arguments",  # noqa
    "scroll_down": "scroll_down: Scrolls down the current open file, will scroll down and show you the 100 lines below your current lines'takes no arguments",  # noqa
    "goto": "goto: This will take you directly to the line <line_num> and show you the 100 lines below it. \n       line_num (int): The line number to go to.",  # noqa
}

COMMANDS_DISCRIPTION_DICT["write_file"] = prepare_func_prompt(write_file)
COMMANDS_DISCRIPTION_DICT["read_file"] = prepare_func_prompt(read_file)
COMMANDS_DISCRIPTION_DICT["execute_shell_command"] = prepare_func_prompt(
    execute_shell_command,
)
COMMANDS_DISCRIPTION_DICT["exec_py_linting"] = prepare_func_prompt(
    exec_py_linting,
)


ERROR_INFO_PROMPT = """Your response is not a JSON object, and cannot be parsed by `json.loads` in parse function:
## Your Response:
[YOUR RESPONSE BEGIN]
{response}
[YOUR RESPONSE END]

## Error Information:
{error_info}

Analyze the reason, and re-correct your response in the correct format."""  # pylint: disable=all  # noqa


def count_file_lines(file_path: str) -> int:
    with open(file_path, "r") as file:
        lines = file.readlines()
    return len(lines)


class SWEAgent(AgentBase):
    """
    The SWE-agent
    """

    def __init__(
        self,
        name: str,
        model_config_name: str,
    ) -> None:
        """ """
        super().__init__(
            name=name,
            model_config_name=model_config_name,
        )

        self.memory_window = 6
        self.max_retries = 2
        self.running_memory: List[str] = []
        self.cur_file: str = ""
        self.cur_line: int = 0
        self.cur_file_content: str = ""

        self.main_goal = ""
        self.commands_prompt = ""
        self.parser = MarkdownJsonDictParser()
        self.get_commands_prompt()

    def get_current_file_content(self) -> None:
        """
        Get the current file content.
        """
        if self.cur_file == "":
            return
        start_line = self.cur_line - 50
        if start_line < 0:
            start_line = 0
        end_line = self.cur_line + 50
        if end_line > count_file_lines(self.cur_file):
            end_line = -1
        read_res = read_file(self.cur_file, start_line, end_line)
        self.cur_file_content = read_res.content

    def step(self) -> Msg:
        """
        Step the SWE-agent.
        """
        message_list = []

        # construct system prompt
        system_prompt = get_system_prompt(self.commands_prompt)
        message_list.append(Msg("user", system_prompt, role="system"))

        # construct context prompt, i.e. previous actions
        context_prompt = get_context_prompt(
            self.running_memory,
            self.memory_window,
        )
        message_list.append(Msg("user", context_prompt, role="user"))

        # construct step prompt for this instance
        self.get_current_file_content()
        step_prompt = get_step_prompt(
            self.main_goal,
            self.cur_file,
            self.cur_line,
            self.cur_file_content,
        )
        message_list.append(Msg("user", step_prompt, role="user"))

        # get response from agent
        try:
            in_prompt = self.model.format(message_list)
            res = self.model(
                in_prompt,
                parse_func=self.parser.parse,
                max_retries=1,
            )

        except ResponseParsingError as e:
            response_msg = Msg(self.name, e.raw_response, "assistant")
            self.speak(response_msg)

            # Re-correct by model itself
            error_msg = Msg(
                name="system",
                content={
                    "action": {"name": "error"},
                    "error_msg": ERROR_INFO_PROMPT.format(
                        parse_func=self.parser.parse,
                        error_info=e.message,
                        response=e.raw_response,
                    ),
                },
                role="system",
            )
            self.speak(error_msg)
            # continue
            self.running_memory.append(error_msg)
            return error_msg

        msg_res = Msg(self.name, res.parsed, role="assistant")

        self.speak(
            Msg(self.name, json.dumps(res.parsed, indent=4), role="assistant"),
        )

        # parse and execute action
        action = res.parsed.get("action")

        obs = self.parse_command(res.parsed["action"])
        self.speak(
            Msg(self.name, "\n====Observation====\n" + obs, role="assistant"),
        )

        # add msg to context windows
        self.running_memory.append(str(action) + str(obs))
        return msg_res

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        action_name = None
        self.main_goal = x.content
        while not action_name == "exit":
            msg = self.step()
            action_name = msg.content["action"]["name"]
        return msg

    def parse_command(self, command_call: dict) -> str:
        command_name = command_call["name"]
        command_args = command_call["arguments"]
        if command_name == "exit":
            return "Current task finished, exitting."
        if command_name in ["goto", "scroll_up", "scroll_down"]:
            if command_name == "goto":
                line = command_call["arguments"]["line_num"]
                command_str = f"Going to {self.cur_file} line \
                    {command_args['line_mum']}."
                command_failed_str = f"Failed to go to {self.cur_file} \
                    line {command_args['line_num']}"
            if command_name == "scroll_up":
                line = self.cur_line - 100
                if line < 0:
                    line = 0
                command_str = (
                    f"Scrolling up from file {self.cur_file} to line {line}."
                )
                command_failed_str = (
                    f"Failed to scroll up {self.cur_file} to line {line}"
                )
            if command_name == "scroll_down":
                line = self.cur_line + 100
                if line > count_file_lines(self.cur_file):
                    line = count_file_lines(self.cur_file)
                command_str = (
                    f"Scrolling down from file {self.cur_file} to line {line}."
                )
                command_failed_str = (
                    f"Failed to scrool down {self.cur_file} to line {line}"
                )
            read_status = read_file(self.cur_file, line, line + 100)
            if read_status.status == "success":
                self.cur_line = line
                obs = read_status.content
                return f"{command_str}. Observe file content: {obs}"
            else:
                return command_failed_str
        if command_name == "execute_shell_command":
            return execute_shell_command(**command_args).content
        if command_name == "write_file":
            self.cur_file = command_args["file_path"]
            self.cur_line = command_args.get("start_line", 0)
            write_status = write_file(**command_args)
            return write_status.content
        if command_name == "read_file":
            self.cur_file = command_args["file_path"]
            self.cur_line = command_args.get("start_line", 0)
            read_status = read_file(**command_args)
            return read_status.content
        if command_name == "exec_py_linting":
            return exec_py_linting(**command_args).content
        return "No such command"

    def get_commands_prompt(self) -> None:
        for name, desc in COMMANDS_DISCRIPTION_DICT.items():
            self.commands_prompt += f"{name}: {desc}\n"
