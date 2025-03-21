# -*- coding: utf-8 -*-
"""The ReAct Agent V2, which use the tools API of the LLM service providers
rather than assembling the prompt manually."""
from typing import Union, Optional

from ._agent import AgentBase
from ..manager import ModelManager
from ..message import Msg, ToolUseBlock, TextBlock, ContentBlock
from ..service import ServiceToolkit, ServiceResponse, ServiceExecStatus


class ReActAgentV2(AgentBase):
    """The ReAct Agent V2, which use the tools API of the LLM service providers
    rather than assembling the prompt manually.

    The currently supported LLM providers include:
    - Anthropic
    - DashScope
    - OpenAI
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
        """Initial the ReAct agent with the given name, model config name and
        tools.

        Args:
            name (`str`):
                The name of the agent.
            model_config_name (`str`):
                The name of the model config, which is used to load model from
                configuration.
            service_toolkit (`ServiceToolkit`):
                The service toolkit object that contains the tool functions.
            sys_prompt (`str`):
                The system prompt of the agent.
            max_iters (`int`, defaults to `10`):
                The maximum number of iterations of the reasoning-acting loops.
            verbose (`bool`, defaults to `True`):
                Whether to print the detailed information during reasoning and
                acting steps. If `False`, only the content in speak field will
                be print out.
        """
        super().__init__(name=name)

        self.sys_prompt: str = sys_prompt.format(name=self.name)

        self.model = ModelManager.get_instance().get_model_by_config_name(
            model_config_name,
        )

        self.service_toolkit = service_toolkit
        self.service_toolkit.add(self.generate_response)

        # Obtain the JSON schemas of the tool functions
        # Also, you can parse it in the _reasoning method for dynamic tool
        # calls
        self.tools = self.model.format_tools_json_schemas(
            self.service_toolkit.json_schemas,
        )

        self.verbose = verbose
        self.max_iters = max_iters

    def reply(self, x: Optional[Union[Msg, list[Msg]]] = None) -> Msg:
        """The reply method of the agent."""
        self.memory.add(x)

        for _ in range(self.max_iters):
            # Reasoning to generate tool calls
            tool_calls = self._reasoning()

            if tool_calls is None:
                continue

            # Acting based on the tool calls
            msg_response = self._acting(tool_calls)
            if msg_response:
                return msg_response

        # Generate a response when exceeding the maximum iterations
        return self._summarizing()

    def _reasoning(self) -> Union[list[ToolUseBlock], None]:
        """The reasoning process of the agent.

        Returns:
            `Union[ToolUseBlock, None]`:
                Return `None` if no tool is used, otherwise return the tool use
                block.
        """
        prompt = self.model.format(
            Msg(
                "system",
                self.sys_prompt,
                role="system",
            ),
            self.memory.get_memory(),
        )

        raw_response = self.model(prompt, tools=self.tools)
        if self.verbose:
            self.speak(
                raw_response.stream or raw_response.text,
                tool_calls=raw_response.tool_calls,
            )

        # Prepare the content for the msg
        content: list[ContentBlock] = []
        if raw_response.text:
            content.append(TextBlock(type="text", text=raw_response.text))
        if raw_response.tool_calls:
            content.extend(raw_response.tool_calls)
        self.memory.add(
            Msg(
                self.name,
                content,
                role="assistant",
            ),
        )

        return raw_response.tool_calls

    def _acting(self, tool_calls: list[ToolUseBlock]) -> Union[None, Msg]:
        """The acting process of the agent, which takes a tool use block as
        input, execute the function and return a message if the
        `generate_response`
        function is called.

        Args:
            tool_calls (`ToolUseBlock`):
                The tool use block to be executed.

        Returns:
            `Union[None, Msg]`:
                Return `None` if the function is not `generate_response`,
                otherwise return a message to the user.
        """
        msg_response: Union[None, Msg] = None
        for tool_call in tool_calls:
            msg_execution = self.service_toolkit.parse_and_call_func(
                tool_call,
                tools_api_mode=True,
            )
            if self.verbose:
                self.speak(msg_execution)
            self.memory.add(msg_execution)

            if tool_call["name"] == "generate_response":
                msg_response = Msg(
                    self.name,
                    str(tool_call["input"]["response"]),
                    "assistant",
                    echo=True,
                )

        return msg_response

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
    def generate_response(
        response: str,  # pylint: disable=unused-argument
    ) -> ServiceResponse:
        """Generate a response. You must call this function to interact with
        others (e.g., users).

        Args:
            response (`str`):
                The response to the user.
        """

        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Success",
        )
