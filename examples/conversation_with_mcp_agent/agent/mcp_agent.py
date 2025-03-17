# -*- coding: utf-8 -*-
"""
Module for MCPAgent which is a dialog agent interacting with users and MCP
tools.
"""
import json
from typing import Optional, Union, Sequence

from loguru import logger
from agentscope.agents import DialogAgent
from agentscope.message import Msg
from agentscope.models import ModelResponse

from .server import Server
from .utils import run_sync

# System prompt is copied from official Example, see here for details:
# https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/refs
# /heads/main/examples/clients/simple-chatbot/mcp_simple_chatbot/main.py
SYS_PROMPT = (
    "You are a helpful assistant with access to these tools:\n\n"
    "{tools_description}\n"
    "Choose the appropriate tool based on the user's question. "
    "If no tool is needed, reply directly.\n\n"
    "IMPORTANT: When you need to use a tool, you must ONLY respond with "
    "the exact JSON object format below, nothing else:\n"
    "{{\n"
    '    "tool": "tool-name",\n'
    '    "arguments": {{\n'
    '        "argument-name": "value"\n'
    "    }}\n"
    "}}\n\n"
    "After receiving a tool's response:\n"
    "1. Transform the raw data into a natural, conversational response\n"
    "2. Keep responses concise but informative\n"
    "3. Focus on the most relevant information\n"
    "4. Use appropriate context from the user's question\n"
    "5. Avoid simply repeating the raw data\n\n"
    "Please use only the tools that are explicitly defined above."
)


class MCPAgent(DialogAgent):
    """A general dialog agent to interact with users and MCP tools."""

    def __init__(
        self,
        name: str,
        sys_prompt: str = "",
        model_config_name: str = None,
        use_memory: bool = True,
        server_configs: dict = None,
    ) -> None:
        """Initialize the agent with a name, system prompt, LLM,
        and servers.

        Args:
            name: The name of the agent.
            sys_prompt: The system prompt that sets the agent's role.
            llm_client: The LLM client to interact with the language model.
            servers: The list of servers providing tools.
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt or SYS_PROMPT,
            model_config_name=model_config_name,
            use_memory=use_memory,
        )
        self.servers = [
            Server(name, srv_config)
            for name, srv_config in server_configs["mcpServers"].items()
        ]

        # Initialize servers synchronously
        run_sync(self.initialize_servers)

    @property
    def sys_prompt(self) -> str:
        """Get the system prompt."""
        return run_sync(self.build_sys_prompt)

    @sys_prompt.setter
    def sys_prompt(self, value: str) -> None:
        """Set the system prompt."""
        self._sys_prompt = value

    async def build_sys_prompt(self) -> str:
        """
        Build and return the system prompt by incorporating the available
        tools' descriptions.

        Returns:
            str: The formatted system prompt for the agent.
        """
        tools_description = "\n".join(
            [
                tool.format_for_llm()
                for server in self.servers
                for tool in await server.list_tools()
            ],
        )

        try:
            system_message = self._sys_prompt.format(
                tools_description=tools_description or "None",
            )
        except Exception as e:
            system_message = (
                f"{self._sys_prompt}\n\n"
                f"You have access to these tools:\n\n{tools_description}"
            )
            print(e)

        return system_message

    async def initialize_servers(self) -> None:
        """Initialize all servers."""
        for server in self.servers:
            try:
                await server.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize server: {e}")
                await self.cleanup_servers()
                raise

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in self.servers:
            await server.cleanup()

    def cleanup_servers_sync(self) -> None:
        """Clean up all servers properly."""
        run_sync(self.cleanup_servers)

    async def process_model_response(
        self,
        model_response: ModelResponse,
    ) -> ModelResponse:
        """Process the LLM response and execute tools if needed.

        Args:
            model_response: The response from the LLM.

        Returns:
            The result of tool execution or the original response.
        """
        try:  # pylint: disable=R1702
            tool_call = json.loads(model_response.text)
            if "tool" in tool_call and "arguments" in tool_call:
                logger.info(f"Executing tool: {tool_call['tool']}")
                logger.info(f"With arguments: {tool_call['arguments']}")

                for server in self.servers:
                    tools = await server.list_tools()
                    if any(tool.name == tool_call["tool"] for tool in tools):
                        try:
                            result = await server.execute_tool(
                                tool_call["tool"],
                                tool_call["arguments"],
                            )

                            if (
                                isinstance(result, dict)
                                and "progress" in result
                            ):
                                progress = result["progress"]
                                total = result["total"]
                                percentage = (progress / total) * 100
                                logger.info(
                                    f"Progress: {progress}/{total} "
                                    f"({percentage:.1f}%)",
                                )

                            model_response.text = (
                                f"Tool execution result: {result}"
                            )

                            return model_response
                        except Exception as e:
                            error_msg = f"Error executing tool: {str(e)}"
                            logger.error(error_msg)

                            model_response.text = error_msg
                            return model_response
                model_response.text = (
                    f"No server found with tool: {tool_call['tool']}"
                )
                return model_response
            return model_response
        except json.JSONDecodeError:
            return model_response

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """Reply function"""
        if self.memory:
            self.memory.add(x)

        # prepare prompt
        prompt = self.model.format(
            Msg("system", self.sys_prompt, role="system"),
            self.memory
            and self.memory.get_memory()
            or x,  # type: ignore[arg-type]
        )

        # call llm and generate response
        response = self.model(prompt)
        response = run_sync(self.process_model_response, response)

        # Print/speak the message in this agent's voice
        # Support both streaming and non-streaming responses by "or"
        self.speak(response.text)

        msg = Msg(self.name, response.text, role="assistant")

        # Record the message in memory
        if self.memory:
            self.memory.add(msg)

        return msg
