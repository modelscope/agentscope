# -*- coding: utf-8 -*-
import uuid
from typing import Union, Optional, List, Literal, Dict, Any

from pydantic import BaseModel
from agentdev.schemas.message_schemas import (
    PromptMessage,
    Parameters,
    AssistantPromptMessage,
)
from openai.types.completion_usage import CompletionUsage


class FileSearch(BaseModel):
    kb_ids: list[uuid.UUID] = []
    enable_search: bool = False
    enable_citation: bool = False
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None
    hybrid_weight: float = 0.7
    search_type: str = "hybrid"
    enable_rerank: bool = False
    rerank_provider: Optional[str] = None
    rerank_model: Optional[str] = None


class Prologue(BaseModel):
    prologue_text: str = ""
    suggested_questions: List[str] = []


class Memory(BaseModel):
    dialog_round: int = 3


class Tool(BaseModel):
    id: str


class McpServer(BaseModel):
    id: str


class AgentParameters(Parameters):
    repetition_penalty: Union[float, None] = None
    tool_params: Optional[dict] = None
    tool_tokens: Optional[dict] = None


class AgentConfig(BaseModel):
    model_provider: str = "tongyi"
    model: str = "qwen-plus"
    instructions: str = "# 知识库 \n请记住以下材料，他们可能对回答问题有帮助。\n${documents}"
    parameters: AgentParameters = AgentParameters()
    file_search: FileSearch = FileSearch()
    memory: Memory = Memory()
    tools: List[Tool] = []
    mcp_servers: List[McpServer] = []
    agent_components: List[str] = []
    workflow_components: List[str] = []
    prologue: Prologue = Prologue()


class AgentRequest(BaseModel):
    app_id: str
    stream: bool = True
    messages: List[PromptMessage]
    conversation_id: Optional[str] = None
    prompt_variables: Optional[dict] = None
    extra_params: Optional[dict] = None
    is_draft: bool = False


class AgentError(BaseModel):
    code: str
    message: str


class AgentResponse(BaseModel):
    request_id: str
    conversation_id: str
    model: str
    message: Union[AssistantPromptMessage, Dict[str, Any]]
    status: Optional[Literal["in_progress", "completed", "failed"]] = None
    usage: Optional[CompletionUsage] = None
    error: Optional[AgentError] = None


class RequestContext(BaseModel):
    request_id: str
    account_id: str
    user_name: str
    workspace_id: str
    account_type: str
    caller_ip: str
    start_time: int
