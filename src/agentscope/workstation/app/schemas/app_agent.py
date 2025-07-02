# -*- coding: utf-8 -*-
"""agent related schemas"""
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
    """File search"""

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
    """Prologue"""

    prologue_text: str = ""
    suggested_questions: List[str] = []


class Memory(BaseModel):
    """Memory"""

    dialog_round: int = 3


class Tool(BaseModel):
    """Tool"""

    id: str


class McpServer(BaseModel):
    """MCP server"""

    id: str


class AgentParameters(Parameters):
    """Agent parameters"""

    repetition_penalty: Union[float, None] = None
    tool_params: Optional[dict] = None
    tool_tokens: Optional[dict] = None


class AgentConfig(BaseModel):
    """Agent config"""

    model_provider: str = "tongyi"
    model: str = "qwen-plus"
    instructions: str = (
        "# 知识库 \nPlease remember the following materials, "
        "as they may be helpful in answering "
        "questions.\n${documents}"
    )
    parameters: AgentParameters = AgentParameters()
    file_search: FileSearch = FileSearch()
    memory: Memory = Memory()
    tools: List[Tool] = []
    mcp_servers: List[McpServer] = []
    agent_components: List[str] = []
    workflow_components: List[str] = []
    prologue: Prologue = Prologue()


class AgentRequest(BaseModel):
    """Agent request"""

    app_id: str
    stream: bool = True
    messages: List[PromptMessage]
    conversation_id: Optional[str] = None
    prompt_variables: Optional[dict] = None
    extra_params: Optional[dict] = None
    is_draft: bool = False


class AgentError(BaseModel):
    """Agent Error"""

    code: str
    message: str


class AgentResponse(BaseModel):
    """Agent response"""

    request_id: str
    conversation_id: str
    model: str
    message: Union[AssistantPromptMessage, Dict[str, Any]]
    status: Optional[Literal["in_progress", "completed", "failed"]] = None
    usage: Optional[CompletionUsage] = None
    error: Optional[AgentError] = None


class RequestContext(BaseModel):
    """Request context"""

    request_id: str
    account_id: str
    user_name: str
    workspace_id: str
    account_type: str
    caller_ip: str
    start_time: int
