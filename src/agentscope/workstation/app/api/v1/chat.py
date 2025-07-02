# -*- coding: utf-8 -*-
"""Chat"""
import json
from typing import AsyncGenerator

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.api.deps import SessionDep, CurrentAccount
from app.core.agent.app_agent_runner import AppAgentRunner
from app.exceptions.base import IncorrectParameterException
from app.schemas.app_agent import AgentRequest

router = APIRouter(prefix="/apps", tags=["apps"])


@router.post("/chat/completions")
async def chat_completions(
    current_account: CurrentAccount,
    request: AgentRequest,
    session: SessionDep,
) -> StreamingResponse:
    """Chat with the app."""
    # validation the input
    if not request.app_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: app id",
        )
    account_id = current_account.account_id
    # call the main logic
    response_type = "sse"
    agent_runner = AppAgentRunner(
        name=request.app_id,
        app_id=request.app_id,
        session=session,
        account_id=account_id,
    )
    if not request.conversation_id:
        request.conversation_id = AppAgentRunner.generate_id()

    generator = agent_runner.arun(
        request=request,
        request_id=AppAgentRunner.generate_id(),
    )
    media_type = {
        "sse": "text/event-stream",
        "json": "application/x-ndjson",
        "text": "text/plain",
    }.get(response_type, "text/event-stream")
    return StreamingResponse(
        stream_generator(generator=generator, response_type=response_type),
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def stream_generator(
    generator: AsyncGenerator,
    response_type: str,
) -> AsyncGenerator:
    """generate stream response"""
    async for output in generator:
        if response_type == "sse":
            if isinstance(output, str):
                yield f"data: {output}\n\n"
            elif isinstance(output, dict):
                yield f"data: {json.dumps(output, ensure_ascii=False)}\n\n"
            elif isinstance(output, BaseModel):
                yield f"data: {output.model_dump_json()}\n\n"
        elif response_type == "json":
            yield json.dumps(output, ensure_ascii=False) + "\n"
        else:  # text
            yield str(output) + "\n"
