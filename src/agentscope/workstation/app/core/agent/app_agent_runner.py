# -*- coding: utf-8 -*-
import json
import uuid
from typing import AsyncGenerator, Any, List, Dict, Optional, Tuple

from openai.types.chat import ChatCompletionChunk
from pydantic import BaseModel
from sqlmodel import Session

from app.core.agent.app_agent import AppAgent
from app.core.config import settings
from app.models.provider import ProviderBase
from app.schemas.app import App
from app.schemas.app_agent import (
    AgentConfig,
    AgentRequest,
    AgentResponse,
    AgentError,
)
from app.services.app_service import AppService
from app.services.mcp_service import MCPService
from app.services.provider_service import ProviderService
from app.services.retrieval_service import RetrievalService
from app.utils.crypto import decrypt_with_rsa
from agentdev.components.redis_memory import (
    RedisMemory,
    MemoryInput,
    MemoryOutput,
)
from agentdev.base.memory import MemoryOperation
from agentdev.schemas.message_schemas import (
    PromptMessage,
    PromptMessageFunction,
    PromptMessageTool,
    PromptMessageRole,
    AssistantPromptMessage,
    ToolCall,
    ToolCallFunction,
)
from agentdev.utils.message_util import merge_incremental_chunk

from loguru import logger


class AppAgentRunner:
    def __init__(
        self,
        name: str,
        app_id: str,
        session: Session,
        account_id: str,
        workspace_id: str = settings.WORKSPACE_ID,
        model_config_name: str = None,
    ):
        self.account_id = account_id
        self.app_service = AppService(session)
        self.provider_service = ProviderService(session)
        app_info: App = self.app_service.get_app(
            app_id=app_id,
            workspace_id=workspace_id,
        )
        if not app_info:
            raise ValueError(f"App with id {app_id} not found")
        app_config = (
            app_info.config.model_dump()
            if isinstance(app_info.config, BaseModel)
            else app_info.config
        )

        self.config = AgentConfig(**app_config)
        provider_info: ProviderBase = self.provider_service.get_provider(
            provider=self.config.model_provider,
            workspace_id=workspace_id,
        )
        if not provider_info.credential:
            raise ValueError(
                f"Provider with id {self.config.model_provider} not found",
            )
        model_credential = json.loads(provider_info.credential)
        self.api_key = decrypt_with_rsa(model_credential["api_key"])
        self.memory_service = RedisMemory(
            host=settings.REDIS_SERVER,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB_MEMORY,
            user=settings.REDIS_USER,
            password=settings.REDIS_PASSWORD,
        )
        self.app_agent = AppAgent(
            name,
            self.config,
            model_config_name,
            base_url=model_credential["endpoint"],
            api_key=self.api_key,
        )
        self.mcp_service = MCPService(session=session, account_id=account_id)
        self.retrieval_service = RetrievalService(session=session)

    @staticmethod
    def update_rag_result(
        instructions: str,
        messages: List[PromptMessage],
        rag_result: List[Dict],
    ) -> List[PromptMessage]:
        system_prompt = ""
        for knowledge in rag_result:
            system_prompt += knowledge.text + "\n"

        if "${documents}" in instructions:
            system_prompt = instructions.replace(
                "${documents}",
                system_prompt,
            )
        else:
            system_prompt = instructions + "\n\n" + system_prompt
        if messages[0].role == PromptMessageRole.SYSTEM.value:
            messages[0].content = system_prompt + messages[0].content
        else:
            messages.insert(
                0,
                PromptMessage(
                    role=PromptMessageRole.SYSTEM.value,
                    content=system_prompt,
                ),
            )
        return messages

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    async def use_memory(
        self,
        messages: List[PromptMessage],
        conversation_id: Optional[str],
        dialog_round: int,
    ) -> Tuple[bool, List[PromptMessage]]:
        """
        when messages has assistant role, it means it contain history info
        , and thus no need to use memory
        """
        if conversation_id is None:
            return False, messages
        should_use_memory = True
        for message in messages:
            if message.role == PromptMessageRole.ASSISTANT.value:
                should_use_memory = False

        if not should_use_memory:
            return should_use_memory, messages
        get_memory_input = MemoryInput(
            operation_type=MemoryOperation.GET,
            run_id=conversation_id,
            filters={"dialogue_round": dialog_round},
        )
        memory_result: MemoryOutput = await self.memory_service.get(
            get_memory_input,
        )

        if len(memory_result.messages) > 0:
            # system message
            messages = []
            if (
                len(messages) > 0
                and messages[0].role == PromptMessageRole.SYSTEM.value
            ):
                messages = [messages.pop(0)]
            # history message
            messages.extend(memory_result.messages)
            # user current round message
            messages.extend(messages)
        return should_use_memory, messages

    @staticmethod
    def convert_completion_to_response(
        request_id: str,
        conversion_id: str,
        model: str,
        chunk: ChatCompletionChunk,
        mcp_name_set: Optional[set] = None,
        include_usage: bool = True,
    ) -> AgentResponse:
        if include_usage and len(chunk.choices) == 0:
            return AgentResponse(
                message=AssistantPromptMessage(content=""),
                conversation_id=conversion_id,
                status="completed",
                usage=chunk.usage,
                request_id=request_id,
                model=model,
            ).model_dump(
                exclude={
                    "messages": {
                        "__all__": {"name", "function_call", "plugin_call"},
                    },
                    "error": True,
                },
                exclude_none=True,
            )

        message = AssistantPromptMessage(
            **chunk.choices[0].delta.model_dump(
                exclude_none=True,
                exclude_defaults=True,
                exclude_unset=True,
            ),
        )
        if message.tool_calls and len(message.tool_calls) > 0:
            for tool_call in message.tool_calls:
                if mcp_name_set and tool_call.function.name in mcp_name_set:
                    tool_call.type = "mcp_tool_call"

        # convert role tool to role assistant, and only support one tool
        if message.role == PromptMessageRole.TOOL.value:
            if mcp_name_set and message.name in mcp_name_set:
                tool_call_type = "mcp_tool_result"
            else:
                tool_call_type = "function"
            tool_calls = ToolCall(
                function=ToolCallFunction(
                    name=message.name,
                    arguments="",
                    output=message.content,
                ),
                id="",
                type=tool_call_type,
            )
            message = AssistantPromptMessage(
                content="",
                tool_calls=[tool_calls],
            )
        message = message.model_dump()

        # support content type
        message["content_type"] = "text"

        finish_reason = chunk.choices[0].finish_reason
        if include_usage:
            status = "in_progress"
        else:
            status = "in_progress" if finish_reason != "stop" else "completed"

        return AgentResponse(
            message=message,
            conversation_id=conversion_id,
            status=status,
            usage=None,
            request_id=request_id,
            model=model,
        ).model_dump(
            exclude={
                "messages": {
                    "__all__": {"name", "function_call", "plugin_call"},
                },
                "error": True,
            },
        )

    @staticmethod
    def convert_mcp_tool_to_tool_function(
        server_code: str,
        mcp_tools: List[Dict[str, Any]],
    ) -> List[Dict]:
        mcp_functions = []
        # convert mcp function to PromptMessageFunction
        for tool in mcp_tools:
            if isinstance(tool, BaseModel):
                tool = tool.model_dump()
            tool["parameters"] = tool["input_schema"]
            function_tool = PromptMessageTool(**tool)
            function_type = "mcp_tool_call"
            mcp_functions.append(
                {
                    "server_code": server_code,
                    "function": PromptMessageFunction(
                        function=function_tool,
                        type=function_type,
                    ),
                    "name": tool["name"],
                },
            )
        return mcp_functions

    async def arun(
        self,
        request: AgentRequest,
        request_id: str = str(uuid.uuid4()),
        **kwargs: Any,
    ) -> AsyncGenerator[AgentResponse, Any]:
        try:
            tool_functions = []
            mcp_tool_functions = []
            mcp_name_set = set()
            user_message = request.messages[-1]

            parameters = self.config.parameters
            parameters.stream = request.stream
            parameters.tool_params = request.extra_params

            if not request.conversation_id:
                request.conversation_id = AppAgentRunner.generate_id()

            # retrieval tool function from mcp
            kwargs["mcp_method"] = self.mcp_service.debug_tools
            for item in self.config.mcp_servers:
                mcp_response = await self.mcp_service.get_mcp_server_code(
                    server_code=item.id,
                    need_tools=True,
                )
                mcp_tools_in_cur_server = (
                    self.convert_mcp_tool_to_tool_function(
                        item.id,
                        mcp_response["tools"],
                    )
                )
                mcp_tool_functions.extend(mcp_tools_in_cur_server)
                for server in mcp_tools_in_cur_server:
                    mcp_name_set.add(server["name"])

            # # retrieval rag result
            # # TODO need to make sure the inputs
            rag_kwargs = self.config.file_search.model_dump(exclude_none=True)
            rag_kwargs["knowledge_base_ids"] = rag_kwargs["kb_ids"]
            rag_result = self.retrieval_service.retrieve(
                account_id=self.account_id,
                query=user_message.content,
                api_key=self.api_key,
                **rag_kwargs,
            )

            # update messages  with rag result
            request.messages = self.update_rag_result(
                instructions=self.config.instructions,
                messages=request.messages,
                rag_result=rag_result,
            )

            # update messages with history
            should_use_memory, messages = await self.use_memory(
                request.messages,
                request.conversation_id,
                self.config.memory.dialog_round,
            )
            request.messages = messages

            cumulated_assistant = []

            async for chunk in self.app_agent.astream(
                request=request,
                parameters=parameters,
                tool_functions=tool_functions,
                mcp_tool_functions=mcp_tool_functions,
                **kwargs,
            ):
                logger.info(chunk)

                cumulated_assistant.append(chunk.model_copy(deep=True))
                yield self.convert_completion_to_response(
                    chunk=chunk,
                    request_id=request_id,
                    conversion_id=request.conversation_id,
                    mcp_name_set=mcp_name_set,
                    include_usage=True,
                    model=self.config.model,
                )
            cumulated_resp = merge_incremental_chunk(cumulated_assistant)

            # add memory
            assistant_replay = AssistantPromptMessage(
                **cumulated_resp.choices[0].delta.model_dump(
                    exclude_none=True,
                ),
            )

            # only store the valid result
            if should_use_memory and assistant_replay.content:
                add_memory_input = MemoryInput(
                    operation_type=MemoryOperation.ADD,
                    run_id=request.conversation_id,
                    messages=[
                        user_message,
                        assistant_replay,
                    ],
                )
                await self.memory_service.add(add_memory_input)

        except Exception as e:
            import traceback

            logger.error(f"error is {e} with detail {traceback.format_exc()}")
            # TODO: standardize error
            yield AgentResponse(
                message={},
                conversation_id=request.conversation_id,
                status="failed",
                request_id=request_id,
                error=AgentError(code="500", message="Internal server error!"),
                model=self.config.model,
            )


if __name__ == "__main__":
    import asyncio
    from app.db.init_db import get_session

    async def run_agent() -> Any:
        (session,) = get_session()
        app_agent_runner = AppAgentRunner(
            name="test",
            app_id="test",
            session=session,
            account_id="10001",
            model_config_name="qwen-plus",
        )  # Iterate through the asynchronous generator and process each chunk
        async for chunk in app_agent_runner.arun(
            request=AgentRequest(
                app_id="test",
                conversation_id="test",
                messages=[
                    PromptMessage(
                        role=PromptMessageRole.USER.value,
                        content="hello",
                    ),
                ],
            ),
        ):
            print(chunk)  # Print or process each generated block

    asyncio.run(run_agent())
